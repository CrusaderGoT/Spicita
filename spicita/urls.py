"""url patterns for the spicita app"""

from django.urls import path

from spicita import views

app_label = "spicita"

urlpatterns = [
    path("", views.home, name="home"),
    path("buy/<int:dish_pk>/", views.buy_food, name="buy_food"),
    path("pay/<str:order_ticket>/", views.init_pay, name="pay"),
    path("verify/<str:order_ticket>/", views.verify_payment, name="verify_pay"),
    path("status/<str:order_ticket>/", views.order_status, name="order_status"),
    path("webhook/paystack/", views.paystack_webhook, name="pay_webhook"),
]
