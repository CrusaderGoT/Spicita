"""forms module for spicita app"""

from django import forms

from spicita.models import Order


class OrderForm(forms.ModelForm[Order]):
    class Meta:
        model = Order
        fields: list = ["address", "note"]
        exclude: list = ["items"]


