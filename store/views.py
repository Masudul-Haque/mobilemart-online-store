import razorpay
from django.db.models import Q
from decimal import Decimal
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login as auth_login
from django.contrib.auth import authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from.models import Brand, Mobile, Cart, ContactMessage, Wishlist ,Order ,OrderItem 


def home(request):

    brands = Brand.objects.all()

    return render(request, 'index.html', {
        'brands': brands
    })

@login_required(login_url='/login/')
def mobiles(request):

    search = request.GET.get('search', '')

    if search:
        mobiles = Mobile.objects.filter(name__icontains=search)
    else:
        mobiles = Mobile.objects.all()

    return render(request, 'mobile.html', {
        'mobiles': mobiles,
        'search': search
    })


@login_required(login_url='/login/')
def brands(request):
    brands = Brand.objects.all()
    return render(request, 'brands.html', {'brands': brands})

@login_required(login_url='/login/')
def brand_mobiles(request, brand_id):
    brand = Brand.objects.get(id=brand_id)
    mobiles = Mobile.objects.filter(brand=brand)

    return render(request, 'brand_mobiles.html', {
        'brand': brand,
        'mobiles': mobiles
    })


@login_required(login_url='/login/')
def about(request):
    return render(request, 'about.html')


@login_required(login_url='/login/')
def contact(request):

    if request.method == 'POST':

        name = request.POST['name']
        email = request.POST['email']
        phone = request.POST['phone']
        message = request.POST['message']

        ContactMessage.objects.create(
            name=name,
            email=email,
            phone=phone,
            message=message
        )

        messages.success(
            request,
            'Your message has been sent successfully!'
        )

        return redirect('contact')

    return render(request, 'contact.html')

def logout_view(request):
    logout(request)
    return redirect('login')


# Login
def login(request):
    if request.method == 'POST':

        email = request.POST['email']
        password = request.POST['password']

        users = User.objects.filter(email=email)

        if not users.exists():
            messages.error(request, 'Invalid email or password!')
            return redirect('login')

        for user in users:
            authenticated_user = authenticate(
                request,
                username=user.username,
                password=password
            )

            if authenticated_user is not None:
                auth_login(request, authenticated_user)
                return redirect('home')

        messages.error(request, 'Invalid email or password!')
        return redirect('login')

    return render(request, 'login.html')


# Register
def register(request):
    if request.method == 'POST':

        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        # Check password
        if password != confirm_password:
            messages.error(request, 'Passwords do not match!')
            return redirect('register')

        # Check username
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists!')
            return redirect('register')

        # Check email
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered!')
            return redirect('register')

        # Create user
        User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        messages.success(
            request,
            'Registration successful! Please login to continue.'
        )

        return redirect('login')

    return render(request, 'register.html')

@login_required(login_url='/login/')
def product_detail(request, mobile_id):

    mobile = Mobile.objects.get(id=mobile_id)

    # Find similar mobiles
    recommended_mobiles = Mobile.objects.filter(
        Q(brand=mobile.brand) |
        Q(price__gte=mobile.price * Decimal('0.8'),
          price__lte=mobile.price * Decimal('1.2'))
    ).exclude(
        id=mobile.id
    ).distinct()[:4]

    return render(request, 'product_detail.html', {
        'mobile': mobile,
        'recommended_mobiles': recommended_mobiles
    })
    
@login_required(login_url='/login/')
def add_to_cart(request, mobile_id):

    mobile = Mobile.objects.get(id=mobile_id)

    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        mobile=mobile
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect('mobiles')  

@login_required(login_url='/login/')
def cart(request):

    cart_items = Cart.objects.filter(user=request.user)

    grand_total = 0

    for item in cart_items:
        item.total_price = item.mobile.price * item.quantity
        grand_total += item.total_price

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'grand_total': grand_total
    })  
    
    
@login_required(login_url='/login/')
def remove_from_cart(request, cart_item_id):

    item = Cart.objects.get(
        id=cart_item_id,
        user=request.user
    )

    item.delete()

    return redirect('cart') 

@login_required(login_url='/login/')
def increase_quantity(request, cart_item_id):

    item = Cart.objects.get(
        id=cart_item_id,
        user=request.user
    )

    item.quantity += 1
    item.save()

    return redirect('cart')


@login_required(login_url='/login/')
def decrease_quantity(request, cart_item_id):

    item = Cart.objects.get(
        id=cart_item_id,
        user=request.user
    )

    if item.quantity > 1:
        item.quantity -= 1
        item.save()

    return redirect('cart')

@login_required(login_url='/login/')
def add_to_wishlist(request, mobile_id):

    mobile = Mobile.objects.get(id=mobile_id)

    Wishlist.objects.get_or_create(
        user=request.user,
        mobile=mobile
    )

    return redirect('product_detail', mobile_id=mobile_id)

@login_required(login_url='/login/')
def wishlist(request):

    wishlist_items = Wishlist.objects.filter(user=request.user)

    return render(request, 'wishlist.html', {
        'wishlist_items': wishlist_items
    })
    
    
@login_required(login_url='/login/')
def remove_from_wishlist(request, wishlist_item_id):

    item = Wishlist.objects.get(
        id=wishlist_item_id,
        user=request.user
    )

    item.delete()

    return redirect('wishlist') 

