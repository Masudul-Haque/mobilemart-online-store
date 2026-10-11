import razorpay
from django.db.models import Q
from decimal import Decimal
from django.views.decorators.http import require_post
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
    order_details = request.session.get('order_details')

    if not order_details:
        return redirect('checkout_details')

    buy_now_mobile_id = request.session.get('buy_now_mobile_id')

    if buy_now_mobile_id:
        mobile = Mobile.objects.filter(id=buy_now_mobile_id).first()

        if not mobile:
            return redirect('mobiles')

        grand_total = mobile.price

    else:
        cart_items = Cart.objects.filter(user=request.user)

        if not cart_items.exists():
            return redirect('cart')

        grand_total = sum(
            (item.mobile.price * item.quantity for item in cart_items),
            Decimal('0.00')
        )

    amount = int(grand_total * 100)

    if amount <= 0:
        messages.error(request, 'Invalid payment amount.')
        return redirect('cart')

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

    request.session['razorpay_order_id'] = order['id']
    request.session['expected_payment_amount'] = amount

    return render(request, 'payment.html', {
        'order': order,
        'amount': amount,
        'key_id': settings.RAZORPAY_KEY_ID,
        'grand_total': grand_total
    })
@login_required(login_url='/login/')
def payment_success(request):
    return render(request, 'payment_success.html')


@login_required(login_url='/login/')
def verify_payment(request):
    if request.method != 'POST':
        return redirect('payment')

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
        # Confirm this is the order created for the current checkout.
        expected_order_id = request.session.get('razorpay_order_id')
        expected_amount = request.session.get('expected_payment_amount')

        if (
            not expected_order_id
            or not expected_amount
            or data['razorpay_order_id'] != expected_order_id
            or not data['razorpay_payment_id']
            or not data['razorpay_signature']
        ):
            raise ValueError('Invalid payment details.')

        # Verify Razorpay signature.
        client.utility.verify_payment_signature(data)

        # Fetch payment details from Razorpay and confirm it is captured.
        payment_info = client.payment.fetch(data['razorpay_payment_id'])

        if (
            payment_info.get('order_id') != expected_order_id
            or payment_info.get('status') != 'captured'
            or int(payment_info.get('amount', 0)) != int(expected_amount)
            or payment_info.get('currency') != 'INR'
        ):
            raise ValueError('Payment is not confirmed.')

        order_details = request.session.get('order_details')

        if not order_details:
            raise ValueError('Checkout details are missing.')

        mobile_id = request.session.get('buy_now_mobile_id')

        if mobile_id:
            mobile = Mobile.objects.get(id=mobile_id)
            order_items = [(mobile, 1)]
            grand_total = mobile.price
        else:
            cart_items = list(
                Cart.objects.filter(user=request.user).select_related('mobile')
            )

            if not cart_items:
                raise ValueError('Cart is empty.')

            order_items = [
                (item.mobile, item.quantity) for item in cart_items
            ]

            grand_total = sum(
                (mobile.price * quantity for mobile, quantity in order_items),
                Decimal('0.00')
            )

        # Check that the server-side total still matches the paid amount.
        if int(grand_total * 100) != int(expected_amount):
            raise ValueError('Order total has changed.')

        order = Order.objects.create(
            user=request.user,
            full_name=order_details['full_name'],
            phone=order_details['phone'],
            address=order_details['address'],
            city=order_details['city'],
            pincode=order_details['pincode'],
            razorpay_order_id=data['razorpay_order_id'],
            razorpay_payment_id=data['razorpay_payment_id'],
            amount=grand_total,
            status='Paid'
        )

        for mobile, quantity in order_items:
            OrderItem.objects.create(
                order=order,
                mobile=mobile,
                quantity=quantity,
                price=mobile.price
            )

        if not mobile_id:
            Cart.objects.filter(user=request.user).delete()

        request.session.pop('order_details', None)
        request.session.pop('buy_now_mobile_id', None)
        request.session.pop('razorpay_order_id', None)
        request.session.pop('expected_payment_amount', None)

        return redirect('payment_success')

    except Exception:
        return render(request, 'payment.html', {
            'error': (
                'Payment could not be verified. '
                'Please check My Orders before trying again.'
            )
        })


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
    mobile = Mobile.objects.filter(id=mobile_id).first()

    if not mobile:
        messages.error(request, 'Mobile not found.')
        return redirect('mobiles')

    order_details = request.session.get('order_details')

    if not order_details:
        request.session['buy_now_mobile_id'] = mobile.id
        return redirect('order_details', mobile_id=mobile.id)

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

    request.session['buy_now_mobile_id'] = mobile.id
    request.session['razorpay_order_id'] = order['id']
    request.session['expected_payment_amount'] = amount

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