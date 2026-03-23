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
    list_display = ["price", "added_on"]

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
    list_display = ["ticket", "total_price", "date"]

    def save_model(self, request: Any, obj: Any, form: Any, change: Any) -> None:
        if not obj.totalprice:
            obj.totalprice = self.calculate_price()
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
