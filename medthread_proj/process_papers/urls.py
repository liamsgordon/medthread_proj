from django.urls import path
from . import views

urlpatterns = [
    path('hello/', views.say_hello),
    path('', views.home_page),
    path('dashboard/', views.dashboard),
    path('paper-summary/', views.paper_summary),
]