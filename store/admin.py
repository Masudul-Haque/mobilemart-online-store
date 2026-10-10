from django.contrib import admin
from .models import Brand, Mobile, ContactMessage, Cart, Wishlist, Order, OrderItem

admin.site.register(Brand)
admin.site.register(Mobile)
admin.site.register(ContactMessage)
admin.site.register(Cart)
admin.site.register(Wishlist)
admin.site.register(Order)
admin.site.register(OrderItem)