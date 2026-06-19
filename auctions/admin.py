from django.contrib import admin

from .models import User, AuctionList, Bid


admin.site.register(User)

@admin.register(AuctionList)
class AuctionListAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "is_available", "owner", "created_at")


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ("item", "price", "user")
