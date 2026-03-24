from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, override
from uuid import uuid4

from django.db import models
from django.db.models import DecimalField, F, Sum

from users.models import Customer

if TYPE_CHECKING:
    from django_stubs_ext.db.models.manager import RelatedManager

# Create your models here.


class Dish(models.Model):
    name = models.CharField(max_length=150, unique=True)
    extras = models.ManyToManyField("spicita.Extra", blank=True)
    added_on = models.DateTimeField(auto_now_add=True)
    icon = models.ImageField(null=True, blank=True, upload_to="food_icons")
    price = models.DecimalField(decimal_places=2, max_digits=10, editable=True)
    description = models.TextField(max_length=500, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Dishes"

    @override
    def __str__(self) -> str:
        return self.name.title()


class Extra(models.Model):
    name = models.CharField(max_length=150, unique=True)
    icon = models.ImageField(upload_to="extra_icons", blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    dishes = models.ManyToManyField(Dish)

    @override
    def __str__(self) -> str:
        return self.name.title()


class Order(models.Model):
    # Reverse relation declared for Pylance — populated by OrderItem's FK related_name
    if TYPE_CHECKING:
        items: RelatedManager[OrderItem]
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    address = models.TextField(max_length=300, blank=False)
    note = models.TextField(max_length=300, blank=True)
    ordered = models.BooleanField(default=False, editable=False)
    delivered = models.BooleanField(default=False, editable=False)
    date = models.DateTimeField(auto_now_add=True)
    ticket = models.UUIDField(
        primary_key=True, default=uuid4, editable=False, unique=True
    )
    total_price = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0")
    )

    def calculate_price(self) -> Decimal:
        """for calculating to price before save"""
        dishes_total = self.items.aggregate(
            total=Sum(F("dish__price") * F("quantity"), output_field=DecimalField())
        )["total"] or Decimal("0")

        extras_total = OrderItemExtra.objects.filter(order_item__order=self).aggregate(
            total=Sum(
                F("extra__price") * F("quantity"),
                output_field=DecimalField(),
            )
        )["total"] or Decimal("0")

        return dishes_total + extras_total

    @property
    def total_item_count(self) -> int:
        from django.db.models import Sum

        items_count = self.items.aggregate(total=Sum("quantity"))["total"] or 0

        extras_count = (
            OrderItemExtra.objects.filter(order_item__order=self).aggregate(
                total=Sum("quantity")
            )["total"]
            or 0
        )

        return items_count + extras_count

    @override
    def save(self, *args, **kwargs) -> None:
        self.total_price = self.calculate_price()
        super().save(*args, **kwargs)

    @override
    def delete(self, using=None, keep_parents=False):
        order_item_ids = list(self.items.values_list("id", flat=True))
        OrderItemExtra.objects.filter(order_item_id__in=order_item_ids).delete()
        self.items.all().delete()
        return super().delete(using=using, keep_parents=keep_parents)

    @override
    def __str__(self) -> str:
        output = f"{self.customer}/{self.ticket}"
        return output


class OrderItem(models.Model):
    if TYPE_CHECKING:
        extras: RelatedManager[OrderItemExtra]
    order = models.ForeignKey(
        "spicita.Order", on_delete=models.CASCADE, related_name="items"
    )
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def total_price(self) -> Decimal:
        dish_total = self.dish.price * self.quantity
        extras_total = sum(
            ie.extra.price * ie.quantity
            for ie in self.extras.select_related("extra").all()
        )
        return dish_total + extras_total

    @override
    def __str__(self) -> str:
        return f"{self.dish} x {self.quantity}"


class OrderItemExtra(models.Model):
    order_item = models.ForeignKey(
        OrderItem, on_delete=models.CASCADE, related_name="extras"
    )
    extra = models.ForeignKey(Extra, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @override
    def __str__(self) -> str:
        return f"{self.extra} x {self.quantity}"
