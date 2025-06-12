from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta
import json
import uuid
from .models import ChatMessage,Product,Cart,Order,Category,Review,Profile, Referral, Deal, Contact, WalletWithdrawal, Notification
from django.http import JsonResponse
from django.views.decorators.http import require_GET



def is_admin(user):
    return user.is_staff or user.is_superuser



@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    # Get all model objects
    orders = Order.objects.all()
    profiles = Profile.objects.all()
    referrals = Referral.objects.all()
    reviews = Review.objects.all()
    contacts = Contact.objects.all()
    deals = Deal.objects.all()
    categorys = Category.objects.all()
    products = Product.objects.all()
    chat_messages = ChatMessage.objects.all()
    carts = Cart.objects.all()
    
    # Get counts
    users_count = User.objects.count()
    products_count = Product.objects.count()
    orders_count = Order.objects.count()
    total_revenue = Order.objects.aggregate(Sum('total_price'))['total_price__sum'] or 0
    
    # Get growth percentages (comparing to last month)
    now = timezone.now()
    one_month_ago = now - timedelta(days=30)
    two_months_ago = now - timedelta(days=60)
    
    # Users growth
    users_last_month = User.objects.filter(date_joined__gte=one_month_ago).count()
    users_previous_month = User.objects.filter(date_joined__gte=two_months_ago, date_joined__lt=one_month_ago).count()
    users_growth = users_last_month - users_previous_month
    users_growth_percent = round((users_growth / max(1, users_previous_month)) * 100)
    
    # Products growth
    products_last_month = Product.objects.filter(created_at__gte=one_month_ago).count()
    products_previous_month = Product.objects.filter(created_at__gte=two_months_ago, created_at__lt=one_month_ago).count()
    products_growth = products_last_month - products_previous_month
    products_growth_percent = round((products_growth / max(1, products_previous_month)) * 100)
    
    # Orders growth
    orders_last_month = Order.objects.filter(created_at__gte=one_month_ago).count()
    orders_previous_month = Order.objects.filter(created_at__gte=two_months_ago, created_at__lt=one_month_ago).count()
    orders_growth = orders_last_month - orders_previous_month
    orders_growth_percent = round((orders_growth / max(1, orders_previous_month)) * 100)
    
    # Revenue growth
    revenue_last_month = Order.objects.filter(created_at__gte=one_month_ago).aggregate(Sum('total_price'))['total_price__sum'] or 0
    revenue_previous_month = Order.objects.filter(created_at__gte=two_months_ago, created_at__lt=one_month_ago).aggregate(Sum('total_price'))['total_price__sum'] or 0
    revenue_growth = revenue_last_month - revenue_previous_month
    revenue_growth_percent = round((revenue_growth / max(1, revenue_previous_month)) * 100)
    
    # Recent orders
    recent_orders = Order.objects.all().order_by('-created_at')[:5]
    
    # Top products
    top_products = Product.objects.all().order_by('-sold')[:5]
    
    # Pending orders count
    pending_orders_count = Order.objects.filter(status='Pending').count()
    
    # Notifications count
    notifications_count = 0  # You can implement this based on your notification system
    
    # Unread messages count
    unread_messages_count = 0  # You can implement this based on your messaging system
    
    # Chart data
    # Monthly sales data for the past 12 months
    monthly_sales = []
    monthly_labels = []
    
    for i in range(11, -1, -1):
        month_start = now - timedelta(days=30 * i + now.day - 1)
        month_end = month_start + timedelta(days=30)
        month_sales = Order.objects.filter(created_at__gte=month_start, created_at__lt=month_end).aggregate(Sum('total_price'))['total_price__sum'] or 0
        monthly_sales.append(float(month_sales))
        monthly_labels.append(month_start.strftime('%b'))
    
    # Category data
    categories_with_count = Category.objects.annotate(product_count=Count('products'))
    category_names = [category.name for category in categories_with_count]
    
    # Calculate sales per category
    category_sales = []
    for category in categories_with_count:
        category_products = Product.objects.filter(category=category)
        category_revenue = 0
        for product in category_products:
            product_orders = Order.objects.filter(product=product)
            product_revenue = product_orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
            category_revenue += float(product_revenue)
        category_sales.append(category_revenue)
    
    context = {
        'users_count': users_count,
        'products_count': products_count,
        'orders_count': orders_count,
        'total_revenue': total_revenue,
        'users_growth': users_growth,
        'users_growth_percent': users_growth_percent,
        'products_growth': products_growth,
        'products_growth_percent': products_growth_percent,
        'orders_growth': orders_growth,
        'orders_growth_percent': orders_growth_percent,
        'revenue_growth': revenue_growth,
        'revenue_growth_percent': revenue_growth_percent,
        'recent_orders': recent_orders,
        'top_products': top_products,
        'pending_orders_count': pending_orders_count,
        'notifications_count': notifications_count,
        'unread_messages_count': unread_messages_count,
        'monthly_sales': json.dumps(monthly_sales),
        'monthly_labels': json.dumps(monthly_labels),
        'category_names': json.dumps(category_names),
        'category_sales': json.dumps(category_sales),
        
        'orders': orders,
        'profiles': profiles,
        'referrals': referrals,
        'reviews': reviews,
        'contacts': contacts,
        'deals': deals,
        'categorys': categorys,  # Keep the original variable name for template compatibility
        'products': products,
        'chat_messages': chat_messages,
        'carts': carts,
    }
    
    return render(request, 'admin_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_users(request):
    search_query = request.GET.get('search', '')
    
    if search_query:
        profiles = Profile.objects.filter(
            Q(user__username__icontains=search_query) | 
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(referral_code__icontains=search_query)
        )
    else:
        profiles = Profile.objects.all()
    
    # Pagination
    paginator = Paginator(profiles, 10)  # Show 10 profiles per page
    page_number = request.GET.get('page')
    profiles = paginator.get_page(page_number)
    
    context = {
        'profiles': profiles,
        'pending_orders_count': Order.objects.filter(status='Pending').count(),
    }
    
    return render(request, 'admin_dashboard.html', context)

@login_required
@require_GET
def get_user_data(request, user_id):
    try:
        # Add debug logging
        print(f"Fetching data for user_id: {user_id}")
        
        user = User.objects.get(id=user_id)
        profile = user.profile  # Assuming you have a profile model related to User
        
        data = {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'bio': profile.bio if hasattr(profile, 'bio') else '',
            'wallet_balance': float(profile.wallet_balance) if hasattr(profile, 'wallet_balance') else 0,
            'points': profile.points if hasattr(profile, 'points') else 0,
            'is_verified': profile.is_verified if hasattr(profile, 'is_verified') else False,
            'profile_picture_url': profile.profile_picture.url if hasattr(profile, 'profile_picture') and profile.profile_picture else None,
        }
        
        # Add debug logging
        print(f"Returning data: {data}")
        
        return JsonResponse({'status': 'success', 'data': data})
    except User.DoesNotExist:
        print(f"User with ID {user_id} not found")
        return JsonResponse({'status': 'error', 'message': 'User not found'}, status=404)
    except Exception as e:
        print(f"Error fetching user data: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
@login_required
@user_passes_test(is_admin)
def admin_add_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        
        # Check if username or email already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return redirect('admin')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return redirect('admin')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Update profile
        profile = Profile.objects.get(user=user)
        
        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']
        
        if 'bio' in request.POST:
            profile.bio = request.POST.get('bio')
        
        # Generate auth token
        profile.auth_token = uuid.uuid4().hex
        profile.is_verified = True
        profile.save()
        
        messages.success(request, f'User {username} created successfully')
        return redirect('admin')
    
    return redirect('admin')

@login_required
@user_passes_test(is_admin)
def admin_edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile = get_object_or_404(Profile, user=user)
    
    if request.method == 'POST':
        # Update user
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.save()
        
        # Update profile
        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']
        
        profile.bio = request.POST.get('bio')
        profile.wallet_balance = request.POST.get('wallet_balance')
        profile.points = request.POST.get('points')
        profile.is_verified = 'is_verified' in request.POST
        profile.save()
        
        messages.success(request, f'User {user.username} updated successfully')
        return redirect('admin')
    
    context = {
        'user_obj': user,
        'profile': profile,
        'pending_orders_count': Order.objects.filter(status='Pending').count(),
    }
    
    return render(request, 'admin_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User {username} deleted successfully')
    
    return redirect('admin')

@login_required
def update_user(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        profile = user.profile
        
        # Update user fields
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.save()
        
        # Update profile fields
        profile.bio = request.POST.get('bio', '')
        profile.wallet_balance = request.POST.get('wallet_balance', 0)
        profile.points = request.POST.get('points', 0)
        profile.is_verified = 'is_verified' in request.POST
        
        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']
        
        profile.save()
        
        messages.success(request, 'User updated successfully')
        return redirect('admin')
    
    return redirect('admin')

@login_required
@user_passes_test(is_admin)
def admin_products(request):
    search_query = request.GET.get('search', '')
    
    if search_query:
        products = Product.objects.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )
    else:
        products = Product.objects.all()
    
    # Pagination
    paginator = Paginator(products, 10)  # Show 10 products per page
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    
    context = {
        'products': products,
        'categories': Category.objects.all(),
        'pending_orders_count': Order.objects.filter(status='Pending').count(),
    }
    
    return render(request, '.html', context)

@login_required
@user_passes_test(is_admin)
def admin_add_product(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        description = request.POST.get('description')
        price = request.POST.get('price')
        commission = request.POST.get('commission')
        stock = request.POST.get('stock')
        is_available = 'is_available' in request.POST
        
        category = get_object_or_404(Category, id=category_id)
        
        product = Product.objects.create(
            name=name,
            category=category,
            description=description,
            price=price,
            commission=commission,
            stock=stock,
            is_available=is_available
        )
        
        if 'image' in request.FILES:
            product.image = request.FILES['image']
            product.save()
        
        messages.success(request, f'Product {name} added successfully')
        return redirect('admin_dashboard')
    
    context = {
        'categories': Category.objects.all(),
        'pending_orders_count': Order.objects.filter(status='Pending').count(),
    }
    
    return render(request, 'admin_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.category = get_object_or_404(Category, id=request.POST.get('category'))
        product.description = request.POST.get('description')
        product.price = request.POST.get('price')
        product.commission = request.POST.get('commission')
        product.stock = request.POST.get('stock')
        product.is_available = 'is_available' in request.POST
        
        if 'image' in request.FILES:
            product.image = request.FILES['image']
        
        product.save()
        
        messages.success(request, f'Product {product.name} updated successfully')
        return redirect('admin_dashboard')
    
    context = {
        'product': product,
        'categories': Category.objects.all(),
        'pending_orders_count': Order.objects.filter(status='Pending').count(),
    }
    
    return render(request, 'admin_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f'Product {name} deleted successfully')
    
    return redirect('admin_dashboard')

@login_required
@user_passes_test(is_admin)
def admin_orders(request):
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    # Get all orders and order by most recent first
    orders = Order.objects.all().order_by('-created_at')
    
    if search_query:
        orders = orders.filter(
            Q(customer_name__icontains=search_query) | 
            Q(customer_email__icontains=search_query) |
            Q(product__name__icontains=search_query)
        )
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(orders, 10)  # Show 10 orders per page
    page_number = request.GET.get('page')
    orders_page = paginator.get_page(page_number)
    
    context = {
        'orders': orders_page,
        'search_query': search_query,
        'status_filter': status_filter,
        'pending_orders_count': Order.objects.filter(status='Pending').count(),
    }
    
    return render(request, 'admin_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_view_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    context = {
        'order': order,
        'pending_orders_count': Order.objects.filter(status='Pending').count(),
    }
    
    return render(request, 'admin_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_update_order_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        
        # Validate the status
        valid_statuses = ['Pending', 'Shipped', 'Delivered', 'Cancelled']
        if new_status in valid_statuses:
            order.status = new_status
            order.save()
            messages.success(request, f"Order #{order.id} status updated to {new_status}")
        else:
            messages.error(request, "Invalid status")
            
    return redirect('admin')

@login_required
@user_passes_test(is_admin)
def update_order_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        
        # Validate the status
        valid_statuses = ['Pending', 'Shipped', 'Delivered']
        if new_status in valid_statuses:
            order.status = new_status
            order.save()
            messages.success(request, f'Order #{order_id} status updated to {new_status}')
        else:
            messages.error(request, 'Invalid status provided')
            
    return redirect('admin')

@login_required
@user_passes_test(is_admin)
def admin_categories(request):
    search_query = request.GET.get('search', '')
    
    if search_query:
        categories = Category.objects.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    else:
        categories = Category.objects.all()
    
    # Pagination
    paginator = Paginator(categories, 10)
    page_number = request.GET.get('page')
    categories = paginator.get_page(page_number)
    
    context = {
        'categories': categories,
        'pending_orders_count': Order.objects.filter(status='Pending').count(),
    }
    
    return render(request, 'admin_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_add_category(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        
        category = Category.objects.create(
            name=name,
            description=description
        )
        
        if 'image' in request.FILES:
            category.image = request.FILES['image']
            category.save()
        
        messages.success(request, f'Category {name} added successfully')
        return redirect('admin_categories')
    
    return render(request, 'admin_dashboard.html', {
        'pending_orders_count': Order.objects.filter(status='Pending').count(),
    })

@login_required
@user_passes_test(is_admin)
def admin_edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.description = request.POST.get('description')
        
        if 'image' in request.FILES:
            category.image = request.FILES['image']
        
        category.save()
        
        messages.success(request, f'Category {category.name} updated successfully')
        return redirect('admin')
    
    context = {
        'category': category,
        'pending_orders_count': Order.objects.filter(status='Pending').count(),
    }
    
    return render(request, 'admin_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        name = category.name
        category.delete()
        messages.success(request, f'Category {name} deleted successfully')
    
    return redirect('admin')

@login_required
@user_passes_test(is_admin)
def admin_deals(request):
    search_query = request.GET.get('search', '')
    
    if search_query:
        deals = Deal.objects.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(seller__username__icontains=search_query)
        )
    else:
        deals = Deal.objects.all()
    
    # Pagination
    paginator = Paginator(deals, 10)
    page_number = request.GET.get('page')
    deals = paginator.get_page(page_number)
    
    context = {
        'deals': deals,
        'pending_orders_count': Order.objects.filter(status='Pending').count(),
    }
    
    return render(request, 'admin_dashboard.html', context)



@login_required
@user_passes_test(is_admin)
def admin_carts(request):
    search_query = request.GET.get('search', '')
    
    if search_query:
        carts = Cart.objects.filter(
            Q(user__username__icontains=search_query) | 
            Q(product__name__icontains=search_query)
        )
    else:
        carts = Cart.objects.all()
    
    # Pagination
    paginator = Paginator(carts, 10)
    page_number = request.GET.get('page')
    carts = paginator.get_page(page_number)
    
    context = {
        'carts': carts,
        'pending_orders_count': Order.objects.filter(status='Pending').count(),
    }
    
    return render(request, 'admin_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_reviews(request):
    search_query = request.GET.get('search', '')
    rating_filter = request.GET.get('rating', '')
    
    reviews = Review.objects.all()
    
    if search_query:
        reviews = reviews.filter(
            Q(user_name__icontains=search_query) | 
            Q(comment__icontains=search_query) |
            Q(product__name__icontains=search_query)
        )
    
    if rating_filter:
        reviews = reviews.filter(rating=rating_filter)
    
    # Pagination
    paginator = Paginator(reviews, 10)
    page_number = request.GET.get('page')
    reviews = paginator.get_page(page_number)
    
    context = {
        'reviews': reviews,
        'pending_orders_count': Order.objects.filter(status='Pending').count(),
    }
    
    return render(request, 'admin_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_view_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    
    context = {
        'review': review,
        'pending_orders_count': Order.objects.filter(status='Pending').count(),
    }
    
    return render(request, 'admin_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    
    if request.method == 'POST':
        product_name = review.product.name
        user_name = review.user_name
        review.delete()
        messages.success(request, f'Review by {user_name} for {product_name} deleted successfully')
    
    return redirect('admin')

@login_required
@user_passes_test(is_admin)
def admin_chat(request):
    search_query = request.GET.get('search', '')
    
    if search_query:
        chat_messages = ChatMessage.objects.filter(
            Q(user__username__icontains=search_query) | 
            Q(message__icontains=search_query)
        )
    else:
        chat_messages = ChatMessage.objects.all().order_by('-timestamp')
    
    # Pagination
    paginator = Paginator(chat_messages, 10)
    page_number = request.GET.get('page')
    chat_messages = paginator.get_page(page_number)
    
    context = {
        'chat_messages': chat_messages,
        'pending_orders_count': Order.objects.filter(status='Pending').count(),
    }
    
    return render(request, 'admin_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_view_message(request, message_id):
    message = get_object_or_404(ChatMessage, id=message_id)
    
    context = {
        'message': message,
        'pending_orders_count': Order.objects.filter(status='Pending').count(),
    }
    
    return render(request, 'admin_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_delete_message(request, message_id):
    message = get_object_or_404(ChatMessage, id=message_id)
    
    if request.method == 'POST':
        username = message.user.username
        message.delete()
        messages.success(request, f'Message from {username} deleted successfully')
    
    return redirect('admin')

@login_required
@user_passes_test(is_admin)
def admin_referrals(request):
    search_query = request.GET.get('search', '')
    
    if search_query:
        referrals = Referral.objects.filter(
            Q(referrer__username__icontains=search_query) | 
            Q(referred__username__icontains=search_query)
        )
    else:
        referrals = Referral.objects.all()
    
    # Pagination
    paginator = Paginator(referrals, 10)
    page_number = request.GET.get('page')
    referrals = paginator.get_page(page_number)
    
    context = {
        'referrals': referrals,
        'pending_orders_count': Order.objects.filter(status='Pending').count(),
    }
    
    return render(request, 'admin_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_view_referral(request, referral_id):
    referral = get_object_or_404(Referral, id=referral_id)
    
    context = {
        'referral': referral,
        'pending_orders_count': Order.objects.filter(status='Pending').count(),
    }
    
    return render(request, 'admin_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_withdrawals(request):
    withdrawals = WalletWithdrawal.objects.all().order_by('-created_at')
    pending_count = withdrawals.filter(status='pending').count()
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter and status_filter != 'all':
        withdrawals = withdrawals.filter(status=status_filter)
    
    # Search by username
    search_query = request.GET.get('q')
    if search_query:
        withdrawals = withdrawals.filter(
            Q(user__username__icontains=search_query) |
            Q(notes__icontains=search_query) |
            Q(admin_notes__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(withdrawals, 10)  # Show 10 withdrawals per page
    page_number = request.GET.get('page')
    withdrawals = paginator.get_page(page_number)
    
    return render(request, 'admin_withdrawals.html', {
        'withdrawals': withdrawals,
        'pending_count': pending_count,
        'status_filter': status_filter,
        'search_query': search_query
    })

@login_required
@user_passes_test(is_admin)
def admin_process_withdrawal(request, withdrawal_id):
    withdrawal = get_object_or_404(WalletWithdrawal, id=withdrawal_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        admin_notes = request.POST.get('admin_notes', '')
        
        if action == 'approve':
            # Check if user still has sufficient balance
            if withdrawal.amount > withdrawal.user.profile.wallet_balance:
                messages.error(request, f'User has insufficient balance. Current balance: ${withdrawal.user.profile.wallet_balance}')
                return redirect('admin_withdrawals')
            
            # Update withdrawal status
            withdrawal.status = 'approved'
            withdrawal.admin_notes = admin_notes
            withdrawal.save()
            
            # Deduct amount from user's wallet
            profile = withdrawal.user.profile
            profile.wallet_balance -= withdrawal.amount
            profile.save()
            
            # Create notification for user
            Notification.objects.create(
                user=withdrawal.user,
                notification_type='system',
                title='Withdrawal Approved',
                message=f'Your withdrawal request for ${withdrawal.amount} has been approved.',
                link='/withdrawal-history/'
            )
            
            messages.success(request, f'Withdrawal request for {withdrawal.user.username} has been approved.')
        
        elif action == 'reject':
            # Update withdrawal status
            withdrawal.status = 'rejected'
            withdrawal.admin_notes = admin_notes
            withdrawal.save()
            
            # Create notification for user
            Notification.objects.create(
                user=withdrawal.user,
                notification_type='system',
                title='Withdrawal Rejected',
                message=f'Your withdrawal request for ${withdrawal.amount} has been rejected.',
                link='/withdrawal-history/'
            )
            
            messages.success(request, f'Withdrawal request for {withdrawal.user.username} has been rejected.')
        
        return redirect('admin_withdrawals')
    
    return render(request, 'admin_process_withdrawal.html', {
        'withdrawal': withdrawal
    })

@login_required
@user_passes_test(is_admin)
def admin_withdrawal_history(request):
    withdrawals = WalletWithdrawal.objects.filter(status__in=['approved', 'rejected']).order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter and status_filter != 'all':
        withdrawals = withdrawals.filter(status=status_filter)
    
    # Search by username or notes
    search_query = request.GET.get('q')
    if search_query:
        withdrawals = withdrawals.filter(
            Q(user__username__icontains=search_query) |
            Q(notes__icontains=search_query) |
            Q(admin_notes__icontains=search_query)
        )
    
    # Filter by date range
    date_range = request.GET.get('date_range')
    if date_range:
        today = timezone.now().date()
        if date_range == 'today':
            withdrawals = withdrawals.filter(created_at__date=today)
        elif date_range == 'week':
            start_of_week = today - timezone.timedelta(days=today.weekday())
            withdrawals = withdrawals.filter(created_at__date__gte=start_of_week)
        elif date_range == 'month':
            start_of_month = today.replace(day=1)
            withdrawals = withdrawals.filter(created_at__date__gte=start_of_month)
        elif date_range == 'year':
            start_of_year = today.replace(month=1, day=1)
            withdrawals = withdrawals.filter(created_at__date__gte=start_of_year)
    
    # Export functionality
    export_format = request.GET.get('export')
    if export_format:
        # Here you would implement the export logic based on the format
        # This would typically involve using a library like pandas or django-import-export
        # For now, we'll just add a message
        messages.info(request, f"Export to {export_format.upper()} functionality will be implemented soon.")
    
    # Calculate statistics
    total_amount = withdrawals.filter(status='approved').aggregate(Sum('amount'))['amount__sum'] or 0
    approved_count = withdrawals.filter(status='approved').count()
    rejected_count = withdrawals.filter(status='rejected').count()
    
    # Pagination
    paginator = Paginator(withdrawals, 10)  # Show 10 withdrawals per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'withdrawals': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
        'date_range': date_range,
        'total_amount': total_amount,
        'approved_count': approved_count,
        'rejected_count': rejected_count
    }
    
    return render(request, 'admin_withdrawal_history.html', context)

@login_required
@user_passes_test(is_admin)
def admin_view_withdrawal(request, withdrawal_id):
    """View to display detailed information about a specific withdrawal"""
    withdrawal = get_object_or_404(WalletWithdrawal, id=withdrawal_id)
    
    # Get other withdrawals from the same user for the history section
    user_withdrawals = WalletWithdrawal.objects.filter(user=withdrawal.user).exclude(id=withdrawal_id).order_by('-created_at')[:5]
    
    context = {
        'withdrawal': withdrawal,
        'user_withdrawals': user_withdrawals
    }
    
    return render(request, 'admin_view_withdrawal.html', context)


@login_required
@user_passes_test(is_admin)
def admin_coadmins(request):
    search_query = request.GET.get('search', '')
    
    if search_query:
        coadmins = CoAdmin.objects.filter(
            Q(name__icontains=search_query) | 
            Q(email__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(user__username__icontains=search_query)
        )
    else:
        coadmins = CoAdmin.objects.all()
    
    # Pagination
    paginator = Paginator(coadmins, 10)  # Show 10 coadmins per page
    page_number = request.GET.get('page')
    coadmins = paginator.get_page(page_number)
    
    context = {
        'coadmins': coadmins,
        'pending_orders_count': Order.objects.filter(status='Pending').count(),
    }
    
    return render(request, 'admin_dashboard.html', context)