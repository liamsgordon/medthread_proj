from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.

def say_hello(request):
    return HttpResponse('Hello World')

def home_page(request):
    return render(request, 'home.html')

def dashboard(request):
    return render(request, 'dashboard.html')

def paper_summary(request):
    return render(request, 'home.html')
