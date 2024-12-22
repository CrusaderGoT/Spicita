'''url patterns for users/costumers app'''
from django.urls import path
from users import views

app_label = "users"

urlpatterns = [
    path('sign-up', views.create_customer, name='sign-up'),
    path('login', views.login, name='login'),
]