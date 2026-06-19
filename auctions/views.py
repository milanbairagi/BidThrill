from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from .models import User, AuctionList, Bid
from .forms import CreateListingForm


ITEM_VIEW_URL = "auctions/item.html"


def render_item_view(request, user, item, message="", input_warning=""):
    """function to be used by other views to render item view"""
    user_bid = None
    if user.is_authenticated:
        user_bid = Bid.objects.filter(user=user, item=item).first()

    return render(request, ITEM_VIEW_URL, {
        "item": item,
        "message": message,
        "input_warning": input_warning,
        "user_bid": user_bid,
    })
    


def index(request):
    active_items = AuctionList.objects.filter(is_available=True)
    return render(request, "auctions/index.html", {
        "items": active_items
    })


def login_view(request):
    if request.method == "POST":
        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


@login_required
def create_listing(request):
    if request.method == 'POST':
        form = CreateListingForm(request.POST, request.FILES)
        if form.is_valid():
            new_item = form.save(commit=False)     
            new_item.owner = request.user
            new_item.save()

        return HttpResponseRedirect(reverse("index"))

    form = CreateListingForm()
    return render(request, "auctions/create_listing.html", {
        "form": form,
    })


def item_view(request, id):
    current_item = AuctionList.objects.get(id=id)
    user = request.user
    
    return render_item_view(request, user, current_item)


@login_required
def item_bid(request, id):
    message = ""
    if request.method == "POST":
        user = request.user
        item = AuctionList.objects.get(id=id)
        user_bid = float(request.POST["bid"])
        all_bids = Bid.objects.filter(item=item)  # returns all bids on the specific item

        leading_bid = item.leading_bid

        if user.is_authenticated:
            if user_bid <= leading_bid:
                # Render item_view
                warning = "Enter bid larger than leading price"
                return render_item_view(request, user, item, "", warning)
            
            # Change bid if the user has already bid the item
            for bid in all_bids:
                if bid.user == user:
                    bid.price = user_bid
                    bid.save()

                    # Change leading_bid to newest bid
                    item.leading_bid = user_bid
                    item.save()

                    message = "Your Bid has been updated"
                    return render_item_view(request, user, item, message)

            
            # add new valid bid
            new_bid = Bid()
            new_bid.user = user
            new_bid.item = item
            new_bid.price = user_bid
            new_bid.save()

            # Updating item
            item.bid_count += 1
            item.leading_bid = user_bid
            item.save()


        message = "Bid is successfully added."
        return render_item_view(request, user, item, message)
                

def closed_listing(request):
    if request.method == "GET":
        closed_item = AuctionList.objects.filter(winner=request.user, is_available=False)
        return render(request, "auctions/closed_listing.html", {
            "closed_item": closed_item,
        })

    else:
        item_id = request.POST["id"]
        item = AuctionList.objects.get(pk=item_id)
        item.is_available = False
        
        bids_on_item = Bid.objects.filter(item=item)
        # find winner who has higher bid
        for bid in bids_on_item:
            if bid.price == item.leading_bid:
                item.winner = bid.user

        item.save()
        return HttpResponseRedirect(reverse("index"))
