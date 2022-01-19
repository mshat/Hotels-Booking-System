from django.urls import path
from . import views

urlpatterns = [
    path('hotels', views.HotelsListView.as_view()),
    path('me', views.PersonView.as_view()),
    path('reservations', views.ReservationsListView.as_view()),
    path('reservations/<str:uid>', views.ReservationView.as_view()),
    path('loyalty', views.LoyaltyView.as_view()),
    path('payment/<str:uid>', views.PaymentView.as_view()),
    path('payments', views.PaymentsListView.as_view()),
]