"""forms module for spicita app"""

from django import forms

from spicita.models import Order


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields: list = ["address", "note"]
        exclude: list = ["items"]


