from django.urls import path

from . import views


app_name = 'control'
urlpatterns = [
    path('login/', views.login, name='login'),
    path('login/<str:source_url>/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('logout/<str:destination_url>/', views.logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
]