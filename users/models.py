from typing import override

from django.contrib.auth.models import User
from django.db import models

# Create your models here.


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    address = models.TextField()
    orders = models.PositiveIntegerField(default=0)

    @override
    def __str__(self) -> str:
        return self.user.username
