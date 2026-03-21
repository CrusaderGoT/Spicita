import hashlib
import hmac
import json

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, QueryDict
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from spicita.forms import OrderForm
from spicita.models import Dish, Extra, Order, OrderItem, OrderItemExtra
from users.models import Customer

# Create your views here.
PAYSTACK_HEADER = {
    "Authorization": f"Bearer {settings.PAYSTACK_SECRET}",
    "Content-Type": "application/json",
}
PAYSTACK_BASE_URL = "https://api.paystack.co"


def home(request: HttpRequest):
    """home view"""
    dishes = Dish.objects.all()
    context = {"dishes": dishes}
    return render(request, "spicita/home.html", context)


@login_required(login_url="login", redirect_field_name="next")
def buy_food(request: HttpRequest, dish_pk: int):
    """view for buying a particular dish"""
    dish = Dish.objects.get(pk=dish_pk)
    extras = dish.extras.all()
    user = request.user
    customer = Customer.objects.get(user=user)

    context = {"dish": dish, "extras": extras}

    if request.method == "POST":
        # process form data
        formData: QueryDict = request.POST
        lat = formData.get("latitude", "lat")
        long = formData.get("longitude", "long")
        address = "+".join([lat, long])
        note = formData.get("note")

        # create order with an initial total_price so DB constraints are satisfied
        new_order = Order.objects.create(
            customer=customer, address=address, note=note, total_price=0
        )

        dish_quantity = formData.get("dish-amount")

        dish_quantity = int(dish_quantity) if dish_quantity else 1
        order_item_obj, _ = OrderItem.objects.get_or_create(
            order=new_order, dish=dish, quantity=dish_quantity
        )

        # ensure the Order.items many-to-many is kept in sync (the model also has a ForeignKey)
        new_order.items.add(order_item_obj)

        if any(k.startswith("select-extra") for k in formData.keys()):
            for key, value in formData.items():
                if key.startswith("select-extra"):
                    extra_name = value
                    amount = formData.get(f"extra-amount-{extra_name}")
                    amount = int(amount) if amount else 1
                    extra_obj = Extra.objects.get(name=extra_name)
                    order_item_extra_obj, created = (
                        OrderItemExtra.objects.get_or_create(
                            order_item=order_item_obj,
                            extra=extra_obj,
                            defaults={"quantity": amount},
                        )
                    )
                    if not created:
                        # update quantity if the relation already existed
                        order_item_extra_obj.quantity = amount
                        order_item_extra_obj.save()
                    order_item_obj.extras.add(order_item_extra_obj)
        # saving will call calculate_price via the model's save override
        new_order.save()
        return redirect("pay", new_order.ticket)

    return render(request, "spicita/buy-food.html", context)


@login_required(login_url="login", redirect_field_name="next")
def init_pay(request: HttpRequest, order_ticket: str):
    """
    view for initializing payment for order.
    Creates a Paystack transaction and redirects to their hosted checkout.
    Shows a retry page if failed.
    """
    order = get_object_or_404(Order, ticket=order_ticket, customer__user=request.user)

    paystack_url = PAYSTACK_BASE_URL + "/transaction/initialize"

    order_status_url = request.build_absolute_uri(f"/status/{order.ticket}")

    if order.ordered:
        messages.info(request, "Order has already been placed.")
        return redirect(order_status_url)

    amount = order.total_price * 100  # to convert to kobo

    payload = {
        "amount": amount,
        "currency": "ngn",
        "reference": str(order.ticket),
        "callback_url": request.build_absolute_uri(f"/verify/{order.ticket}"),
        "metadata": {
            "order_id": str(order.ticket),
            "custom_fields": [
                {
                    "display_name": str(item.dish),
                    "variable_name": "Dish",
                    "value": item.quantity,
                    "extras": [
                        {
                            "display_name": str(ie.extra),
                            "value": ie.quantity,
                            "variable_name": "Extra",
                        }
                        for ie in item.extras.select_related("extra").all()
                    ],
                }
                for item in order.items.select_related("dish")
                .prefetch_related("extras__extra")
                .all()
            ],
        },
    }

    res = requests.post(
        paystack_url,
        json=payload,
        headers=PAYSTACK_HEADER,
        timeout=10,
    )

    data = res.json()

    if not data.get("status"):
        messages.error(request, data.get("message", "Failed to initialize payment"))

        return redirect(order_status_url)

    # redirect to paystack payment page
    return redirect(data["data"]["authorization_url"])


@login_required(login_url="login", redirect_field_name="next")
def verify_payment(request: HttpRequest, order_ticket: str):

    reference = request.GET.get("reference") or order_ticket

    url = PAYSTACK_BASE_URL + f"/transaction/verify/{reference}"

    order_status_url = request.build_absolute_uri(f"/status/{reference}")

    res = requests.post(url, headers=PAYSTACK_HEADER)

    data = res.json()

    if not data.get("status"):
        messages.error(request, "Failed to verify payment")
        return redirect(order_status_url)

    if data["data"]["status"] == "success":
        # get order and mark as order
        order = get_object_or_404(Order, ticket=reference)
        if not order.ordered:
            order.ordered = True
            order.save(update_fields=["ordered"])
        messages.success(request, "Order has been placed")
        return redirect(order_status_url)

    messages.success(request, "Order payment was not verified")
    return redirect(order_status_url)


@csrf_exempt
@require_POST
def paystack_webhook(request):
    """
    Paystack POSTs events here server-to-server.
    Handles edge cases where the user closes the tab before the callback fires.
    """
    # Verify the request is genuinely from Paystack
    paystack_sig = request.headers.get("x-paystack-signature", "")
    computed_sig = hmac.new(
        settings.PAYSTACK_SECRET.encode("utf-8"),
        request.body,
        hashlib.sha512,
    ).hexdigest()

    if not hmac.compare_digest(paystack_sig, computed_sig):
        return HttpResponse(status=401)

    event = json.loads(request.body)

    if event.get("event") == "charge.success":
        reference = event["data"]["reference"]
        try:
            order = Order.objects.get(ticket=reference)
            if not order.ordered:
                order.ordered = True
                order.save(update_fields=["ordered"])
        except Order.DoesNotExist:
            pass  # Log this in production

    return HttpResponse(status=200)

@login_required(login_url="login", redirect_field_name="next")
def order_status(request: HttpRequest, order_ticket: str):
    order = get_object_or_404(Order, ticket=order_ticket, customer__user=request.user)

    return render(request, "spicita/order-status.html", {"order": order})

def order_food(request: HttpRequest):
    """view for buying multiple dishes"""
    dishes = Dish.objects.all()
    if request.method == "POST":
        form = OrderForm(data=request.POST)
    else:
        form = OrderForm()
    context = {"form": form, "dishes": dishes}
    return render(request, "spicita/orderfood.html", context)
