from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.urls import reverse

from users.forms import CustomUserCreationForm
from users.models import Customer

# Create your views here.


def create_customer(request: HttpRequest):
    """to register new costumer"""
    if request.method == "POST":
        form = CustomUserCreationForm(data=request.POST)
        if form.is_valid():
            new_user = form.save()
            Customer.objects.create(user=new_user)
            login(request, new_user)
            messages.success(
                request,
                f"successfully registered as {request.POST['username']}, Welcome!",
            )
            return redirect(reverse("home"))
    else:
        form: CustomUserCreationForm = CustomUserCreationForm()
    context = {"form": form}
    return render(request, "users/create_costumer.html", context)


def login_view(request: HttpRequest):
    form = AuthenticationForm()
    context = {"form": form}

    if request.method == "POST":
        form.data = request.POST

        user = authenticate(
            request,
            username=request.POST.get("username"),
            password=request.POST.get("password"),
        )
        if user:
            login(request, user)
            messages.success(request, "log in successful")
            return redirect(reverse("home"))
        else:
            messages.error(request, "username and password do not match.")
            return render(request, "users/login.html", context)

    return render(request, "users/login.html", context)
