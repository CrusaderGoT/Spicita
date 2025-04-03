'''url patterns for users/costumers app'''
from django.urls import path
from users import views

app_label = "users"

urlpatterns = [
    path('signup', views.create_customer, name='signup'),
    path('login', views.login_view, name='login'),
]