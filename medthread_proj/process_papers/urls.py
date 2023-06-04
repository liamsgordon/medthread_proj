from django.urls import path
from . import views

urlpatterns = [
    path('hello/', views.say_hello),
    path('', views.home_page),
    path('dashboard/', views.dashboard),
    path('paper-summary/<int:id>/', views.paper_summary),

]