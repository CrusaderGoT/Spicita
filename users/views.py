from django.shortcuts import render
from django.contrib.auth.forms import UserCreationForm

# Create your views here.

def create_customer(request):
    '''to register new costumer'''
    if request.method == 'GET':

        ''