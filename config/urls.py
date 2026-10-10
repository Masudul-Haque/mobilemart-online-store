from django.contrib import admin
from django.urls import path
from store import views

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', views.home, name='home'),

    path('mobiles/', views.mobiles, name='mobiles'),

    path('brands/', views.brands, name='brands'),

    path('brand/<int:brand_id>/', views.brand_mobiles, name='brand_mobiles'),

    path('about/', views.about, name='about'),

    path('contact/', views.contact, name='contact'),

    path('login/', views.login, name='login'),

    path('logout/', views.logout_view, name='logout'),
    
    path('product/<int:mobile_id>/', views.product_detail, name='product_detail'),

    path('register/', views.register, name='register'),
    
    path('cart/', views.cart, name='cart'),
    
    path('order-details/<int:mobile_id>/', views.order_details, name='order_details'),
    
    path('checkout-details/', views.checkout_details, name='checkout_details'),
    
    path('wishlist/', views.wishlist, name='wishlist'),
    
    path('payment/', views.payment, name='payment'),
    
    path('buy-now/<int:mobile_id>/', views.buy_now, name='buy_now'),
    
    path('payment-success/', views.payment_success, name='payment_success'),
    
    path('verify-payment/', views.verify_payment, name='verify_payment'),
    
    path('my-orders/', views.my_orders, name='my_orders'),
    
    path('remove-from-wishlist/<int:wishlist_item_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    
    path('remove-from-cart/<int:cart_item_id>/', views.remove_from_cart, name='remove_from_cart'),
    
    path('increase-quantity/<int:cart_item_id>/', views.increase_quantity, name='increase_quantity'),
    
    path('decrease-quantity/<int:cart_item_id>/', views.decrease_quantity, name='decrease_quantity'),
    
    path('add-to-cart/<int:mobile_id>/', views.add_to_cart, name='add_to_cart'),
    
    path('add-to-wishlist/<int:mobile_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    
    
]