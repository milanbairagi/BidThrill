from .models import AuctionList
from django import forms


class CreateListingForm(forms.ModelForm):
    class Meta:
        model = AuctionList
        fields = ["name", "description", "price", "image", "category"]

        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control my-2",
                "required": True,
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control my-2",
                "required": True,
            }),
            "price": forms.NumberInput(attrs={
                "class": "form-control my-2",
                "required": True,
                "placeholder": "0.0",
            }),
            "image": forms.FileInput(attrs={
                "class": "form-control my-2",
            }),
            "category": forms.Select(attrs={
                "class": "form-control my-2",
            }),
        }

        labels = {
            "image": "Image (optional)",
            "category": "Category",
        }
