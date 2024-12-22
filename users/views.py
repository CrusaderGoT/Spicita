from django.shortcuts import render, HttpResponse, redirect
from users.models import Customer
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate
from django.contrib import messages
# Create your views here.

def create_customer(request):
    '''to register new costumer'''
    if request.method != 'POST':
        form = UserCreationForm()
    else:
        form = UserCreationForm(data=request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.username = request.POST['username']
            new_user.email = request.POST['email']
            new_user.password1 = request.POST['password1']
            new_user.password2 = request.POST['password2']
            new_user.save()
            Customer.objects.create(user=new_user,
                                    address=request.POST['address'])
            login(request, new_user)
            messages.success(request, f'successfully registered as {request.POST["username"]}, Welcome!')
            return redirect(request.path)
        else:
            HttpResponse('invalid')
    context = {'form': form}
    return render(request, 'users/create_costumer.html', context)
    
def login(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        user = authenticate(request, username=request.POST.get('username'),
                            password=request.POST.get('password'))
        if user:
            login(user)
            messages.success(request, 'log in successful')
            return redirect(request.path)
        else:
            messages.error(request, 'username and password do not match.')
            return redirect('login')
    else:
        form = AuthenticationForm()
    context = {'form': form}
    return render(request, 'users/login.html', context)