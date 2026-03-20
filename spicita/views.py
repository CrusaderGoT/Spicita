from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, QueryDict
from django.shortcuts import redirect, render

from spicita.forms import OrderForm
from spicita.models import Dish, Extra, Order, OrderItem, OrderItemExtra
from users.models import Customer

# Create your views here.


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
        new_order = Order.objects.create(customer=customer, address=address, note=note, total_price=0)

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
                    order_item_extra_obj, created = OrderItemExtra.objects.get_or_create(
                        order_item=order_item_obj,
                        extra=extra_obj,
                        defaults={"quantity": amount},
                    )
                    if not created:
                        # update quantity if the relation already existed
                        order_item_extra_obj.quantity = amount
                        order_item_extra_obj.save()
                    order_item_obj.extras.add(order_item_extra_obj)

        new_order.ordered = True
        # saving will call calculate_price via the model's save override
        new_order.save()  # save again to compute total price
        print(new_order.total_price, "price", new_order.items.get_queryset())
        return redirect("pay", new_order.ticket)

    return render(request, "spicita/buy-food.html", context)


def pay(request: HttpRequest, order_ticket: str):
    """view for paying for order"""
    order = Order.objects.get(ticket=order_ticket)
    if request.method == "GET":
        "payment form"
    else:
        "submit payment form"
    context = {"order": order, "amount": len(order.items.all())}
    return render(request, "spicita/pay.html", context)


def order_food(request: HttpRequest):
    """view for buying multiple dishes"""
    dishes = Dish.objects.all()
    if request.method == "POST":
        form = OrderForm(data=request.POST)
    else:
        form = OrderForm()
    context = {"form": form, "dishes": dishes}
    return render(request, "spicita/orderfood.html", context)
