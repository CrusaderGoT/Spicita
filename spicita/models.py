from uuid import uuid4

from django.db import models

from users.models import Customer

# Create your models here.


class Dish(models.Model):
    FOODS = {
        "Rice": {
            "fried rice": "Fried",
            "jollof rice": "Jollof",
            "rice ofe akwu": "Ofe Akwu",
        },
        "Soup": {
            "oha soup": "Oha",
            "egusi soup": "Egusi",
        },
        "Snack": {
            "meat pie": "Meat Pie",
            "sharwama chicken": "Sharwama (Chicken)",
            "sharwama beef": "Sharwama (Beef)",
        },
    }
    PRICES = {
        "Rice": {
            "fried rice": 1000,
            "jollof rice": 800,
            "rice ofe akwu": 1200,
        },
        "Soup": {
            "oha soup": 700,
            "egusi soup": 700,
        },
        "Snack": {
            "meat pie": 450,
            "sharwama chicken": 950,
            "sharwama beef": 900,
        },
    }
    name = models.CharField(max_length=150, choices=FOODS, unique=True)
    extras = models.ManyToManyField("spicita.Extra")
    added_on = models.DateTimeField(auto_now_add=True)
    icon = models.ImageField(null=True, blank=True, upload_to="static/food_icons")
    price = models.DecimalField(decimal_places=2, max_digits=10, editable=False)
    description = models.TextField(max_length=500, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Dishes"

    def __str__(self) -> str:
        return self.name.title()


class Extra(models.Model):
    EXTRA = {
        "Drinks": {
            "sprite": "Sprite",
            "coke": "Coca-Cola",
            "pepsi": "Pepsi",
        },
        "Rice": {
            "chicken": "Chicken",
            "beef": "Beef",
        },
        "Soup": {
            "fufu": "Fufu",
            "soup": "Soup",
            "sauce": "Sauce",
        },
    }
    EXTRAS = models.TextChoices(
        "Extras", ("sprite", "coke", "pepsi", "chicken", "beef", "fufu", "soup")
    )
    name = models.CharField(max_length=150, choices=EXTRA, unique=True, null=True)
    icon = models.ImageField(upload_to="static/extra_icons", blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self) -> str:
        return self.name.title()


class OrderItem(models.Model):
    dish = models.ForeignKey(
        "spicita.Dish", blank=True, on_delete=models.CASCADE, null=True
    )
    extra = models.ForeignKey(
        "spicita.Extra", blank=True, on_delete=models.CASCADE, null=True
    )
    dish_quantity = models.PositiveIntegerField(default=1, blank=True)
    extra_quantity = models.PositiveIntegerField(default=1, blank=True)

    def __str__(self) -> str:
        if self.dish is None:
            return f"{self.extra} x {self.extra_quantity}"
        else:
            return f"{self.dish} x {self.dish_quantity}"


class Order(models.Model):
    items = models.ManyToManyField("spicita.OrderItem", editable=False)
    total_price = models.PositiveIntegerField(
        verbose_name="Total Price of Order (Naira)", editable=False
    )
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    address = models.TextField(max_length=300, blank=False)
    note = models.TextField(max_length=300, blank=True)
    ordered = models.BooleanField(default=False, editable=False)
    delivered = models.BooleanField(default=False, editable=False)
    date = models.DateTimeField(auto_now_add=True)
    ticket = models.UUIDField(
        primary_key=True, default=uuid4, editable=False, unique=True
    )

    def calculate_price(self):
        """for calculating to price before save"""
        price_list = []
        for order_item in self.items.all():
            if order_item.dish:
                price = order_item.dish.price * order_item.dish_quantity
                price_list.append(int(price))
            elif order_item.extra:
                price = order_item.extra.price * order_item.extra_quantity
                price_list.append(int(price))
        t_price = sum(price_list)
        return t_price

    def save(self, *args, **kwargs):
        self.total_price = self.calculate_price()
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        # Delete associated OrderItem objects
        self.items.all().delete()
        # Call the delete method of the base class
        return super().delete(using=using, keep_parents=keep_parents)

    def __str__(self) -> str:
        output = f"{self.customer}/{self.ticket}"
        return output
