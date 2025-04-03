from typing import Any

from django.contrib import admin
from django.db.models.query import QuerySet
from django.http.request import HttpRequest

from spicita.logic.file_handler import del_temp_files
from spicita.models import Dish, Extra, Order

# Register your models here.


# For Dish Model
class AdminDish(admin.ModelAdmin):
    model = Dish
    list_display = ["display_name", "get_price", "added_on"]

    def display_name(self, obj: Any):
        "function for computing the display name\n"
        "based on the Dish.name"
        if obj.name is not None:
            for k, v in Dish.FOODS.items():
                for k2, v2 in v.items():
                    if k2 == obj.name:
                        ext = f"{v2} {k}"
                        return ext
        else:
            return "No Dish"

    display_name.short_description = "Dishes"

    def get_price(self, obj: Any):
        if obj.price is not None:
            return f"\u20a6{obj.price}"
        else:
            return "N/A"

    get_price.short_description = "Price (Naira)"

    def save_model(self, request: Any, obj: Any, form: Any, change: Any) -> None:
        # set the price before save
        if not obj.price:
            for v in Dish.FOODS.values():
                for v2 in Dish.PRICES.values():
                    for k in v.keys():
                        for k1, v3 in v2.items():
                            if k == k1 and obj.name == k1:
                                obj.price = v3
        return super().save_model(request, obj, form, change)

    def delete_model(self, request: HttpRequest, obj: Any) -> None:
        # delete icon as obj is deleted
        if request.method == "POST":
            if obj.icon:
                del_temp_files(obj.icon.path)
        return super().delete_model(request, obj)

    def delete_queryset(self, request: HttpRequest, queryset: QuerySet[Any]) -> None:
        # delete icon for queryset delete method
        if request.method == "POST":
            for dish in queryset:
                if dish.icon:
                    del_temp_files(dish.icon.path)
        return super().delete_queryset(request, queryset)


# register Dish
admin.site.register(Dish, AdminDish)


# customize order in admin
class AdminOrder(admin.ModelAdmin):
    model = Order
    list_display = ["order_list", "tprice", "name", "date"]

    def name(self, obj: Any):
        return f"{obj.customer}/{obj.ticket}"

    name.short_description = "Order (customer/ticket)"

    def tprice(self, obj: Any):
        price_list = []
        for order_item in obj.items.all():
            if order_item.dish:
                price = order_item.dish.price * order_item.dish_quantity
                price_list.append(int(price))
            elif order_item.extra:
                price = order_item.extra.price * order_item.extra_quantity
                price_list.append(int(price))
        price = sum(price_list)
        if price:
            return f"\u20a6{price}"
        else:
            return "Not Computed!"

    tprice.short_description = "Total Price (Naira)"

    def order_list(self, obj: Any):
        return [i for i in obj.items.all() if i is not None]

    order_list.short_description = "Order"

    def save_model(self, request: Any, obj: Any, form: Any, change: Any) -> None:
        if not obj.tprice:
            obj.tprice = self.total_price(obj)
        return super().save_model(request, obj, form, change)

    def delete_model(self, request: HttpRequest, obj: Any) -> None:
        obj.items.all().delete()
        return super().delete_model(request, obj)

    def delete_queryset(self, request: HttpRequest, queryset: QuerySet[Any]) -> None:
        if request.method == "POST":
            for order in queryset:
                order.items.all().delete()
        return super().delete_queryset(request, queryset)

    def save_form(self, request: Any, form: Any, change: Any) -> Any:
        return super().save_form(request, form, change)


# register Order
admin.site.register(Order, AdminOrder)

# register Extra
admin.site.register(Extra)
