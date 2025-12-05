from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('webhook/', views.whatsapp_webhook, name='whatsapp_webhook'),
    path('api/bookings/', views.BookingListCreate.as_view(), name='api_bookings'),
]
