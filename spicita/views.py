from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.decorators import login_required
from spicita.models import Dish, Extra, OrderItem, Order
from users.models import Customer
from spicita.forms import OrderForm
import googlemaps
# Create your views here.
gmaps = googlemaps.Client(key='AIzaSyBvK-etEEd7Rm-eKeTI8kTa5XUap90bRW0')

def home(request):
    '''home view'''
    if request.method == 'GET':
        dishes = Dish.objects.all()
        context = {'dishes': dishes}
        return render(request, 'spicita/home.html', context)
    
@login_required(login_url='login', redirect_field_name='next')   
def buy_food(request, dish_name):
    '''view for buying a particular dish'''
    dish = Dish.objects.get(name=dish_name)
    extras = dish.extras.all()
    customer = Customer.objects.get(user=request.user)
    if request.method == 'POST':
        form = OrderForm(data=request.POST)
        if form.is_valid():
            lat = request.POST.get('latitude')
            lon = request.POST.get('longitude')
            """code for google maps, doesn't work cos no google atm card
            directions = gmaps.directions(
                "st. marks anglican church, nnewichi",
                (lat, lon),
                mode = 'driving',)
            distance = directions[0]['legs'][0]['distance']['text']
            duration = directions[0]['legs'][0]['duration']['text']"""
            new_order = form.save(commit=False)
            new_order.customer = customer
            if lat and lon:
                new_order.address = f"{lat} {lon}"
            else:
                new_order.address = request.POST.get('address')
            new_order.note = request.POST['note']
            new_order.save()
            # fetch selected extras
            selected_extras = [{'extra': request.POST[f"selectExtra{ extra.name }"],
                                'quantity': request.POST.get(f"extraNum{ extra.name }", 0),}
                                for extra in extras
                                if f"selectExtra{ extra.name }" in request.POST
                                and request.POST[f"selectExtra{ extra.name }"]]
            #create orderitem and add dish and extras to order
            order_item1 = OrderItem.objects.create(dish=dish,
                                                  dish_quantity=request.POST['dishAmt'])
            new_order.items.add(order_item1)
            for extra in selected_extras:
                # fetch extra instance
                extra_inst = Extra.objects.get(name=extra['extra'])
                extra_item = OrderItem.objects.create(extra=extra_inst,
                                                      extra_quantity=extra['quantity'])
                new_order.items.add(extra_item)
            new_order.ordered = True
            new_order.save() # save again to cumpute total price
            return redirect('pay', new_order.ticket)
    else:
        form = OrderForm()
    context = {'dish': dish, 'extras': extras, 'form': form, 'custumer': customer}
    return render(request, 'spicita/buyfood.html', context)

def pay(request, order_ticket):
    '''view for paying for order'''
    order = Order.objects.get(ticket=order_ticket)
    if request.method == 'GET':
        'payment form'
    else:
        'submit payment form'
    context = {'order': order, 'amount': len(order.items.all())}
    return render(request, 'spicita/pay.html', context)

def order_food(request):
    '''view for buying multiple dishes'''
    dishes = Dish.objects.all()
    extras = Extra.objects.all()
    if request.method == 'POST':
        form = OrderForm(data=request.POST)
    else:
        form = OrderForm()
    context = {'form': form, 'dishes': dishes, 'extras': extras}
    return render(request, 'spicita/orderfood.html', context)
    