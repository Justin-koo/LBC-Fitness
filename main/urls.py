from django.urls import path
from .views import *
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('', index, name='index'),
    path('scan_nfc/', scan_nfc, name='scan_nfc'),
    path('members', member_list, name='member_list'),
    path('members/create', create_member, name='create_member'),
    path('members/edit/<int:pk>', edit_member, name='edit_member'),
    path('members/<int:pk>/extend/', extend_membership, name='extend_membership'),
    path('members/delete/<int:pk>', delete_member, name='delete_member'),
    path('price', price_list, name='price_list'),
    path('price/create', create_price, name='create_price'),
    path('price/edit/<int:pk>', edit_price, name='edit_price'),
    path('price/delete/<int:pk>', delete_price, name='delete_price'),
    path('get-price', get_price, name='get_price'),
    path('payment/logs', payment_log_list, name='payment_log_list'),
]
