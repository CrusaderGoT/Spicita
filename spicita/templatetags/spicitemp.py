"""module for custom templates for spicita app"""

from django import template

# build teplates here
register = template.Library()


@register.filter
def tprice(item):
    """function for getting the total
    price of an order item.\n
    (item quantity * item price)"""
    if item.dish is None:
        return item.extra.price * item.extra_quantity
    else:
        return item.dish.price * item.dish_quantity


@register.filter
def sort():
    ""
