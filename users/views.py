from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from users.models import Customer

# Create your views here.


def create_customer(request: HttpRequest):
    """to register new costumer"""
    if request.method != "POST":
        form: UserCreationForm[User] = UserCreationForm()
    else:
        form = UserCreationForm(data=request.POST)
        if form.is_valid():
            new_user = form.save()
            Customer.objects.create(user=new_user)
            login(request, new_user)
            messages.success(
                request,
                f"successfully registered as {request.POST['username']}, Welcome!",
            )
            return redirect(request.path)
        else:
            HttpResponse("invalid")
    context = {"form": form}
    return render(request, "users/create_costumer.html", context)


def login_view(request: HttpRequest):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        user = authenticate(
            request,
            username=request.POST.get("username"),
            password=request.POST.get("password"),
        )
        if user:
            login(request, user)
            messages.success(request, "log in successful")
            return redirect(request.path)
        else:
            messages.error(request, "username and password do not match.")
            return redirect("login")
    else:
        form = AuthenticationForm()
    context = {"form": form}
    return render(request, "users/login.html", context)
