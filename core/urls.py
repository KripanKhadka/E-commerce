from django.urls import path
from . import views
from .views import (
    HomeView,
    ItemDetailView,
    OrderSummaryView,
    RegisterView,
    add_to_cart,
    remove_from_cart,
    checkout,
    payment,
    esewa_success,
    esewa_failure,
    order_status,
    order_detail,
    confirm_received,
    add_coupon,
    request_refund,
    account,
)

app_name = 'core'

urlpatterns = [
    # General Pages
    path('', HomeView.as_view(), name='home'),
    path('account/', account, name='account'),
    path('register/', RegisterView.as_view(), name='register'),
    path('product/<slug>/', ItemDetailView.as_view(), name='product'),
    
    # Cart & Checkout
    path('add-to-cart/<slug>/', add_to_cart, name='add-to-cart'),
    path('remove-from-cart/<slug>/', remove_from_cart, name='remove-from-cart'),
    path('order-summary/', OrderSummaryView.as_view(), name='order-summary'),
    path('checkout/', checkout, name='checkout'),
    
    # Payment Route
    path('payment/', payment, name='payment'),
    
    # Payment Gateway Callbacks
    path('esewa/success/', esewa_success, name='esewa-success'),
    path('esewa/failure/', esewa_failure, name='esewa-failure'),
    
    # Order Tracking & Actions
    path('order-status/', order_status, name='order-status'),
    path('orders/<int:pk>/', order_detail, name='order-detail'),
    path('confirm-received/', confirm_received, name='confirm-received'),
    path('add-coupon/', add_coupon, name='add-coupon'),
    path('request-refund/', request_refund, name='request-refund'),
]