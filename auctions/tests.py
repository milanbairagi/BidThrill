from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import AuctionList, Bid

User = get_user_model()


class BaseTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="password123")
        self.other_user = User.objects.create_user(username="otheruser", password="password123")
        self.item = AuctionList.objects.create(
            name="Test Item", price=100.0, owner=self.user
        )


class AuthTests(BaseTestCase):
    # E
    def test_login_success(self):
        response = self.client.post(reverse("login"), {"username": "testuser", "password": "password123"})
        self.assertRedirects(response, reverse("index"))

    def test_login_invalid_credentials(self):
        response = self.client.post(reverse("login"), {"username": "testuser", "password": "wrong"})
        self.assertContains(response, "Invalid username and/or password.")

    def test_register_creates_user(self):
        self.client.post(reverse("register"), {
            "username": "newuser", "email": "new@example.com",
            "password": "pass", "confirmation": "pass",
        })
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_register_password_mismatch(self):
        response = self.client.post(reverse("register"), {
            "username": "newuser", "email": "new@example.com",
            "password": "pass1", "confirmation": "pass2",
        })
        self.assertContains(response, "Passwords must match.")
    # E
    def test_logout(self):
        self.client.login(username="testuser", password="password123")
        self.client.get(reverse("logout"))
        response = self.client.get(reverse("index"))
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class IndexAndItemViewTests(BaseTestCase):

    def test_index_shows_only_active_items(self):
        self.item.is_available = False
        self.item.save()
        response = self.client.get(reverse("index"))
        self.assertNotIn(self.item, response.context["items"])

    def test_item_view_loads(self):
        response = self.client.get(reverse("item_view", args=[self.item.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["item"], self.item)


class CreateListingTests(BaseTestCase):

    def test_requires_login(self):
        response = self.client.get(reverse("create_listing"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('create_listing')}")

    def test_creates_item_with_correct_owner(self):
        self.client.login(username="testuser", password="password123")
        self.client.post(reverse("create_listing"), {"name": "New Item", "price": 50.0})
        item = AuctionList.objects.get(name="New Item")
        self.assertEqual(item.owner, self.user)


class BiddingTests(BaseTestCase):

    def test_requires_login(self):
        response = self.client.post(reverse("item_bid", args=[self.item.id]), {"bid": 200.0})
        self.assertEqual(response.status_code, 302)

    def test_valid_bid_updates_leading_bid_and_count(self):
        self.client.login(username="otheruser", password="password123")
        self.client.post(reverse("item_bid", args=[self.item.id]), {"bid": 200.0})
        self.item.refresh_from_db()
        self.assertEqual(self.item.leading_bid, 200.0)
        self.assertEqual(self.item.bid_count, 1)

    def test_low_bid_rejected(self):
        self.client.login(username="otheruser", password="password123")
        response = self.client.post(reverse("item_bid", args=[self.item.id]), {"bid": 50.0})
        self.assertContains(response, "Enter bid larger than leading price")

    def test_rebid_updates_existing_bid_without_duplicate(self):
        self.client.login(username="otheruser", password="password123")
        self.client.post(reverse("item_bid", args=[self.item.id]), {"bid": 150.0})
        self.client.post(reverse("item_bid", args=[self.item.id]), {"bid": 250.0})
        self.assertEqual(Bid.objects.filter(item=self.item, user=self.other_user).count(), 1)
        self.item.refresh_from_db()
        self.assertEqual(self.item.leading_bid, 250.0)


class ClosedListingTests(BaseTestCase):

    def setUp(self):
        super().setUp()
        Bid.objects.create(user=self.other_user, item=self.item, price=200.0)
        self.item.leading_bid = 200.0
        self.item.save()

    def test_close_item_assigns_winner_and_closes(self):
        self.client.login(username="testuser", password="password123")
        self.client.post(reverse("closed_listing"), {"id": self.item.id})
        self.item.refresh_from_db()
        self.assertFalse(self.item.is_available)
        self.assertEqual(self.item.winner, self.other_user)

    # E
    def test_get_shows_only_current_users_wins(self):
        self.item.is_available = False
        self.item.winner = self.other_user
        self.item.save()
        self.client.login(username="otheruser", password="password123")
        response = self.client.get(reverse("closed_listing"))
        self.assertIn(self.item, response.context["closed_item"])