@login_required(login_url='/login/')
def payment(request):

    client = razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        )
    )

    cart_items = Cart.objects.filter(user=request.user)

    grand_total = 0

    for item in cart_items:
        grand_total += item.mobile.price * item.quantity

    amount = int(grand_total * 100)

    order = client.order.create({
        'amount': amount,
        'currency': 'INR',
        'payment_capture': 1
    })
@login_required(login_url='/login/')
def payment(request):

    order_details = request.session.get('order_details')

    if not order_details:
        return redirect('checkout_details')

    buy_now_mobile_id = request.session.get('buy_now_mobile_id')

    if buy_now_mobile_id:
        mobile = Mobile.objects.get(id=buy_now_mobile_id)
        grand_total = mobile.price
    else:
        cart_items = Cart.objects.filter(user=request.user)

        grand_total = 0

        for item in cart_items:
            grand_total += item.mobile.price * item.quantity

    amount = int(grand_total * 100)

    client = razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        )
    )

    order = client.order.create({
        'amount': amount,
        'currency': 'INR',
        'payment_capture': 1
    })

    return render(request, 'payment.html', {
        'order': order,
        'amount': amount,
        'key_id': settings.RAZORPAY_KEY_ID,
        'grand_total': grand_total
    })
    
    from django.http import JsonResponse

@login_required(login_url='/login/')
def payment_success(request):
    return render(request, 'payment_success.html')


@login_required(login_url='/login/')
def verify_payment(request):

    if request.method == 'POST':

        client = razorpay.Client(
            auth=(
                settings.RAZORPAY_KEY_ID,
                settings.RAZORPAY_KEY_SECRET
            )
        )

        data = {
            'razorpay_order_id': request.POST.get('razorpay_order_id'),
            'razorpay_payment_id': request.POST.get('razorpay_payment_id'),
            'razorpay_signature': request.POST.get('razorpay_signature')
        }

        try:

            # Verify Razorpay payment
            client.utility.verify_payment_signature(data)

            # Get Order Details from session
            order_details = request.session.get('order_details')

            if not order_details:
                return redirect('checkout_details')

            amount = request.POST.get('amount')

            # Create Order
            order = Order.objects.create(

                user=request.user,

                full_name=order_details['full_name'],

                phone=order_details['phone'],

                address=order_details['address'],

                city=order_details['city'],

                pincode=order_details['pincode'],

                razorpay_order_id=data['razorpay_order_id'],

                razorpay_payment_id=data['razorpay_payment_id'],

                amount=amount,

                status='Paid'
            )

            # Check Buy Now
            mobile_id = request.session.get('buy_now_mobile_id')

            if mobile_id:

                mobile = Mobile.objects.get(id=mobile_id)

                OrderItem.objects.create(

                    order=order,

                    mobile=mobile,

                    quantity=1,

                    price=mobile.price
                )

            # Cart Checkout
            else:

                cart_items = Cart.objects.filter(
                    user=request.user
                )

                for item in cart_items:

                    OrderItem.objects.create(

                        order=order,

                        mobile=item.mobile,

                        quantity=item.quantity,

                        price=item.mobile.price
                    )

                cart_items.delete()


            # Clear session
            request.session.pop('order_details', None)
            request.session.pop('buy_now_mobile_id', None)


            return redirect('payment_success')


        except Exception:

            return render(request, 'payment.html', {
                'error': 'Payment verification failed!'
            })


    return redirect('payment')


@login_required(login_url='/login/')
def my_orders(request):

    orders = Order.objects.filter(
        user=request.user
    ).order_by('-created_at')

    return render(request, 'my_orders.html', {
        'orders': orders
    })
    
    
@login_required(login_url='/login/')
def buy_now(request, mobile_id):

    mobile = Mobile.objects.get(id=mobile_id)

    amount = int(mobile.price * 100)

    client = razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        )
    )

    order = client.order.create({
        'amount': amount,
        'currency': 'INR',
        'payment_capture': 1
    })

    return render(request, 'buy_now.html', {
        'mobile': mobile,
        'order': order,
        'amount': amount,
        'key_id': settings.RAZORPAY_KEY_ID
    })  
    
    
@login_required(login_url='/login/')
def order_details(request, mobile_id):

    mobile = Mobile.objects.get(id=mobile_id)

    if request.method == 'POST':

        request.session['order_details'] = {
            'full_name': request.POST.get('full_name'),
            'phone': request.POST.get('phone'),
            'address': request.POST.get('address'),
            'city': request.POST.get('city'),
            'pincode': request.POST.get('pincode'),
        }

        request.session['buy_now_mobile_id'] = mobile_id

        return redirect('payment')

    return render(request, 'order_details.html', {
        'mobile': mobile
    })
    
    
@login_required(login_url='/login/')
def checkout_details(request):

    if request.method == 'POST':

        request.session['order_details'] = {
            'full_name': request.POST.get('full_name'),
            'phone': request.POST.get('phone'),
            'address': request.POST.get('address'),
            'city': request.POST.get('city'),
            'pincode': request.POST.get('pincode'),
        }

        request.session['buy_now_mobile_id'] = None

        return redirect('payment')

    return render(request, 'order_details.html')         