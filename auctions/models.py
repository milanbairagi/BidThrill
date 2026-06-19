from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class Category(models.Model):
    name = models.CharField(max_length=64)

    class Meta:
        ordering = ("name",)
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class AuctionList(models.Model):
    name = models.CharField(max_length=64)
    description = models.TextField(blank=True, null=True)
    price = models.FloatField(default=0.0)
    image = models.ImageField(upload_to="auction_img", blank=True, null=True)
    is_available = models.BooleanField(default=True, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, blank=True, null=True, related_name="category", default=1)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="auctions")
    
    leading_bid = models.FloatField(blank=True, null=True)
    bid_count = models.IntegerField(default=0)
    winner = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Set leading_bid to price when creating a new instance (if not already set)
        if self.pk is None and self.leading_bid is None:
            self.leading_bid = self.price
        super(AuctionList, self).save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class Bid(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name="bid")
    item = models.ForeignKey(AuctionList, on_delete=models.CASCADE, null=True, related_name="bid")
    price = models.FloatField()

    def __str__(self):
        return f"Bid {self.price} at {self.item.name} by {self.user.username}"


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name="comments")
    item = models.ForeignKey(AuctionList, on_delete=models.CASCADE, null=True, related_name="comments")
    comment = models.TextField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.comment[:20]

    class Meta:
        ordering = ['-created_at']


class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='watchlist_items')
    item = models.ForeignKey(AuctionList, on_delete=models.CASCADE, null=True, related_name="watchlist_items")

    def __str__(self):
        return f"{self.user} Watchlist {self.item.name}"
