from typing import Any

from django.contrib import admin
from django.db.models.query import QuerySet
from django.http.request import HttpRequest

from spicita.logic.file_handler import del_temp_files
from spicita.models import Dish, Extra, Order, OrderItem, OrderItemExtra


# For Dish Model
class AdminDish(admin.ModelAdmin):
    model = Dish
    list_display = ["name", "price", "added_on"]
    search_fields = ["name"]
    list_filter = ["added_on"]

    def delete_model(self, request: HttpRequest, obj: Dish) -> None:
        if request.method == "POST":
            if obj.icon:
                del_temp_files(obj.icon.path)
        return super().delete_model(request, obj)

    def delete_queryset(self, request: HttpRequest, queryset: QuerySet[Dish]) -> None:
        if request.method == "POST":
            for dish in queryset:
                if dish.icon:
                    del_temp_files(dish.icon.path)
        return super().delete_queryset(request, queryset)


class AdminExtra(admin.ModelAdmin):
    model = Extra
    list_display = ["name", "price"]
    search_fields = ["name"]

    def save_model(
        self, request: HttpRequest, obj: Extra, form: Any, change: bool
    ) -> None:
        super().save_model(request, obj, form, change)
        # Auto-add this extra to all its related dishes
        selected_dishes = form.cleaned_data.get("dishes", Dish.objects.none())
        for dish in selected_dishes:
            dish.extras.add(obj)


class OrderItemExtraInline(admin.TabularInline):
    model = OrderItemExtra
    extra = 0
    fields = ["extra", "quantity"]


class AdminOrderItem(admin.ModelAdmin):
    model = OrderItem
    list_display = ["dish", "order", "quantity"]
    search_fields = ["dish__name", "order__ticket"]
    list_filter = ["dish"]
    inlines = [OrderItemExtraInline]

    def delete_queryset(
        self, request: HttpRequest, queryset: QuerySet[OrderItem]
    ) -> None:
        order_item_ids = list(queryset.values_list("id", flat=True))
        OrderItemExtra.objects.filter(order_item_id__in=order_item_ids).delete()
        super().delete_queryset(request, queryset)


class AdminOrderItemExtra(admin.ModelAdmin):
    model = OrderItemExtra
    list_display = ["extra", "order_item", "quantity"]
    search_fields = ["extra__name", "order_item__dish__name"]
    list_filter = ["extra"]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ["dish", "quantity"]
    show_change_link = True


class AdminOrder(admin.ModelAdmin):
    model = Order
    list_display = ["ticket", "customer", "total_price", "ordered", "delivered", "date"]
    list_filter = ["ordered", "delivered", "date"]
    search_fields = ["ticket", "customer__user__username"]
    readonly_fields = ["total_price", "ticket", "date"]
    inlines = [OrderItemInline]

    def save_model(
        self, request: HttpRequest, obj: Order, form: Any, change: bool
    ) -> None:
        obj.total_price = obj.calculate_price()
        super().save_model(request, obj, form, change)

    def delete_queryset(self, request: HttpRequest, queryset: QuerySet[Order]) -> None:
        order_item_ids = list(
            OrderItem.objects.filter(order__in=queryset).values_list("id", flat=True)
        )
        OrderItemExtra.objects.filter(order_item_id__in=order_item_ids).delete()
        OrderItem.objects.filter(id__in=order_item_ids).delete()
        super().delete_queryset(request, queryset)


admin.site.register(Dish, AdminDish)
admin.site.register(Extra, AdminExtra)
admin.site.register(OrderItem, AdminOrderItem)
admin.site.register(OrderItemExtra, AdminOrderItemExtra)
admin.site.register(Order, AdminOrder)
