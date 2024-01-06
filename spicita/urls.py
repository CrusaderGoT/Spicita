'''url patterns for the spicita app'''
from django.urls import path
from spicita import views

app_label = "spicita"

urlpatterns = [
    path('', views.home, name='home'),
    path('buy/<str:dish_name>/', views.buy_food, name='buyfood'),
    path('pay/<str:order_ticket>/', views.pay, name='pay'),
    path('order/', views.order_food, name='orderfood'),
]