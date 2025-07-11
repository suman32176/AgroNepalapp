from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.db.models import Q, Count, Sum, Avg, F
from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
import json
from .models import ChatMessage,Product,Cart,Order,Category,Review,Profile, Referral, Deal, LikedProduct,CoAdmin, DealChatMessage, Notification, ReferralCommission, WalletWithdrawal, ShareRecord
from .forms import ProductForm ,OrderForm,DealForm,ContactForm,CoAdminRegistrationForm,CartOrderForm
from django.contrib.auth.decorators import login_required,user_passes_test
import uuid
import pusher
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.core.paginator import Paginator
from decimal import Decimal
import logging
import traceback
from functools import wraps
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction, IntegrityError
from .utils import give_commission_if_delivered

# Set up logging
logger = logging.getLogger(__name__)

# Error handling decorator
def handle_errors(view_func):
    """Decorator to handle unexpected errors in views"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except Http404:
            # Re-raise 404 errors
            raise
        except PermissionDenied:
            # Re-raise permission denied errors
            raise
        except ValidationError as e:
            # Handle validation errors
            logger.error(f"Validation error in {view_func.__name__}: {str(e)}")
            from django.contrib import messages
            messages.error(request, f"Validation error: {str(e)}")
            return redirect('home')
        except IntegrityError as e:
            # Handle database integrity errors
            logger.error(f"Database integrity error in {view_func.__name__}: {str(e)}")
            from django.contrib import messages
            messages.error(request, "A database error occurred. Please try again.")
            return redirect('home')
        except Exception as e:
            # Handle all other unexpected errors
            logger.error(f"Unexpected error in {view_func.__name__}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            from django.contrib import messages
            messages.error(request, "An unexpected error occurred. Please try again or contact support.")
            return redirect('home')
    return wrapper

# Safe API response decorator
def safe_api_response(view_func):
    """Decorator for API views to return JSON error responses"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except Http404:
            return JsonResponse({'error': 'Resource not found'}, status=404)
        except PermissionDenied:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        except ValidationError as e:
            return JsonResponse({'error': f'Validation error: {str(e)}'}, status=400)
        except Exception as e:
            logger.error(f"API error in {view_func.__name__}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return JsonResponse({'error': 'An unexpected error occurred'}, status=500)
    return wrapper

# Pusher credentials with error handling
try:
    pusher_client = pusher.Pusher(
        app_id=settings.PUSHER_APP_ID,
        key=settings.PUSHER_KEY,
        secret=settings.PUSHER_SECRET,
        cluster=settings.PUSHER_CLUSTER,
        ssl=True
    )
except Exception as e:
    logger.error(f"Failed to initialize Pusher client: {str(e)}")
    pusher_client = None

# Create your views here.
def is_superuser(user):
    return user.is_superuser

def is_coadmin(user):
    try:
        profile = user.profile
        return profile.show_request_manager_btn
    except (Profile.DoesNotExist, AttributeError):
        return False

# Safe view wrappers
@handle_errors
def safe_home(request):
    return home(request)

@handle_errors
def safe_login_attempt(request):
    return login_attempt(request)

@handle_errors
def safe_register_attempt(request, referral_code=None):
    if referral_code:
        return register_attempt(request, referral_code)
    return register_attempt(request)

@handle_errors
def safe_success(request):
    return success(request)

@handle_errors
def safe_token_send(request):
    return token_send(request)

@handle_errors
def safe_verify(request, auth_token):
    return verify(request, auth_token)

@handle_errors
def safe_error_page(request):
    return error_page(request)

@handle_errors
@login_required
def safe_dashboard(request):
    return dashboard(request)

@handle_errors
def safe_logout_attempt(request):
    return logout_attempt(request)

@handle_errors
def safe_change_password(request):
    return change_password(request)

@handle_errors
@login_required
def safe_profile(request):
    return profile(request)

@handle_errors
@login_required
def safe_add_product(request):
    return add_product(request)

@handle_errors
def safe_product_detail(request, id):
    return product_detail(request, id)

@handle_errors
def safe_product(request):
    return product(request)

@handle_errors
def safe_chat_room(request):
    return chat_room(request)

@handle_errors
@csrf_exempt
@login_required
def safe_send_message(request):
    return send_message(request)

@handle_errors
@login_required
def safe_cart_view(request):
    return cart_view(request)

@handle_errors
@login_required
def safe_add_to_cart(request, product_id):
    return add_to_cart(request, product_id)

@handle_errors
@login_required
def safe_remove_from_cart(request, cart_id):
    return remove_from_cart(request, cart_id)

@handle_errors
def safe_order(request, product_id):
    return order(request, product_id)

@handle_errors
@login_required
def safe_order_details(request):
    return order_details(request)

@handle_errors
def safe_submit_review(request, id):
    return submit_review(request, id)

@handle_errors
@login_required
def safe_resend_verification(request):
    return resend_verification(request)

@handle_errors
@login_required
def safe_request_withdrawal(request):
    return request_withdrawal(request)

@handle_errors
@login_required
def safe_withdrawal_history(request):
    return withdrawal_history(request)

@handle_errors
@login_required
def safe_cancel_withdrawal(request, withdrawal_id):
    return cancel_withdrawal(request, withdrawal_id)

@handle_errors
@login_required
@user_passes_test(lambda u: u.is_staff or hasattr(u, 'coadmin_profile'))
def safe_admin_withdrawals(request):
    return admin_withdrawals(request)

@handle_errors
@login_required
@user_passes_test(lambda u: u.is_staff or hasattr(u, 'coadmin_profile'))
def safe_process_withdrawal(request, withdrawal_id):
    return process_withdrawal(request, withdrawal_id)

@handle_errors
def safe_deals_list(request):
    return deals_list(request)

@handle_errors
def safe_deal_detail(request, pk):
    return deal_detail(request, pk)

@handle_errors
@login_required
def safe_add_deal(request):
    return add_deal(request)

@handle_errors
@login_required
def safe_edit_deal(request, pk):
    return edit_deal(request, pk)

@handle_errors
@login_required
def safe_delete_deal(request, pk):
    return delete_deal(request, pk)

@handle_errors
@login_required
def safe_delete_product(request, id):
    return delete_product(request, id)

@handle_errors
@require_POST
@login_required
def safe_update_cart(request, item_id):
    return update_cart(request, item_id)

@handle_errors
@require_POST
@login_required
def safe_remove_from_cart_ajax(request, item_id):
    return remove_from_cart_ajax(request, item_id)

@handle_errors
@require_POST
@login_required
def safe_clear_cart(request):
    return clear_cart(request)

@handle_errors
@login_required
def safe_cart_order_history(request):
    return cart_order_history(request)

@handle_errors
@login_required
def safe_update_cart_order_status(request, order_id):
    return update_cart_order_status(request, order_id)

@handle_errors
@login_required
def safe_cancel_cart_order(request, order_id):
    return cancel_cart_order(request, order_id)

@handle_errors
@login_required
def safe_cart_checkout(request):
    return cart_checkout(request)

@handle_errors
@login_required
def safe_cart_order_confirmation(request, order_id):
    return cart_order_confirmation(request, order_id)

@handle_errors
@safe_api_response
@require_POST
def safe_get_cities(request):
    return get_cities(request)

@handle_errors
@safe_api_response
@require_POST
def safe_calculate_shipping_ajax(request):
    return calculate_shipping_ajax(request)

@handle_errors
@login_required
def safe_update_order_status(request, order_id):
    return update_order_status(request, order_id)

@handle_errors
@login_required
def safe_cancel_order(request, order_id):
    return cancel_order(request, order_id)

@handle_errors
def safe_job_page(request):
    return job_page(request)

@handle_errors
def safe_hi(request):
    return hi(request)

@handle_errors
def safe_home2(request):
    return home2(request)

@handle_errors
def safe_categories_view(request):
    return categories_view(request)

@handle_errors
def safe_category_detail_view(request, category_id):
    return category_detail_view(request, category_id)

@handle_errors
def safe_search_products(request):
    return search_products(request)

@handle_errors
def safe_newsletter_signup(request):
    return newsletter_signup(request)

@handle_errors
def safe_send_hello_email(request):
    return send_hello_email(request)

@handle_errors
def safe_seller_dashboard(request):
    return seller_dashboard(request)

@handle_errors
@login_required
def safe_edit_product(request, product_id):
    return edit_product(request, product_id)

@handle_errors
@login_required
def safe_toggle_wishlist(request, product_id):
    return toggle_wishlist(request, product_id)

@handle_errors
@login_required
def safe_coadmin_form(request):
    return coadmin_form(request)

@handle_errors
@user_passes_test(is_coadmin)
def safe_coadmin_page(request):
    return coadmin_page(request)

@handle_errors
@login_required
def safe_deal_chat(request, deal_id):
    return deal_chat(request, deal_id)

@handle_errors
@login_required
def safe_deal_chat_with_user(request, deal_id, user_id):
    return deal_chat_with_user(request, deal_id, user_id)

@handle_errors
@csrf_exempt
@login_required
def safe_send_deal_message(request):
    return send_deal_message(request)

@handle_errors
@login_required
def safe_check_new_deal_messages(request):
    return check_new_deal_messages(request)

@handle_errors
@user_passes_test(is_coadmin)
def safe_coadmin_orders(request):
    return coadmin_orders(request)

@handle_errors
@user_passes_test(is_coadmin)
def safe_coadmin_products(request):
    return coadmin_products(request)

@handle_errors
@user_passes_test(is_coadmin)
def safe_coadmin_deals(request):
    return coadmin_deals(request)

@handle_errors
@user_passes_test(is_coadmin)
def safe_coadmin_messages(request):
    return coadmin_messages(request)

@handle_errors
@safe_api_response
@user_passes_test(is_coadmin)
def safe_accept_order(request, order_id):
    return accept_order(request, order_id)

@handle_errors
@safe_api_response
@user_passes_test(is_coadmin)
def safe_mark_messages_read(request):
    return mark_messages_read(request)

@handle_errors
@login_required
def safe_notifications_list(request):
    return notifications_list(request)

@handle_errors
@login_required
def safe_mark_notification_read(request, notification_id):
    return mark_notification_read(request, notification_id)

@handle_errors
@login_required
def safe_mark_all_notifications_read(request):
    return mark_all_notifications_read(request)

@handle_errors
@safe_api_response
def safe_get_unread_notifications_count(request):
    return get_unread_notifications_count(request)

@handle_errors
@safe_api_response
@login_required
def safe_get_notifications_api(request):
    return get_notifications_api(request)

@handle_errors
@safe_api_response
@login_required
def safe_record_share(request):
    return record_share(request)

@handle_errors
@safe_api_response
@login_required
def safe_get_share_stats(request):
    return get_share_stats(request)

def home(request):
    # Fetch all products from the database
    categories = Category.objects.all()
    chat_messages = ChatMessage.objects.all().order_by('timestamp')
    products = Product.objects.all()
    trending_products = Product.objects.filter(is_available=True, sold__gt=10).order_by('-sold')[:6]
    recent_products = Product.objects.filter(created_at__gte=timezone.now() - timezone.timedelta(days=10)).order_by('-created_at')
    cart_items = []
    total_amount = 0
    if request.user.is_authenticated:
        cart_items = Cart.objects.filter(user=request.user)
        total_amount = sum(item.total_price() for item in cart_items)
        
    # Calculate average rating for each product
    for product in products:
        product.avg_rating = product.get_average_rating()
        product.review_count = product.get_rating_count() 
    
    context = {
        'products': products ,
        'trending_products': trending_products,
        'chat_messages': chat_messages,
        'cart_items':cart_items,
        'total_amount':total_amount,
        'recent_products':recent_products,
        'categories': categories,
        
    }
    return render(request, 'home.html',context)
    # if is_mobile(request):
    #     return render(request, 'mobile/home.html')
    # else:
    #     return render(request, 'home.html',context)


def login_attempt(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user_obj = User.objects.filter(username = username).first()
        if user_obj is None:
            messages.error(request, 'Username not found')
            return redirect('/register')
        
        profile_obj = Profile.objects.filter(user = user_obj).first()

        if not profile_obj.is_verified:
            messages.warning(request, "Profile not verified. Check your mail")
            return redirect('/login')
        
        user = authenticate(username = username, password = password)
        if user is None:
            messages.warning(request, 'Wrong password')
            return redirect('/login')
        
        login(request, user)
        return redirect('home')
    

    return render(request, 'login.html')



def register_attempt(request, referral_code=None):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            # Validate input data
            if not username or not email or not password:
                messages.error(request, "All fields are required")
                return redirect('register_attempt')
                
            if User.objects.filter(username=username).exists():
                messages.warning(request, "Username already exists")
                return redirect('register_attempt')
            
            if User.objects.filter(email=email).exists():
                messages.warning(request, "Email already exists")
                return redirect('register_attempt')
            
            # Create user
            user_obj = User.objects.create_user(username=username, email=email, password=password)
            
            # Generate auth token
            auth_token = str(uuid.uuid4())
            
            # Update the profile that was created by the signal
            profile_obj = Profile.objects.get(user=user_obj)
            profile_obj.auth_token = auth_token
            profile_obj.save()
            
            # Handle referral if provided
            if referral_code:
                try:
                    referrer_profile = Profile.objects.get(referral_code=referral_code)
                    profile_obj.referred_by = referrer_profile.user
                    profile_obj.save()

                    # Create referral record
                    Referral.objects.create(referrer=referrer_profile.user, referred=user_obj)
                    messages.success(request, f"You were referred by {referrer_profile.user.username}")
                except Profile.DoesNotExist:
                    messages.error(request, "Invalid referral code")
            
            # Send verification email
            send_mail_after_registration(email, auth_token)
            
            # Redirect to token sent page
            return redirect('token_send')
        
        except Exception as e:
            print(f"Registration error: {e}")
            messages.error(request, f"An error occurred during registration: {e}")
            return redirect('register_attempt')
    
    return render(request, 'register.html', {'referral_code': referral_code})




@login_required
def mark_successful_referral(request, referral_id):
    """Mark a referral as successful and award points"""
    referral = get_object_or_404(Referral, id=referral_id, referrer=request.user)
    
    if not referral.is_successful:
        # Mark as successful
        referral.is_successful = True
        referral.save()
        
        # Award points to the referrer
        referrer_profile = request.user.profile
        referrer_profile.points += settings.REFERRAL_REWARD
        referrer_profile.save()
        
        messages.success(request, f"Referral marked as successful! You earned {settings.REFERRAL_REWARD} points.")
    
    return redirect('dashboard')



def send_mail_after_registration(email, token):
    try:
        subject = 'Verify Your Account'
        # Use absolute URL with domain name for production
        verification_link = f'http://127.0.0.1:8000/verify/{token}'

        # HTML message with styling
        message = f'''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Verify Your Account</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f4;
                    padding: 20px;
                    color: #333;
                }}
                .container {{
                    background-color: #ffffff;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                    width: 80%;
                    max-width: 600px;
                    margin: 0 auto;
                }}
                h1 {{
                    color: #4CAF50;
                }}
                p {{
                    font-size: 16px;
                    line-height: 1.5;
                }}
                .btn {{
                    background-color: #4CAF50;
                    color: #fff;
                    padding: 12px 20px;
                    text-decoration: none;
                    border-radius: 4px;
                    font-size: 16px;
                    display: inline-block;
                }}
                .footer {{
                    font-size: 12px;
                    color: #aaa;
                    text-align: center;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Welcome to Our Website!</h1>
                <p>Hi there,</p>
                <p>Thank you for registering with us. To complete your registration and verify your email address, please click the button below:</p>
                <a href="{verification_link}" class="btn">Verify Your Account</a>
                <p>If you did not sign up for this account, please ignore this email.</p>
                <div class="footer">
                    <p>&copy; {2025} Your Website. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        '''

        # Send the email
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [email]
        send_mail(subject, '', email_from, recipient_list, html_message=message)
        print(f"Verification email sent to {email} with token {token}")
        return True
    except Exception as e:
        print(f"Error sending verification email: {e}")
        return False



def success(request):
    return render(request, 'success.html')

def token_send(request):
    return render(request, 'token_send.html')

def verify(request, auth_token):
    try:
        # Find the profile with the given auth token
        profile_obj = Profile.objects.filter(auth_token=auth_token).first()
        
        if profile_obj:
            # Check if already verified
            if profile_obj.is_verified:
                messages.success(request, "Your account is already verified. Please login.")
                login(request, user)
                return redirect('home')  # Make sure this URL name is correct
            
            # Verify the account
            profile_obj.is_verified = True
            profile_obj.save()
            messages.success(request, "Your account has been verified successfully. You can now login.")
            return redirect('home')  # Make sure this URL name is correct
        else:
            # No profile found with this token
            messages.error(request, "Invalid verification token. Please check your email or request a new verification link.")
            return redirect('error_page')  # Make sure this URL name is correct
        
    except Exception as e:
        print(f"Verification error: {e}")
        messages.error(request, "An error occurred during verification. Please try again or contact support.")
        return redirect('error_page')  # Make sure this URL name is correct

def error_page(request):
    return render(request, 'error.html')


@login_required(login_url='/login')
def dashboard(request):
    user = request.user
    context = {
        'user': user
    }
    return render(request, 'dashboard.html', context)

def logout_attempt(request):
    logout(request)
    return redirect('/login')

def change_password(request):
    if request.method == 'POST':
        username =  request.POST.get('username')
        email =  request.POST.get('email')
        new_password1 =  request.POST.get('new_password1')
        new_password2 =  request.POST.get('new_password2')

        if new_password1 != new_password2:
            messages.error(request, "Password don't match")
            return redirect('change_password')
        
        user_obj = User.objects.filter(username = username).first()

        if user_obj.email != email:
            messages.error(request, 'Incorrect email...')
            return redirect('change_password')

        if user_obj is None:
            messages.error(request, "User not found")
            return redirect('change_password')

        profile_obj = Profile.objects.filter(user = user_obj).first()
        if not profile_obj.is_verified:
            messages.warning(request, 'Please verify your account first...')
            return redirect('/')

        user_obj.set_password(new_password1)
        user_obj.save()

    return render(request, 'change_password.html')




@login_required
def profile(request):
    """View to display the user's profile and related information"""
    chat_messages = ChatMessage.objects.all().order_by('timestamp')
    profile = request.user.profile
    
    # Get users who registered using this user's referral code
    referred_users = User.objects.filter(profile__referred_by=request.user)
    
    # Get all referral commissions earned by this user
    commissions = ReferralCommission.objects.filter(referrer=request.user)
    
    # Calculate total commission earned
    total_commission = commissions.aggregate(Sum('commission_amount'))['commission_amount__sum'] or 0
    
    # Get recent commissions (last 5)
    recent_commissions = commissions.order_by('-created_at')[:5]
    
    # Show button_text based on profile verification and request
    show_btn = False
    if not hasattr(request.user, 'coadmin_profile') and profile.is_verified:
        show_btn = True  # Only show the CoAdmin request button for verified users who aren't already CoAdmins
    
    context = {
        'profile': profile,
        'referred_users': referred_users,
        'commissions': commissions,
        'total_commission': total_commission,
        'recent_commissions': recent_commissions,
        'show_btn': show_btn,
        'chat_messages': chat_messages,
    }
    
    return render(request, 'profile.html', context)


@login_required
def resend_verification(request):
    profile = Profile.objects.filter(user=request.user).first()

    if not profile:
        messages.error(request, "No profile found. Please register first.")
        return redirect('register_attempt')

    if profile.is_verified:
        messages.info(request, "Your account is already verified.")
        return redirect('profile')

    # Generate new verification token
    profile.auth_token = str(uuid.uuid4())

    try:
        # Resend verification email
        send_mail_after_registration(profile.user.email, profile.auth_token)
        profile.save()  # Save only after successful email sending

        messages.success(request, "Verification email has been sent. Please check your inbox.")
    except Exception as e:
        messages.error(request, f"Failed to send email: {str(e)}")

    return redirect('profile')


@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            # Save with current user as seller
            product = form.save(commit=False)
            product.seller = request.user
            product.save()
            
            # Notification to admin and coadmins about new product
            admins = User.objects.filter(is_superuser=True)
            coadmins = User.objects.filter(coadmin_profile__isnull=False)
            
            # Combine admin and coadmin users
            notification_users = list(admins) + list(coadmins)
            
            # Create notification for each admin/coadmin
            for user in notification_users:
                create_notification(
                    user=user,
                    notification_type='product',
                    title="New Product Added",
                    message=f"A new product '{product.name}' has been added by {request.user.username}. Price: Rs. {product.price}",
                    link=f"/product/{product.id}/"
                )
            
            messages.success(request, "Product added successfully.")
            return redirect('product')
        else:
            messages.error(request, "Error adding product. Please check the form.")
    else:
        form = ProductForm()
    
    context = {
        'form': form
    }
    return render(request, 'add_product.html', context)

def product_detail(request, id):
    # Use get_object_or_404 to fetch the product by ID
    product = get_object_or_404(Product, id=id)
    reviews = Review.objects.filter(product=product).order_by('-created_at')
    
    # Return the product detail template with the product data
    return render(request, 'product_details.html', {'product': product,'reviews':reviews})


@login_required
def delete_product(request, id):
    """Delete a product if the user is the seller or has appropriate permissions"""
    product = get_object_or_404(Product, id=id)
    
    # Check if user is the seller or has permission to delete
    if request.user != product.seller and not request.user.is_superuser and not is_coadmin(request.user):
        messages.error(request, "You don't have permission to delete this product.")
        return redirect('product')
    
    if request.method == 'POST':
        # Delete the product
        product_name = product.name
        product.delete()
        messages.success(request, f"Product '{product_name}' has been deleted successfully.")
        
        # Redirect based on user type
        if is_coadmin(request.user):
            return redirect('coadmin_products')
        else:
            return redirect('product')
    
    # If GET request, show confirmation page
    return render(request, 'delete_product_confirm.html', {'product': product})


def product(request):
    chat_messages = ChatMessage.objects.all().order_by('timestamp')
    user = request.user
    # Fetch all available products initially
    products = Product.objects.filter(is_available=True)
    liked_products = LikedProduct.objects.filter(user=user).values_list('product_id', flat=True)
    rating_range = [1, 2, 3, 4, 5]
    # Get filter parameters from the request
    category_id = request.GET.get('category', '')  # Default empty string
    search_query = request.GET.get('search', '')  # Default empty string
    sort_by = request.GET.get('sort', '')  # Default empty string

    # Apply category filter
    if category_id:
        products = products.filter(category_id=category_id)

    
    # Apply search filter
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )
        
    # Apply sorting
    if sort_by:
        if sort_by == 'price-low':
            products = products.order_by('price')
        elif sort_by == 'price-high':
            products = products.order_by('-price')
        elif sort_by == 'rating':
            products = products.annotate(
                avg_rating=Avg('reviews__rating'),
                review_count=Count('reviews')
            ).order_by(
                F('avg_rating').desc(nulls_last=True),  # Sort by avg_rating, nulls (no ratings) at the end
                F('sold').desc()  # For products with no ratings, sort by sold count
            )
        elif sort_by == 'newest':
            products = products.order_by('-created_at')
        elif sort_by == 'featured': # New: Sort by newest for featured
            products = products.order_by('-created_at')
            
    # Calculate average rating for each product
    for product in products:
        product.avg_rating = product.get_average_rating()
        product.review_count = product.get_rating_count()    

    # Fetch all categories for the dropdown
    categories = Category.objects.all()

    # Pagination
    paginator = Paginator(products, 100000)  
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    return render(request, 'product.html', {
        'chat_messages': chat_messages,
        'products': products,
        'categories': categories,
        'selected_category': category_id,  # Send back selected category to retain in dropdown
        'search_query': search_query,  # Send back search query to retain input value
        'sort_by': sort_by, # Send back sort_by to retain selected option
        'liked_products':liked_products
    })

# Chat function start >
def chat_room(request):
    chat_messages = ChatMessage.objects.all().order_by('timestamp')
    for message in chat_messages:
        message.timestamp = timezone.localtime(message.timestamp)
    return render(request, 'chat_room.html', {'chat_messages': chat_messages})




# @csrf_exempt
# @login_required
# def send_message(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             message = data.get('message', '').strip()

#             if not message:
#                 return JsonResponse({'status': 'error', 'message': 'Message cannot be empty'}, status=400)

#             user = request.user

#             # Save message to the database
#             chat_message = ChatMessage.objects.create(user=user, message=message)
        
#             # Correct timestamp format
#             formatted_timestamp = chat_message.timestamp.strftime('%Y-%m-%d %H:%M:%S')

#             # Send message to Pusher
#             pusher_client.trigger('chat', 'message', {
#                 'username': user.username,
#                 'message': message,
#                 'timestamp': formatted_timestamp  # Corrected timestamp format
#             })

#             return JsonResponse({'status': 'success', 'message': message})

#         except json.JSONDecodeError:
#             return JsonResponse({'status': 'error', 'message': 'Invalid JSON format'}, status=400)
#         except Exception as e:
#             return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

#     return JsonResponse({'status': 'failed', 'message': 'Invalid request method'}, status=405)


@csrf_exempt
@login_required
def send_message(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = data.get('message', '').strip()

            if not message:
                return JsonResponse({'status': 'error', 'message': 'Message cannot be empty'}, status=400)

            user = request.user

            # Save message to the database
            chat_message = ChatMessage.objects.create(user=user, message=message)
        
            # Correct timestamp format
            formatted_timestamp = chat_message.timestamp.strftime('%Y-%m-%d %H:%M:%S')

            # Try to send message to Pusher, but don't fail if it errors
            try:
                pusher_client.trigger('chat', 'message', {
                    'username': user.username,
                    'message': message,
                    'timestamp': formatted_timestamp
                })
            except Exception as pusher_error:
                print("Pusher error:", pusher_error)

            return JsonResponse({'status': 'success', 'message': message})

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON format'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'failed', 'message': 'Invalid request method'}, status=405)
# chat function end..........................


# cart start>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def cart_view(request):
    chat_messages = ChatMessage.objects.all().order_by('timestamp')
    """View to display the shopping cart"""
    cart_items = Cart.objects.filter(user=request.user)
    cart_total = sum(item.total_price() for item in cart_items)
    
    # Calculate shipping cost (example logic - adjust as needed)
    shipping_cost = Decimal('0.00')
    if cart_total < Decimal('1000.00') and cart_total > Decimal('0.00'):
        shipping_cost = Decimal('100.00')
    
    total_with_shipping = cart_total + shipping_cost
    
    context = {
        'chat_messages': chat_messages,
        'cart_items': cart_items,
        'cart_total': cart_total,
        'shipping_cost': shipping_cost,
        'total_with_shipping': total_with_shipping,
    }
    
    return render(request, 'cart.html', context)
@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    # Create notification for adding to cart
    create_notification(
        user=request.user,
        notification_type='product',
        title="Item added to cart",
        message=f"You've added {product.name} to your cart.",
        link="/cart/"
    )

    return redirect('cart')

# @login_required
# def cart_checkout(request):
#     """View to handle the checkout process for the cart"""
#     # Get cart items
#     cart_items = Cart.objects.filter(user=request.user)
    
#     # Redirect to cart if empty
#     if not cart_items.exists():
#         messages.warning(request, "Your cart is empty. Please add items before checkout.")
#         return redirect('cart')
    
#     # Calculate cart totals
#     cart_total = sum(item.total_price() for item in cart_items)
    
#     # Calculate initial shipping cost (will be updated via JS)
#     initial_shipping_cost = Decimal('0.00')
#     if cart_total < Decimal('1000.00') and cart_total > Decimal('0.00'):
#         initial_shipping_cost = Decimal('100.00')
    
#     if request.method == 'POST':
#         try:
#             # Get form data
#             customer_name = request.POST.get('customer_name')
#             customer_email = request.POST.get('customer_email')
#             customer_phone = request.POST.get('customer_phone')
#             province = request.POST.get('province')
#             city = request.POST.get('city')
#             street_address = request.POST.get('street_address')
#             delivery_instructions = request.POST.get('delivery_instructions', '')
#             payment_method = request.POST.get('payment_method')
            
#             # Validate required fields
#             if not all([customer_name, customer_email, customer_phone, province, city, street_address, payment_method]):
#                 messages.error(request, "Please fill in all required fields.")
#                 return redirect('cart_checkout')
            
#             # Generate a unique order group ID to link related orders
#             order_group = str(uuid.uuid4())[:8]  # Use first 8 characters for brevity
            
#             # Create a separate order for each cart item
#             first_order_id = None
            
#             # Check if the current user was referred by someone
#             has_referrer = hasattr(request.user, 'profile') and request.user.profile.referred_by is not None
#             referrer = request.user.profile.referred_by if has_referrer else None
            
#             # Get all admin users to allocate commission if there's no referrer
#             admin_users = User.objects.filter(is_superuser=True).first()
            
#             # Track total shipping for admin commission
#             total_shipping = Decimal('0.00')
            
#             for index, cart_item in enumerate(cart_items):
#                 # Create a new order for each product
#                 order = Order()
                
#                 # Set customer information
#                 order.customer_name = customer_name
#                 order.customer_email = customer_email
#                 order.customer_phone = customer_phone
#                 order.province = province
#                 order.city = city
#                 order.street_address = street_address
#                 order.delivery_instructions = delivery_instructions
#                 order.payment_method = payment_method
                
#                 # Set product and quantity from cart item
#                 order.product = cart_item.product
#                 order.quantity = cart_item.quantity
                
#                 # Add order group ID to link related orders
#                 order.order_group = order_group
                
#                 # Calculate shipping cost (only apply to the first order)
#                 shipping_cost = calculate_shipping_cost(province, city) if index == 0 else 0
#                 order.shipping_cost = shipping_cost
#                 total_shipping += Decimal(shipping_cost)
                
#                 # Get the product's commission amount
#                 product_commission = cart_item.product.commission
                
#                 # Calculate price for this item - commission will go to referrer or admin
#                 item_price = cart_item.product.price * cart_item.quantity
                
#                 # The actual amount paid to the seller is the item price minus commission
#                 seller_amount = item_price - product_commission
                
#                 # Total price for the order includes the full price plus shipping
#                 order.total_price = item_price + (shipping_cost if index == 0 else 0)
                
#                 # Save the order
#                 order.save()
                
#                 # Store the first order ID for redirection
#                 if index == 0:
#                     first_order_id = order.id
                
#                 # Handle the commission
                
#                 # if has_referrer:
#                 #     # Create a commission record for the referrer
#                 #     commission = ReferralCommission(
#                 #         referrer=referrer,
#                 #         referred_user=request.user,
#                 #         order=order,
#                 #         product=cart_item.product,
#                 #         commission_amount=product_commission
#                 #     )
#                 #     commission.save()
#                 if has_referrer:
#                     # Check if the referrer has shared this specific product before
#                     shared_product = ShareRecord.objects.filter(
#                         user=referrer,  # the referrer like 'ullu'
#                         product=cart_item.product  # the product being purchased
#                     ).exists()

#                     if shared_product:
#                         # Referrer shared this product, so give commission
#                         commission = ReferralCommission(
#                             referrer=referrer,
#                             referred_user=request.user,
#                             order=order,
#                             product=cart_item.product,
#                             commission_amount=product_commission
#                         )
#                         commission.save()
                    
#                     # Add the commission to the referrer's wallet
#                     referrer_profile = Profile.objects.get(user=referrer)
#                     referrer_profile.wallet_balance += product_commission
#                     referrer_profile.save()
                    
#                     # Notify the referrer about the commission
#                     create_notification(
#                         user=referrer,
#                         notification_type='commission',
#                         title="Commission earned!",
#                         message=f"You earned ₹{product_commission} commission from {request.user.username}'s purchase of {cart_item.product.name}",
#                         link="/profile/"
#                     )
#                 elif admin_users:
#                     # If no referrer, commission goes to admin
#                     admin_profile = Profile.objects.get(user=admin_users)
#                     admin_profile.wallet_balance += product_commission
#                     admin_profile.save()
            
#             # Add shipping fee to admin wallet
#             if admin_users and total_shipping > 0:
#                 admin_profile = Profile.objects.get(user=admin_users)
#                 admin_profile.wallet_balance += total_shipping
#                 admin_profile.save()
                
#                 # Notify admin about the shipping commission
#                 create_notification(
#                     user=admin_users,
#                     notification_type='commission',
#                     title="Shipping fee received",
#                     message=f"You received ₹{total_shipping} shipping fee from order #{first_order_id}",
#                     link="/admin_orders/"
#                 )
            
#             # Clear the cart
#             cart_items.delete()
            
#             # Create purchase notification
#             create_notification(
#                 user=request.user,
#                 notification_type='order',
#                 title="Purchase complete!",
#                 message=f"Your order has been placed successfully. Order #: {first_order_id}",
#                 link=f"/cart/confirmation/{first_order_id}/"
#             )
            
#             # Notify seller(s) about new order
#             for cart_item in list(cart_items):
#                 # Notify the seller about the new order
#                 create_notification(
#                     user=cart_item.product.seller,
#                     notification_type='order',
#                     title="New order received",
#                     message=f"You've received a new order for {cart_item.product.name}. Order #: {first_order_id}",
#                     link=f"/order_details/"
#                 )
            
#             # Redirect to the confirmation page
#             messages.success(request, "Your order has been placed successfully!")
#             return redirect('cart_order_confirmation', order_id=first_order_id)
            
#         except Exception as e:
#             # Log the error
#             print(f"Error creating order: {e}")
#             messages.error(request, f"An error occurred while processing your order: {e}")
#             return redirect('cart_checkout')
    
#     context = {
#         'cart_items': cart_items,
#         'cart_total': cart_total,
#         'shipping_cost': initial_shipping_cost,
#         'total_with_shipping': cart_total + initial_shipping_cost,
#     }
    
#     return render(request, 'cart_checkout.html', context)

@login_required
def cart_checkout(request):
    cart_items = Cart.objects.filter(user=request.user)

    if not cart_items.exists():
        messages.warning(request, "Your cart is empty. Please add items before checkout.")
        return redirect('cart')

    cart_total = sum(item.total_price() for item in cart_items)
    initial_shipping_cost = Decimal('100.00') if cart_total < Decimal('1000.00') else Decimal('0.00')

    if request.method == 'POST':
        try:
            # Collect form data
            customer_name = request.POST.get('customer_name')
            customer_email = request.POST.get('customer_email')
            customer_phone = request.POST.get('customer_phone')
            province = request.POST.get('province')
            city = request.POST.get('city')
            street_address = request.POST.get('street_address')
            delivery_instructions = request.POST.get('delivery_instructions', '')
            payment_method = request.POST.get('payment_method')

            if not all([customer_name, customer_email, customer_phone, province, city, street_address, payment_method]):
                messages.error(request, "Please fill in all required fields.")
                return redirect('cart_checkout')

            order_group = str(uuid.uuid4())[:8]
            first_order_id = None

            has_referrer = hasattr(request.user, 'profile') and request.user.profile.referred_by is not None
            referrer = request.user.profile.referred_by if has_referrer else None
            admin_users = User.objects.filter(is_superuser=True).first()

            total_shipping = Decimal('0.00')

            for index, cart_item in enumerate(cart_items):
                order = Order()
                order.customer_name = customer_name
                order.customer_email = customer_email
                order.customer_phone = customer_phone
                order.province = province
                order.city = city
                order.street_address = street_address
                order.delivery_instructions = delivery_instructions
                order.payment_method = payment_method
                order.product = cart_item.product
                order.quantity = cart_item.quantity
                order.order_group = order_group

                shipping_cost = calculate_shipping_cost(province, city) if index == 0 else 0
                order.shipping_cost = shipping_cost
                total_shipping += Decimal(shipping_cost)

                product_commission = cart_item.product.commission
                item_price = cart_item.product.price * cart_item.quantity
                order.total_price = item_price + (shipping_cost if index == 0 else 0)
                order.save()

                if index == 0:
                    first_order_id = order.id

                # ✅ Create commission but DO NOT give wallet balance now
                if has_referrer:
                    shared_product = ShareRecord.objects.filter(user=referrer, product=cart_item.product).exists()
                    if shared_product:
                        ReferralCommission.objects.create(
                            referrer=referrer,
                            referred_user=request.user,
                            order=order,
                            product=cart_item.product,
                            commission_amount=product_commission,
                            is_given=False  # Wait for delivery
                        )
                elif admin_users:
                    admin_profile = Profile.objects.get(user=admin_users)
                    admin_profile.wallet_balance += product_commission
                    admin_profile.save()

            if admin_users and total_shipping > 0:
                admin_profile = Profile.objects.get(user=admin_users)
                admin_profile.wallet_balance += total_shipping
                admin_profile.save()

                create_notification(
                    user=admin_users,
                    notification_type='commission',
                    title="Shipping fee received",
                    message=f"You received ₹{total_shipping} shipping fee from order #{first_order_id}",
                    link="/admin_orders/"
                )

            # Clear cart
            cart_items.delete()

            # Notify buyer
            create_notification(
                user=request.user,
                notification_type='order',
                title="Purchase complete!",
                message=f"Your order has been placed successfully. Order #: {first_order_id}",
                link=f"/cart/confirmation/{first_order_id}/"
            )

            # Notify sellers
            for cart_item in list(cart_items):
                create_notification(
                    user=cart_item.product.seller,
                    notification_type='order',
                    title="New order received",
                    message=f"You've received a new order for {cart_item.product.name}. Order #: {first_order_id}",
                    link=f"/order_details/"
                )

            messages.success(request, "Your order has been placed successfully!")
            return redirect('cart_order_confirmation', order_id=first_order_id)

        except Exception as e:
            print(f"Error creating order: {e}")
            messages.error(request, f"An error occurred while processing your order: {e}")
            return redirect('cart_checkout')

    context = {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'shipping_cost': initial_shipping_cost,
        'total_with_shipping': cart_total + initial_shipping_cost,
    }
    return render(request, 'cart_checkout.html', context)

@login_required
def cart_order_confirmation(request, order_id):
    """View to display order confirmation after successful checkout"""
    try:
        # Get the main order
        order = get_object_or_404(Order, id=order_id)
        
        # Get the order group
        order_group = order.order_group
        
        # If we have an order group, get all related orders
        related_orders = []
        if order_group:
            # Find all orders in this group
            related_orders = Order.objects.filter(order_group=order_group)
        
        # Calculate totals
        subtotal = sum(o.total_price - o.shipping_cost for o in related_orders) if related_orders else order.total_price - order.shipping_cost
        shipping = sum(o.shipping_cost for o in related_orders) if related_orders else order.shipping_cost
        total = subtotal + shipping
        
        context = {
            'order': order,
            'related_orders': related_orders,
            'subtotal': subtotal,
            'shipping': shipping,
            'total': total,
        }
        
        return render(request, 'cart_confirmation.html', context)
    except Exception as e:
        print(f"Error displaying confirmation: {e}")
        messages.error(request, f"An error occurred: {e}")
        return redirect('home')

@require_POST
@login_required
def update_cart(request, item_id):
    """AJAX view to update cart item quantity"""
    try:
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))
        
        # Get the cart item
        cart_item = get_object_or_404(Cart, id=item_id, user=request.user)
        
        # Update quantity and save
        cart_item.quantity = quantity
        cart_item.save()
        
        # Recalculate cart totals
        cart_items = Cart.objects.filter(user=request.user)
        cart_total = sum(item.total_price() for item in cart_items)
        
        # Calculate shipping cost (example logic - adjust as needed)
        shipping_cost = Decimal('0.00')
        if cart_total < Decimal('1000.00') and cart_total > Decimal('0.00'):
            shipping_cost = Decimal('100.00')
        
        total_with_shipping = cart_total + shipping_cost
        
        # Return updated values as JSON
        return JsonResponse({
            'success': True,
            'subtotal': float(cart_item.total_price()),
            'cart_total': float(cart_total),
            'shipping_cost': float(shipping_cost),
            'total_with_shipping': float(total_with_shipping),
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@require_POST
@login_required
def remove_from_cart_ajax(request, item_id):
    """AJAX view to remove an item from the cart"""
    try:
        # Get the cart item and delete it
        cart_item = get_object_or_404(Cart, id=item_id, user=request.user)
        cart_item.delete()
        
        # Recalculate cart totals
        cart_items = Cart.objects.filter(user=request.user)
        cart_total = sum(item.total_price() for item in cart_items)
        
        # Calculate shipping cost (example logic - adjust as needed)
        shipping_cost = Decimal('0.00')
        if cart_total < Decimal('1000.00') and cart_total > Decimal('0.00'):
            shipping_cost = Decimal('100.00')
        
        total_with_shipping = cart_total + shipping_cost
        
        # Return updated values as JSON
        return JsonResponse({
            'success': True,
            'cart_total': float(cart_total),
            'shipping_cost': float(shipping_cost),
            'total_with_shipping': float(total_with_shipping),
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def remove_from_cart(request, cart_id):
    """Regular view to remove an item from the cart (non-AJAX)"""
    cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
    product_name = cart_item.product.name
    
    # Create notification for removing from cart
    create_notification(
        user=request.user,
        notification_type='product',
        title="Item removed from cart",
        message=f"You've removed {product_name} from your cart.",
        link="/cart/"
    )
    
    cart_item.delete()
    messages.success(request, f"{product_name} removed from your cart.")
    return redirect('cart')

@require_POST
@login_required
def clear_cart(request):
    """AJAX view to clear the entire cart"""
    try:
        # Delete all cart items for the user
        Cart.objects.filter(user=request.user).delete()
        
        messages.success(request, 'Your cart has been cleared.')
        return JsonResponse({'success': True})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    

@require_POST
def get_cities(request):
    """AJAX view to get cities based on selected province"""
    try:
        data = json.loads(request.body)
        province = data.get('province', '')
        
        # Get cities for the selected province
        shipping_rates = {
            "Province 1": ["Biratnagar", "Dharan", "Itahari", "Damak", "Birtamod", "Mechinagar", "Urlabari"],
            "Province 2": ["Janakpur", "Birgunj", "Simara", "Kalaiya", "Malangwa", "Jaleshwar", "Rajbiraj"],
            "Bagmati": ["Kathmandu", "Lalitpur", "Bhaktapur", "Hetauda", "Bharatpur", "Bidur", "Dhulikhel"],
            "Gandaki": ["Pokhara", "Damauli", "Gorkha", "Waling", "Syangja", "Baglung", "Besisahar"],
            "Lumbini": ["Butwal", "Bhairahawa", "Nepalgunj", "Tulsipur", "Ghorahi", "Tansen", "Kapilvastu"],
            "Karnali": ["Birendranagar", "Jumla", "Dailekh", "Salyan", "Rukum", "Jajarkot", "Dolpa"],
            "Sudurpashchim": ["Dhangadhi", "Mahendranagar", "Tikapur", "Dadeldhura", "Dipayal", "Bajhang", "Bajura"]
        }
        
        cities = shipping_rates.get(province, [])
        
        return JsonResponse({
            'success': True,
            'cities': cities
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@require_POST
def calculate_shipping_ajax(request):
    """AJAX view to calculate shipping cost"""
    try:
        data = json.loads(request.body)
        province = data.get('province', '')
        city = data.get('city', '')
        
        shipping_cost = calculate_shipping_cost(province, city)
        
        # Get cart total
        cart_items = Cart.objects.filter(user=request.user)
        cart_total = sum(item.total_price() for item in cart_items)
        
        return JsonResponse({
            'success': True,
            'shipping_cost': shipping_cost,
            'total': float(cart_total) + shipping_cost
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

def calculate_shipping_cost(province, city):
    # Shipping rates dictionary
    shipping_rates = {
        "Province 1": {
            "Biratnagar":100, 
            "Dharan":100, 
            "Itahari":50, 
            "Damak":60, 
            "Birtamod" :150, 
            "Mechinagar":120, 
            "Urlabari":120,
            "default": 200
        },
        "Province 2": {
            "Janakpur": 200, 
            "Birgunj": 200, 
            "Simara": 200, 
            "Kalaiya": 200, 
            "Malangwa": 200, 
            "Jaleshwar": 200, 
            "Rajbiraj": 200,
            "default": 200
        },
        "Bagmati": {
            "Kathmandu": 200, 
            "Lalitpur": 200, 
            "Bhaktapur": 200, 
            "Hetauda": 200, 
            "Bharatpur": 200, 
            "Bidur": 200, 
            "Dhulikhel": 200,
            "default": 200
        },
        "Gandaki": {
            "Pokhara": 200, 
            "Damauli": 200, 
            "Gorkha": 200, 
            "Waling": 200, 
            "Syangja": 200, 
            "Baglung": 200, 
            "Besisahar": 200,
            "default": 200
        },
        "Lumbini": {
            "Butwal": 200, 
            "Bhairahawa": 200, 
            "Nepalgunj": 200, 
            "Tulsipur": 200, 
            "Ghorahi": 200, 
            "Tansen": 200, 
            "Kapilvastu": 200,
            "default": 200
        },
        "Karnali": {
            "Birendranagar": 200, 
            "Jumla": 200, 
            "Dailekh": 200, 
            "Salyan": 200, 
            "Rukum": 200, 
            "Jajarkot": 200, 
            "Dolpa": 200,
            "default": 200
        },
        "Sudurpashchim": {
            "Dhangadhi": 200, 
            "Mahendranagar": 200, 
            "Tikapur": 200, 
            "Dadeldhura": 200, 
            "Dipayal": 200, 
            "Bajhang": 200, 
            "Bajura": 200,
            "default": 200
        }
    }
    
    # Get province rates
    province_rates = shipping_rates.get(province, {})
    
    # Get city rate or default
    shipping_cost = province_rates.get(city, province_rates.get("default", 200))
    
    return shipping_cost

@login_required
def cart_order_history(request):
    """
    View to display all cart orders for the current logged-in user.
    Includes pagination and order statistics.
    """
    # Get all orders for the current user, ordered by most recent first
    user_orders = CartOrder.objects.filter(user=request.user).order_by('-created_at')
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(user_orders, 5)  # Show 5 orders per page
    
    try:
        orders = paginator.page(page)
    except PageNotAnInteger:
        orders = paginator.page(1)
    except EmptyPage:
        orders = paginator.page(paginator.num_pages)
    
    # Calculate order statistics
    total_orders = user_orders.count()
    pending_orders = user_orders.filter(status='Pending').count()
    shipped_orders = user_orders.filter(status='Shipped').count()
    delivered_orders = user_orders.filter(status='Delivered').count()
    
    context = {
        'orders': orders,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'shipped_orders': shipped_orders,
        'delivered_orders': delivered_orders,
        'page_obj': orders,  # For pagination template
    }
    
    return render(request, 'cart_order_history.html', context)

@login_required
def update_cart_order_status(request, order_id):
    """
    View to update the status of a cart order.
    Only staff members can update order status.
    """
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to update order status.")
        return redirect('cart_order_history')
    
    cart_order = get_object_or_404(CartOrder, id=order_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(CartOrder._meta.get_field('status').choices):
            cart_order.status = new_status
            cart_order.save()
            messages.success(request, f"Cart Order #{cart_order.id} status updated to {new_status}")
        else:
            messages.error(request, "Invalid status")
    
    return redirect('cart_order_history')

@login_required
def cancel_cart_order(request, order_id):
    """
    View to cancel a pending cart order.
    Users can only cancel their own orders that are in 'Pending' status.
    """
    cart_order = get_object_or_404(CartOrder, id=order_id)
    
    # Check if this is the user's order
    if cart_order.user != request.user:
        messages.error(request, "You can only cancel your own orders.")
        return redirect('cart_order_history')
    
    # Check if order is in Pending status
    if cart_order.status != 'Pending':
        messages.error(request, "Only pending orders can be cancelled.")
        return redirect('cart_order_history')
    
    if request.method == 'POST':
        cart_order.status = 'Cancelled'
        cart_order.save()
        messages.success(request, f"Cart Order #{cart_order.id} has been cancelled.")
    
    return redirect('cart_order_history')
# cart end>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

# order start>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


# def order(request, product_id):
#     chat_messages = ChatMessage.objects.all().order_by('timestamp')
#     product = get_object_or_404(Product, id=product_id)
    
#     if request.method == 'POST':
#         form = OrderForm(request.POST)
#         if form.is_valid():
#             order = form.save(commit=False)
#             order.product = product
            
#             # If user is authenticated, ensure we use their email
#             if request.user.is_authenticated:
#                 order.customer_email = request.user.email
            
#             # Calculate product total
#             order.total_price = product.price * order.quantity
            
#             # Calculate shipping cost based on location
#             province = form.cleaned_data.get('province')
#             city = form.cleaned_data.get('city')
            
#             # Get shipping cost from your shipping rates data
#             shipping_cost = calculate_shipping_cost(province, city)
#             order.shipping_cost = shipping_cost
#             order.total_price += shipping_cost
            
#             # Check if the current user was referred by someone
#             has_referrer = request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.referred_by is not None
#             referrer = request.user.profile.referred_by if has_referrer else None
            
#             # Get admin user to allocate commission if there's no referrer
#             admin_users = User.objects.filter(is_superuser=True).first()
            
#             # Get the product's commission amount
#             product_commission = product.commission
            
#             # If using wallet payment, check balance
#             if form.cleaned_data.get('payment_method') == 'wallet' and request.user.is_authenticated:
#                 if request.user.profile.wallet_balance < order.total_price:
#                     messages.error(request, 'Insufficient wallet balance for this order.')
#                     return redirect('order', product_id=product_id)
                
#                 # Deduct from wallet
#                 request.user.profile.wallet_balance -= order.total_price
#                 request.user.profile.save()
            
#             order.save()
            
#             # Handle the commission
#             if has_referrer:
#                 # Create a commission record for the referrer
#                 commission = ReferralCommission(
#                     referrer=referrer,
#                     referred_user=request.user,
#                     order=order,
#                     product=product,
#                     commission_amount=product_commission
#                 )
#                 commission.save()
                
#                 # Add the commission to the referrer's wallet
#                 referrer_profile = Profile.objects.get(user=referrer)
#                 referrer_profile.wallet_balance += product_commission
#                 referrer_profile.save()
                
#                 # Notify the referrer about the commission
#                 create_notification(
#                     user=referrer,
#                     notification_type='commission',
#                     title="Commission earned!",
#                     message=f"You earned ₹{product_commission} commission from {request.user.username}'s purchase of {product.name}",
#                     link="/profile/"
#                 )
#             elif admin_users:
#                 # If no referrer, commission goes to admin
#                 admin_profile = Profile.objects.get(user=admin_users)
#                 admin_profile.wallet_balance += product_commission
#                 admin_profile.save()
            
#             # Add shipping fee to admin wallet
#             if admin_users and shipping_cost > 0:
#                 admin_profile = Profile.objects.get(user=admin_users)
#                 admin_profile.wallet_balance += shipping_cost
#                 admin_profile.save()
                
#                 # Notify admin about the shipping commission
#                 create_notification(
#                     user=admin_users,
#                     notification_type='commission',
#                     title="Shipping fee received",
#                     message=f"You received ₹{shipping_cost} shipping fee from order #{order.id}",
#                     link="/admin_orders/"
#                 )
            
#             # Create purchase notification for buyer
#             if request.user.is_authenticated:
#                 create_notification(
#                     user=request.user,
#                     notification_type='order',
#                     title="Order placed successfully",
#                     message=f"Your order for {product.name} has been placed. Order #: {order.id}",
#                     link=f"/order_details/"
#                 )
                
#             # Create notification for seller about new order
#             create_notification(
#                 user=product.seller,
#                 notification_type='order',
#                 title="New order received",
#                 message=f"You've received a new order for {product.name}. Order #: {order.id}",
#                 link=f"/order_details/"
#             )
            
#             messages.success(request, 'Your order has been placed successfully!')
#             return redirect('order_confirmation', order_id=order.id)
#     else:
#         # Pre-fill form with user data if authenticated
#         initial_data = {}
#         if request.user.is_authenticated:
#             initial_data = {
#                 'customer_name': request.user.get_full_name() or request.user.username,
#                 'customer_email': request.user.email,
#             }
#             # Add phone if available in profile
#             if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'phone_number'):
#                 initial_data['customer_phone'] = request.user.profile.phone_number
        
#         form = OrderForm(initial=initial_data)
    
#     context = {
#         'product': product,
#         'form': form,
#         'chat_messages': chat_messages,
#     }
#     return render(request, 'order.html', context)

# def order(request, product_id):
#     chat_messages = ChatMessage.objects.all().order_by('timestamp')
#     product = get_object_or_404(Product, id=product_id)

#     if request.method == 'POST':
#         form = OrderForm(request.POST)
#         if form.is_valid():
#             order = form.save(commit=False)
#             order.product = product

#             if request.user.is_authenticated:
#                 order.customer_email = request.user.email

#             # Calculate product total
#             order.total_price = product.price * order.quantity

#             # Shipping cost
#             province = form.cleaned_data.get('province')
#             city = form.cleaned_data.get('city')
#             shipping_cost = calculate_shipping_cost(province, city)
#             order.shipping_cost = shipping_cost
#             order.total_price += shipping_cost

#             # Check referrer
#             has_referrer = request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.referred_by is not None
#             referrer = request.user.profile.referred_by if has_referrer else None

#             # Admin user fallback
#             admin_users = User.objects.filter(is_superuser=True).first()
#             product_commission = product.commission

#             # Wallet payment handling
#             if form.cleaned_data.get('payment_method') == 'wallet' and request.user.is_authenticated:
#                 if request.user.profile.wallet_balance < order.total_price:
#                     messages.error(request, 'Insufficient wallet balance for this order.')
#                     return redirect('order', product_id=product_id)
#                 request.user.profile.wallet_balance -= order.total_price
#                 request.user.profile.save()

#             order.save()

#             # ✅ Only give commission if referrer has shared this specific product
#             if has_referrer and ShareRecord.objects.filter(user=referrer, product=product).exists():
#                 # Give commission to referrer
#                 commission = ReferralCommission(
#                     referrer=referrer,
#                     referred_user=request.user,
#                     order=order,
#                     product=product,
#                     commission_amount=product_commission
#                 )
#                 commission.save()

#                 # Update referrer's wallet
#                 referrer_profile = Profile.objects.get(user=referrer)
#                 referrer_profile.wallet_balance += product_commission
#                 referrer_profile.save()

#                 # Notify referrer
#                 create_notification(
#                     user=referrer,
#                     notification_type='commission',
#                     title="Commission earned!",
#                     message=f"You earned ₹{product_commission} commission from {request.user.username}'s purchase of {product.name}",
#                     link="/profile/"
#                 )

#             elif admin_users:
#                 # No referrer or product not shared → commission to admin
#                 admin_profile = Profile.objects.get(user=admin_users)
#                 admin_profile.wallet_balance += product_commission
#                 admin_profile.save()

#             # Add shipping fee to admin wallet
#             if admin_users and shipping_cost > 0:
#                 admin_profile = Profile.objects.get(user=admin_users)
#                 admin_profile.wallet_balance += shipping_cost
#                 admin_profile.save()

#                 # Notify admin
#                 create_notification(
#                     user=admin_users,
#                     notification_type='commission',
#                     title="Shipping fee received",
#                     message=f"You received ₹{shipping_cost} shipping fee from order #{order.id}",
#                     link="/admin_orders/"
#                 )

#             # Notify buyer
#             if request.user.is_authenticated:
#                 create_notification(
#                     user=request.user,
#                     notification_type='order',
#                     title="Order placed successfully",
#                     message=f"Your order for {product.name} has been placed. Order #: {order.id}",
#                     link=f"/order_details/"
#                 )

#             # Notify seller
#             create_notification(
#                 user=product.seller,
#                 notification_type='order',
#                 title="New order received",
#                 message=f"You've received a new order for {product.name}. Order #: {order.id}",
#                 link=f"/order_details/"
#             )

#             messages.success(request, 'Your order has been placed successfully!')
#             return redirect('order_confirmation', order_id=order.id)

#     else:
#         initial_data = {}
#         if request.user.is_authenticated:
#             initial_data = {
#                 'customer_name': request.user.get_full_name() or request.user.username,
#                 'customer_email': request.user.email,
#             }
#             if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'phone_number'):
#                 initial_data['customer_phone'] = request.user.profile.phone_number

#         form = OrderForm(initial=initial_data)

#     context = {
#         'product': product,
#         'form': form,
#         'chat_messages': chat_messages,
#     }
#     return render(request, 'order.html', context)

def order(request, product_id):
    chat_messages = ChatMessage.objects.all().order_by('timestamp')
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.product = product

            if request.user.is_authenticated:
                order.customer_email = request.user.email

            # Calculate product total
            order.total_price = product.price * order.quantity

            # Shipping cost
            province = form.cleaned_data.get('province')
            city = form.cleaned_data.get('city')
            shipping_cost = calculate_shipping_cost(province, city)
            order.shipping_cost = shipping_cost
            order.total_price += shipping_cost

            # Check referrer
            has_referrer = request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.referred_by is not None
            referrer = request.user.profile.referred_by if has_referrer else None

            # Admin user fallback
            admin_users = User.objects.filter(is_superuser=True).first()
            product_commission = product.commission

            # Wallet payment handling
            if form.cleaned_data.get('payment_method') == 'wallet' and request.user.is_authenticated:
                if request.user.profile.wallet_balance < order.total_price:
                    messages.error(request, 'Insufficient wallet balance for this order.')
                    return redirect('order', product_id=product_id)
                request.user.profile.wallet_balance -= order.total_price
                request.user.profile.save()

            order.save()

            # ✅ Create commission record but DO NOT give money yet
            if has_referrer and ShareRecord.objects.filter(user=referrer, product=product).exists():
                ReferralCommission.objects.create(
                    referrer=referrer,
                    referred_user=request.user,
                    order=order,
                    product=product,
                    commission_amount=product_commission,
                    is_given=False  # Wait until delivery
                )

            elif admin_users:
                # Commission goes to admin → can handle similarly if needed
                admin_profile = Profile.objects.get(user=admin_users)
                admin_profile.wallet_balance += product_commission
                admin_profile.save()

            # Add shipping fee to admin wallet
            if admin_users and shipping_cost > 0:
                admin_profile = Profile.objects.get(user=admin_users)
                admin_profile.wallet_balance += shipping_cost
                admin_profile.save()

                # Notify admin
                create_notification(
                    user=admin_users,
                    notification_type='commission',
                    title="Shipping fee received",
                    message=f"You received ₹{shipping_cost} shipping fee from order #{order.id}",
                    link="/admin_orders/"
                )

            # Notify buyer
            if request.user.is_authenticated:
                create_notification(
                    user=request.user,
                    notification_type='order',
                    title="Order placed successfully",
                    message=f"Your order for {product.name} has been placed. Order #: {order.id}",
                    link=f"/order_details/"
                )

            # Notify seller
            create_notification(
                user=product.seller,
                notification_type='order',
                title="New order received",
                message=f"You've received a new order for {product.name}. Order #: {order.id}",
                link=f"/order_details/"
            )

            messages.success(request, 'Your order has been placed successfully!')
            return redirect('order_confirmation', order_id=order.id)

    else:
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'customer_name': request.user.get_full_name() or request.user.username,
                'customer_email': request.user.email,
            }
            if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'phone_number'):
                initial_data['customer_phone'] = request.user.profile.phone_number

        form = OrderForm(initial=initial_data)

    context = {
        'product': product,
        'form': form,
        'chat_messages': chat_messages,
    }
    return render(request, 'order.html', context)



# def give_commission_if_delivered(order):
#     commissions = ReferralCommission.objects.filter(order=order, is_given=False)
#     for commission in commissions:
#         referrer_profile = commission.referrer.profile
#         referrer_profile.wallet_balance += commission.commission_amount
#         referrer_profile.save()

#         commission.is_given = True
#         commission.save()

#         create_notification(
#             user=commission.referrer,
#             notification_type='commission',
#             title="Commission earned!",
#             message=f"You earned ₹{commission.commission_amount} commission from {commission.referred_user.username}'s purchase of {commission.product.name}",
#             link="/profile/"
#         )
        
def calculate_shipping_cost(province, city):
    # Shipping rates dictionary (same as in the JavaScript)
    shipping_rates = {
        
        "Province 1": {
            "Biratnagar":100, 
            "Dharan":100, 
            "Itahari":50, 
            "Damak":60, 
            "Birtamod" :150, 
            "Mechinagar":120, 
            "Urlabari":120,
            "default": 200
        },
        "Province 2": {
            "Janakpur": 200, 
            "Birgunj": 200, 
            "Simara": 200, 
            "Kalaiya": 200, 
            "Malangwa": 200, 
            "Jaleshwar": 200, 
            "Rajbiraj": 200,
            "default": 200
        },
        "Bagmati": {
            "Kathmandu": 200, 
            "Lalitpur": 200, 
            "Bhaktapur": 200, 
            "Hetauda": 200, 
            "Bharatpur": 200, 
            "Bidur": 200, 
            "Dhulikhel": 200,
            "default": 200
            
        },
        "Gandaki": {
            "Pokhara": 200, 
            "Damauli": 200, 
            "Gorkha": 200, 
            "Waling": 200, 
            "Syangja": 200, 
            "Baglung": 200, 
            "Besisahar": 200,
            "default": 200
        },
        "Lumbini": {
            "Butwal": 200, 
            "Bhairahawa": 200, 
            "Nepalgunj": 200, 
            "Tulsipur": 200, 
            "Ghorahi": 200, 
            "Tansen": 200, 
            "Kapilvastu": 200,
            "default": 200
        },
        "Karnali": {
            "Birendranagar": 200, 
            "Jumla": 200, 
            "Dailekh": 200, 
            "Salyan": 200, 
            "Rukum": 200, 
            "Jajarkot": 200, 
            "Dolpa": 200,
            "default": 200
        },
        "Sudurpashchim": {
            "Dhangadhi": 200, 
            "Mahendranagar": 200, 
            "Tikapur": 200, 
            "Dadeldhura": 200, 
            "Dipayal": 200, 
            "Bajhang": 200, 
            "Bajura": 200,
            "default": 200
            }
        }


    
    # Get province rates
    province_rates = shipping_rates.get(province, {})
    
    # Get city rate or default
    shipping_cost = province_rates.get(city, province_rates.get("default", 200))
    
    return shipping_cost

def order_details(request):
    chat_messages = ChatMessage.objects.all().order_by('timestamp')
    # Get all orders for the current user, ordered by most recent first
    user_orders = Order.objects.filter(customer_email=request.user.email).order_by('-created_at')
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(user_orders, 100000)  # Show 5 orders per page
    
    try:
        orders = paginator.page(page)
    except PageNotAnInteger:
        orders = paginator.page(1)
    except EmptyPage:
        orders = paginator.page(paginator.num_pages)
    
    # Calculate order statistics
    total_orders = user_orders.count()
    pending_orders = user_orders.filter(status='pending').count()
    shipped_orders = user_orders.filter(status='shipped').count()
    delivered_orders = user_orders.filter(status='delivered').count()
    # shipped_orders = user_orders.filter(status='shipped').count()
    print(f"Total Orders: {total_orders}")
    print(f"Pending Orders: {pending_orders}")
    print(f"Shipped Orders: {shipped_orders}")
    print(f"Delivered Orders: {delivered_orders}")
    # Filter only pending orders for counting in the template
    pending_orders_list = user_orders.filter(status="Pending")

    context = {
        'chat_messages':chat_messages,
        'orders': orders,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'shipped_orders': shipped_orders,
        'delivered_orders': delivered_orders,
        'pending_orders_list': pending_orders_list,  # Pass the filtered pending orders
        'page_obj': orders,  # For pagination template
    }
    
    return render(request, 'order_details.html', context)


@login_required
def update_order_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        
        # Check if the user is authorized (either a coadmin or the customer)
        if request.user.is_superuser or (hasattr(request.user, 'coadmin_profile')) or order.customer_email == request.user.email:
            new_status = request.POST.get('status')
            old_status = order.status  # Store the old status for comparison
            
            # Update the order status
            order.status = new_status
            order.save()
            
            # Get all users with this order (by email)
            users_with_order = User.objects.filter(email=order.customer_email)
            
            # Create a notification for each user
            for user in users_with_order:
                # Create different messages based on the status change
                if new_status == 'processing':
                    title = "Your order is being processed"
                    message = f"Order #{order.id} for {order.product.name} is now being processed. We're preparing your items for shipment and will update you when they're on the way."
                elif new_status == 'shipped':
                    title = "Your order has shipped!"
                    message = f"Great news! Order #{order.id} for {order.product.name} has been shipped and is on its way to you. You can expect delivery in the next few days."
                elif new_status == 'delivered':
                    title = "Your order has been delivered"
                    message = f"Order #{order.id} for {order.product.name} has been marked as delivered. We hope you enjoy your purchase! Don't forget to leave a review."
                elif new_status == 'cancelled':
                    title = "Your order has been cancelled"
                    message = f"Order #{order.id} for {order.product.name} has been cancelled. If you didn't request this cancellation, please contact customer support."
                else:
                    title = f"Order status updated to {new_status}"
                    message = f"Order #{order.id} for {order.product.name} has been updated to: {new_status}."
                
                # Create the notification
                create_notification(
                    user=user,
                    notification_type='order',
                    title=title,
                    message=message,
                    link=f"/order/{order.id}/"  # Link to the order details
                )
            
            messages.success(request, f"Order status updated to: {new_status}")
            
            if 'coadmin' in request.path:
                return redirect('coadmin_orders')
            return redirect('order_details')
        else:
            messages.error(request, "You are not authorized to update this order.")
            return redirect('order_details')
    
    return redirect('order_details')


@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    # Check if user is authorized to cancel this order
    if request.user.is_superuser or (hasattr(request.user, 'coadmin_profile')) or order.customer_email == request.user.email:
        # Check if the order is in a status that can be cancelled
        if order.status not in ['delivered', 'cancelled']:
            old_status = order.status
            order.status = 'cancelled'
            order.save()
            
            # Get all users with this order (by email)
            users_with_order = User.objects.filter(email=order.customer_email)
            
            # Create a notification for each user
            for user in users_with_order:
                create_notification(
                    user=user,
                    notification_type='order',
                    title="Your order has been cancelled",
                    message=f"Order #{order.id} for {order.product.name} has been cancelled. If you have any questions, please contact our customer service team.",
                    link=f"/order/{order.id}/"
                )
            
            # Also notify the seller
            create_notification(
                user=order.product.seller,
                notification_type='order',
                title="Order cancelled",
                message=f"Order #{order.id} for {order.product.name} has been cancelled by the customer or an administrator.",
                link=f"/order/{order.id}/"
            )
            
            messages.success(request, "Order has been cancelled successfully.")
        else:
            messages.error(request, "This order cannot be cancelled because it is already delivered or cancelled.")
    else:
        messages.error(request, "You are not authorized to cancel this order.")
    
    return redirect('order_details')
# order end  >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


# review start >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def submit_review(request, id):
    product = get_object_or_404(Product, id=id)

    if request.method == "POST":
        user_name = request.POST.get("user_name")
        rating = request.POST.get("rating")
        comment = request.POST.get("comment")

        # Validate inputs
        if not user_name or not rating or not comment:
            messages.error(request, "All fields are required!")
            return redirect('product_detail', id=product.id)

        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                messages.error(request, "Rating must be between 1 and 5.")
                return redirect('product_detail', id=product.id)
        except ValueError:
            messages.error(request, "Invalid rating value.")
            return redirect('product_detail', id=product.id)

        # Save review
        Review.objects.create(
            product=product,
            user_name=user_name,
            rating=rating,
            comment=comment
        )

        messages.success(request, "Review submitted successfully!")
        return redirect('product_detail', id=product.id)

    return redirect('product_detail', id=product.id)

# review ends >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>





def job_page(request):
    chat_messages = ChatMessage.objects.all().order_by('timestamp')
    context = {
        'chat_messages': chat_messages,
    }
    return render(request, 'job.html', context)
   



def home2(request):
    return render(request, 'home2.html')



def categories_view(request):
    chat_messages = ChatMessage.objects.all().order_by('timestamp')
    """
    View for displaying all categories and their related products.
    """
    # Get all categories with their products count
    categories = Category.objects.annotate(
        product_count=Count('products')
    ).order_by('name')
    
    # For each category, get available products
    for category in categories:
        # Limit to available products only
        category.available_products = category.products.filter(
            is_available=True
        ).order_by('-created_at')
    
    context = {
        'chat_messages': chat_messages,
        'categories': categories,
        'total_categories': categories.count(),
    }
    
    return render(request, 'categories.html', context)

def category_detail_view(request, category_id):
    """
    View for displaying a single category and all its products.
    """
    category = get_object_or_404(Category, id=category_id)
    
    # Get all available products for this category
    products = category.products.filter(is_available=True).order_by('-created_at')
    
    # Get related categories (optional)
    related_categories = Category.objects.exclude(id=category_id).annotate(
        product_count=Count('products')
    ).order_by('-product_count')[:4]
    
    context = {
        'category': category,
        'products': products,
        'related_categories': related_categories,
    }
    
    return render(request, 'category_detail.html', context)

def search_products(request):
    """
    View for searching products and categories.
    """
    query = request.GET.get('q', '')
    
    if query:
        # Search in products
        products = Product.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query),
            is_available=True
        ).order_by('-created_at')
        
        # Search in categories
        categories = Category.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query)
        ).annotate(product_count=Count('products')).order_by('name')
    else:
        products = Product.objects.filter(is_available=True).order_by('-created_at')[:8]
        categories = Category.objects.annotate(
            product_count=Count('products')
        ).order_by('name')
    
    context = {
        'query': query,
        'products': products,
        'categories': categories,
        'product_count': products.count(),
        'category_count': categories.count(),
    }
    
    return render(request, 'search_results.html', context)

def newsletter_signup(request):
    """
    View for handling newsletter signups.
    """
    if request.method == 'POST':
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        consent = request.POST.get('consent', False)
        
        # Here you would typically save this to your database
        # and perhaps integrate with an email marketing service
        
        # For now, just redirect back with a success message
        from django.contrib import messages
        messages.success(request, 'Thank you for subscribing to our newsletter!')
        
        # Redirect back to the referring page
        return redirect(request.META.get('HTTP_REFERER', 'categories'))
    
    # If not POST, redirect to categories page
    return redirect('categories')

def subscriber_details(request, subscriber_id):
    # Fetch the subscriber based on the given ID
    subscriber = NewsletterSubscriber.objects.get(id=subscriber_id)
    # Render a template with the subscriber details
    return render(request, 'subscriber_details.html', {'subscriber': subscriber})







def send_hello_email(request):
    user_email = 'user_email@example.com'  # Replace with the recipient's email
    subject = 'Hello!'
    message = 'Hello there, this is a simple hello message sent from Django.'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [user_email]

    try:
        send_mail(subject, message, email_from, recipient_list)
        print(f"Email sent to {user_email}")
        return render(request, 'email_sent.html')  # Redirect or render a success page
    except Exception as e:
        print(f"Error sending email: {e}")
        return render(request, 'error.html')

# for deals start>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def deals_list(request):
    chat_messages = ChatMessage.objects.all().order_by('timestamp')
    deals = Deal.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'deals/deals_list.html', {'deals': deals,'chat_messages': chat_messages})

def deal_detail(request, pk):
    deal = get_object_or_404(Deal, pk=pk, is_active=True)
    
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.deal = deal
            contact.save()
            messages.success(request, "Your message has been sent to the seller!")
            return redirect('deal_detail', pk=pk)
    else:
        form = ContactForm()
    
    return render(request, 'deals/deal_detail.html', {'deal': deal, 'form': form})

@login_required
def add_deal(request):
    if request.method == 'POST':
        form = DealForm(request.POST, request.FILES)
        if form.is_valid():
            deal = form.save(commit=False)
            deal.seller = request.user
            deal.save()
            messages.success(request, "Deal added successfully!")
            return redirect('deal_detail', pk=deal.pk)
    else:
        form = DealForm()
    
    return render(request, 'deals/add_deal.html', {'form': form})

@login_required
def edit_deal(request, pk):
    deal = get_object_or_404(Deal, pk=pk, seller=request.user)
    
    if request.method == 'POST':
        form = DealForm(request.POST, request.FILES, instance=deal)
        if form.is_valid():
            form.save()
            messages.success(request, "Deal updated successfully!")
            return redirect('deal_detail', pk=deal.pk)
    else:
        form = DealForm(instance=deal)
    
    return render(request, 'deals/edit_deal.html', {'form': form, 'deal': deal})

@login_required
def delete_deal(request, pk):
    """Delete a deal if the user is the seller"""
    deal = get_object_or_404(Deal, pk=pk)
    
    # Check if user is the seller or has permission to delete
    if request.user != deal.seller and not request.user.is_superuser and not is_coadmin(request.user):
        messages.error(request, "You don't have permission to delete this deal.")
        return redirect('deals')
    
    if request.method == 'POST':
        # Delete the deal
        deal_title = deal.title
        deal.delete()
        messages.success(request, f"Deal '{deal_title}' has been deleted successfully.")
        
        # Redirect based on user type
        if is_coadmin(request.user):
            return redirect('coadmin_deals')
        else:
            return redirect('deals')
    
    # If GET request, show confirmation page
    return render(request, 'deals/delete_deal_confirm.html', {'deal': deal})

# Deal Chat functionality
@login_required
def deal_chat(request, deal_id):
    """View to display chat interface for a specific deal"""
    deal = get_object_or_404(Deal, pk=deal_id, is_active=True)
    
    # Determine the other user (seller or buyer)
    if request.user == deal.seller:
        # If user is seller, get all users who have chatted with them about this deal
        chat_partners = User.objects.filter(
            sent_deal_messages__deal=deal, 
            sent_deal_messages__receiver=request.user
        ).distinct() | User.objects.filter(
            received_deal_messages__deal=deal,
            received_deal_messages__sender=request.user
        ).distinct()
        
        context = {
            'deal': deal,
            'chat_partners': chat_partners,
            'is_seller': True
        }
        return render(request, 'deals/deal_chat_seller.html', context)
    else:
        # If user is buyer, show chat with seller
        # Get or create a chat session with the seller
        messages = DealChatMessage.objects.filter(
            deal=deal
        ).filter(
            (Q(sender=request.user) & Q(receiver=deal.seller)) |
            (Q(sender=deal.seller) & Q(receiver=request.user))
        ).order_by('timestamp')
        
        # Mark messages as read
        unread_messages = messages.filter(receiver=request.user, is_read=False)
        unread_messages.update(is_read=True)
        
        context = {
            'deal': deal,
            'chat_messages': messages,
            'is_seller': False,
            'seller': deal.seller,
            'pusher_key': settings.PUSHER_KEY,
            'pusher_cluster': settings.PUSHER_CLUSTER
        }
        return render(request, 'deals/deal_chat.html', context)

@login_required
def deal_chat_with_user(request, deal_id, user_id):
    """View for sellers to chat with a specific user about a deal"""
    deal = get_object_or_404(Deal, pk=deal_id)
    other_user = get_object_or_404(User, pk=user_id)
    
    # Verify the current user is the seller of this deal
    if request.user != deal.seller:
        messages.error(request, "You don't have permission to access this chat.")
        return redirect('deal_detail', pk=deal_id)
    
    # Get messages between seller and this specific user
    chat_messages = DealChatMessage.objects.filter(
        deal=deal
    ).filter(
        (Q(sender=request.user) & Q(receiver=other_user)) |
        (Q(sender=other_user) & Q(receiver=request.user))
    ).order_by('timestamp')
    
    # Mark messages as read
    unread_messages = chat_messages.filter(receiver=request.user, is_read=False)
    unread_messages.update(is_read=True)
    
    context = {
        'deal': deal,
        'other_user': other_user,
        'chat_messages': chat_messages,
        'is_seller': True,
        'pusher_key': settings.PUSHER_KEY,
        'pusher_cluster': settings.PUSHER_CLUSTER
    }
    
    return render(request, 'deals/deal_chat_seller_with_user.html', context)

@csrf_exempt
@login_required
def send_deal_message(request):
    """API to send a message in a deal chat"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            deal_id = data.get('deal_id')
            receiver_id = data.get('receiver_id')
            message_text = data.get('message', '').strip()
            
            if not all([deal_id, receiver_id, message_text]):
                return JsonResponse({'status': 'error', 'message': 'Missing required fields'}, status=400)
            
            # Get deal and receiver
            deal = get_object_or_404(Deal, pk=deal_id)
            receiver = get_object_or_404(User, pk=receiver_id)
            
            # Verify permissions (either sender is the seller, or receiver is the seller)
            if request.user != deal.seller and receiver != deal.seller:
                return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
            
            # Create the message
            chat_message = DealChatMessage.objects.create(
                deal=deal,
                sender=request.user,
                receiver=receiver,
                message=message_text
            )
            
            # Format message for response
            response_data = {
                'status': 'success',
                'message_id': chat_message.id,
                'sender': request.user.username,
                'message': message_text,
                'timestamp': chat_message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Send message through Pusher for real-time updates
            channel_name = f'deal_chat_{deal_id}_{min(request.user.id, receiver.id)}_{max(request.user.id, receiver.id)}'
            pusher_client.trigger(channel_name, 'message', response_data)
            
            return JsonResponse(response_data)
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON format'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Only POST method is allowed'}, status=405)

@login_required
def check_new_deal_messages(request):
    """API to check for new unread messages in deal chats"""
    user = request.user
    
    # Count unread messages
    unread_count = DealChatMessage.objects.filter(receiver=user, is_read=False).count()
    
    # Get deal IDs with unread messages
    deals_with_unread = DealChatMessage.objects.filter(
        receiver=user, 
        is_read=False
    ).values_list('deal_id', flat=True).distinct()
    
    # Get sender IDs with unread messages
    senders_with_unread = DealChatMessage.objects.filter(
        receiver=user, 
        is_read=False
    ).values_list('sender_id', flat=True).distinct()
    
    return JsonResponse({
        'unread_count': unread_count,
        'deals_with_unread': list(deals_with_unread),
        'senders_with_unread': list(senders_with_unread)
    })


# for seller account start>>>>>>>>>>>>>>>
def seller_dashboard(request):
    chat_messages = ChatMessage.objects.all().order_by('timestamp')
    
    products = Product.objects.filter(seller=request.user)  # Only show products of logged-in seller
    orders = Order.objects.filter(product__seller=request.user)  # Orders for seller's products
    wallet_balance = sum(order.total_price for order in orders if order.status == "Delivered")
    revenue = sum(product.price * product.sold for product in products)

    return render(request, "seller_dashboard.html", {
        "products": products,
        "orders": orders,
        "wallet_balance": wallet_balance,
        "revenue": revenue,
        "chat_messages":chat_messages
    })
def edit_product(request, product_id):
    # Get the product
    product = get_object_or_404(Product, id=product_id)
    
    # Check if the current user is authorized to edit this product
    # This will depend on how you're associating products with sellers
    try:
        seller = request.user.seller
        if product not in seller.products.all():
            messages.error(request, "You don't have permission to edit this product")
            return redirect('seller_dashboard')
    except AttributeError:
        # If there's no way to verify ownership, you might need additional logic
        # or rely on your application's authorization system
        pass
    
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
        return redirect('seller_dashboard')
    
    context = {
        'product': product,
        'categories': Category.objects.all(),
        'pending_orders_count': Order.objects.filter(status='Pending').count(),
    }
    
    return render(request, 'edit_product.html', context)


def hi(request):
    
    return render(request, 'hi.html')


def toggle_wishlist(request, product_id):
    user = request.user
    product = Product.objects.get(id=product_id)

    if request.method == 'POST':
        # Check if the product is already in the wishlist
        liked_product, created = LikedProduct.objects.get_or_create(user=user, product=product)
        if not created:
            liked_product.delete()  # Remove from wishlist if already liked
            return JsonResponse({'status': 'removed', 'message': 'Product removed from wishlist.'})
        return JsonResponse({'status': 'added', 'message': 'Product added to wishlist.'})

    # Render the template (GET request or direct access)
    liked_products = LikedProduct.objects.filter(user=user).values_list('product_id', flat=True)
    context = {
        'liked_products': liked_products,
    }
    return render(request, 'product.html', context)



# for coadmin>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.>>>>>>>>>>>
def is_coadmin(user):
    try:
        # Check if the user has show_request_manager_btn enabled in their profile
        profile = user.profile
        return profile.show_request_manager_btn
    except Profile.DoesNotExist:
        return False

@user_passes_test(is_coadmin)
def coadmin_page(request):
    # Get current date for calculations
    today = timezone.now().date()
    thirty_days_ago = today - timezone.timedelta(days=30)
    prev_thirty_days = thirty_days_ago - timezone.timedelta(days=30)
    
    # Get order stats with growth calculation
    current_orders = Order.objects.filter(created_at__date__gte=thirty_days_ago).count()
    previous_orders = Order.objects.filter(created_at__date__gte=prev_thirty_days, created_at__date__lt=thirty_days_ago).count()
    order_growth = 0
    if previous_orders > 0:
        order_growth = round(((current_orders - previous_orders) / previous_orders) * 100)
    
    # Get revenue stats with growth calculation
    current_revenue = Order.objects.filter(created_at__date__gte=thirty_days_ago).aggregate(Sum('total_price'))['total_price__sum'] or 0
    previous_revenue = Order.objects.filter(created_at__date__gte=prev_thirty_days, created_at__date__lt=thirty_days_ago).aggregate(Sum('total_price'))['total_price__sum'] or 0
    revenue_growth = 0
    if previous_revenue > 0:
        revenue_growth = round(((current_revenue - previous_revenue) / previous_revenue) * 100)
    
    # Get order counts by status
    total_orders = Order.objects.all().count()
    pending_orders = Order.objects.filter(status='pending').count()
    processing_orders = Order.objects.filter(status='processing').count()
    shipped_orders = Order.objects.filter(status='shipped').count()
    delivered_orders = Order.objects.filter(status='delivered').count()
    cancelled_orders = Order.objects.filter(status='cancelled').count()
    
    # Get product and deal counts
    total_products = Product.objects.all().count()
    total_deals = Deal.objects.all().count()
    active_deals = Deal.objects.filter(is_active=True).count()
    
    # Get low stock products (5 or fewer)
    low_stock_products = Product.objects.filter(stock__lte=5)
    
    # Check if Deal model has start_date and end_date fields
    deal_has_date_fields = hasattr(Deal, 'start_date') and hasattr(Deal, 'end_date')
    
    # Get expiring deals (within next 7 days) if date fields exist
    expiring_deals = []
    if deal_has_date_fields:
        next_week = today + timezone.timedelta(days=7)
        expiring_deals = Deal.objects.filter(end_date__range=[today, next_week])
    
    # Get total revenue
    total_revenue = Order.objects.filter(status__in=['delivered', 'shipped']).aggregate(Sum('total_price'))['total_price__sum'] or 0
    
    # Get recent orders
    recent_orders = Order.objects.all().order_by('-created_at')[:5]
    
    # Get best selling products
    best_selling_products = Product.objects.annotate(
        sales_count=Count('order')
    ).order_by('-sales_count')[:5]
    
    # Get unread messages count
    unread_deal_messages = DealChatMessage.objects.filter(
        receiver=request.user,
        is_read=False
    ).count()
    
    # Generate chart data for last 7 days
    chart_labels = []
    chart_orders = []
    chart_revenue = []
    
    for i in range(6, -1, -1):
        day = today - timezone.timedelta(days=i)
        chart_labels.append(day.strftime('%a'))
        
        # Count orders for this day
        day_orders = Order.objects.filter(created_at__date=day).count()
        chart_orders.append(day_orders)
        
        # Sum revenue for this day
        day_revenue = Order.objects.filter(created_at__date=day).aggregate(Sum('total_price'))['total_price__sum'] or 0
        chart_revenue.append(float(day_revenue))
    
    return render(request, 'coadmin_page.html', {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'processing_orders': processing_orders,
        'shipped_orders': shipped_orders,
        'delivered_orders': delivered_orders,
        'cancelled_orders': cancelled_orders,
        
        'total_products': total_products,
        'low_stock_products': low_stock_products,
        
        'total_deals': total_deals,
        'active_deals': active_deals,
        'expiring_deals': expiring_deals,
        
        'total_revenue': total_revenue,
        'revenue_growth': revenue_growth,
        'order_growth': order_growth,
        
        'recent_orders': recent_orders,
        'best_selling_products': best_selling_products,
        'unread_deal_messages': unread_deal_messages,
        
        'chart_labels': json.dumps(chart_labels),
        'chart_orders': json.dumps(chart_orders),
        'chart_revenue': json.dumps(chart_revenue),
        
        'now': timezone.now(),
    })


    
def coadmin_form(request):
    # Check if user already has a coadmin profile
    if hasattr(request.user, 'coadmin_profile'):
        messages.error(request, 'You already have a co-admin profile.')
        return redirect('dashboard')  # Redirect to appropriate page
        
    if request.method == 'POST':
        form = CoAdminRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            # Don't save the form immediately
            coadmin = form.save(commit=False)
            
            # Associate the current logged-in user with the coadmin
            coadmin.user = request.user
            
            # Now save the coadmin
            coadmin.save()
            
            # Add success message
            messages.success(request, 'Co-admin registration successful!')
            
            # Redirect to success page
            return redirect('home')  # Replace with your success URL
    else:
        # Pre-fill form with user data
        initial_data = {
            'name': f"{request.user.first_name} {request.user.last_name}".strip(),
            'email': request.user.email,
        }
        form = CoAdminRegistrationForm(initial=initial_data)
    
    return render(request, 'coadmin_form.html', {'form': form})


# ends for coadmin>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.>>>>>>>>>>>

# Additional coadmin dashboard views
@user_passes_test(is_coadmin)
def coadmin_orders(request):
    """View for coadmin to manage all orders"""
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('q', '')
    
    # Start with all orders
    orders = Order.objects.all().order_by('-created_at')
    
    # Apply status filter if provided
    if status_filter and status_filter != 'all':
        orders = orders.filter(status=status_filter)
    
    # Apply search filter if provided
    if search_query:
        orders = orders.filter(
            Q(customer_name__icontains=search_query) | 
            Q(customer_email__icontains=search_query) |
            Q(product__name__icontains=search_query) |
            Q(id__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(orders, 20)  # 20 orders per page
    page_number = request.GET.get('page')
    orders_page = paginator.get_page(page_number)
    
    # Get order statistics
    order_stats = {
        'total': Order.objects.count(),
        'pending': Order.objects.filter(status='pending').count(),
        'processing': Order.objects.filter(status='processing').count(),
        'shipped': Order.objects.filter(status='shipped').count(),
        'delivered': Order.objects.filter(status='delivered').count(),
        'cancelled': Order.objects.filter(status='cancelled').count(),
    }
    
    context = {
        'orders': orders_page,
        'stats': order_stats,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'coadmin_orders.html', context)

@user_passes_test(is_coadmin)
def coadmin_products(request):
    """View for coadmin to manage products"""
    # Get filter parameters
    category_id = request.GET.get('category', '')
    search_query = request.GET.get('q', '')
    stock_filter = request.GET.get('stock', '')
    
    # Start with all products
    products = Product.objects.all().order_by('-created_at')
    
    # Apply category filter if provided
    if category_id:
        products = products.filter(category_id=category_id)
    
    # Apply search filter if provided
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # Apply stock filter if provided
    if stock_filter == 'low':
        products = products.filter(stock__lt=10, is_available=True)
    elif stock_filter == 'out':
        products = products.filter(stock=0)
    
    # Pagination
    paginator = Paginator(products, 20)  # 20 products per page
    page_number = request.GET.get('page')
    products_page = paginator.get_page(page_number)
    
    # Get product statistics
    product_stats = {
        'total': Product.objects.count(),
        'available': Product.objects.filter(is_available=True).count(),
        'unavailable': Product.objects.filter(is_available=False).count(),
        'low_stock': Product.objects.filter(stock__lt=10, is_available=True).count(),
        'out_of_stock': Product.objects.filter(stock=0).count(),
    }
    
    # Get all categories for filter dropdown
    categories = Category.objects.all()
    
    context = {
        'products': products_page,
        'stats': product_stats,
        'categories': categories,
        'category_id': category_id,
        'search_query': search_query,
        'stock_filter': stock_filter,
    }
    
    return render(request, 'coadmin_products.html', context)

@user_passes_test(is_coadmin)
def coadmin_deals(request):
    """View for coadmin to manage wholesale deals"""
    # Get filter parameters
    search_query = request.GET.get('q', '')
    active_only = request.GET.get('active', 'true') == 'true'
    
    # Start with all deals
    deals = Deal.objects.all().order_by('-created_at')
    
    # Apply active filter
    if active_only:
        deals = deals.filter(is_active=True)
    
    # Apply search filter if provided
    if search_query:
        deals = deals.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(seller__username__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(deals, 20)  # 20 deals per page
    page_number = request.GET.get('page')
    deals_page = paginator.get_page(page_number)
    
    # Get deal statistics
    deal_stats = {
        'total': Deal.objects.count(),
        'active': Deal.objects.filter(is_active=True).count(),
        'inactive': Deal.objects.filter(is_active=False).count(),
    }
    
    context = {
        'deals': deals_page,
        'stats': deal_stats,
        'search_query': search_query,
        'active_only': active_only,
    }
    
    return render(request, 'coadmin_deals.html', context)

@user_passes_test(is_coadmin)
def coadmin_messages(request):
    """View for coadmin to manage and monitor all chat messages"""
    # Get filter parameters
    search_query = request.GET.get('q', '')
    unread_only = request.GET.get('unread', 'false') == 'true'
    
    # Get deal messages (private chats)
    deal_messages = DealChatMessage.objects.all().order_by('-timestamp')
    
    # Apply unread filter if requested
    if unread_only:
        deal_messages = deal_messages.filter(is_read=False, receiver=request.user)
    
    # Apply search filter if provided
    if search_query:
        deal_messages = deal_messages.filter(
            Q(message__icontains=search_query) | 
            Q(sender__username__icontains=search_query) |
            Q(receiver__username__icontains=search_query) |
            Q(deal__title__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(deal_messages, 30)  # 30 messages per page
    page_number = request.GET.get('page')
    messages_page = paginator.get_page(page_number)
    
    # Get message statistics
    message_stats = {
        'total_deal_messages': DealChatMessage.objects.count(),
        'unread_deal_messages': DealChatMessage.objects.filter(is_read=False, receiver=request.user).count(),
    }
    
    context = {
        'messages': messages_page,
        'stats': message_stats,
        'search_query': search_query,
        'unread_only': unread_only,
    }
    
    return render(request, 'coadmin_messages.html', context)

@user_passes_test(is_coadmin)
def accept_order(request, order_id):
    """API endpoint for coadmin to accept and process an order"""
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        
        # Update order status to processing
        if order.status == 'pending':
            order.status = 'processing'
            order.save()
            
            # Notify the customer
            customer_users = User.objects.filter(email=order.customer_email)
            for user in customer_users:
                create_notification(
                    user=user,
                    notification_type='order',
                    title="Your order has been accepted",
                    message=f"Good news! Order #{order.id} for {order.product.name} has been accepted and is now being processed.",
                    link=f"/order/{order.id}/"
                )
            
            # Notify the seller
            create_notification(
                user=order.product.seller,
                notification_type='order',
                title="Order accepted",
                message=f"Order #{order.id} for {order.product.name} has been accepted and marked as processing.",
                link=f"/order/{order.id}/"
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Order #{order_id} has been accepted and is now being processed.'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': f'Order #{order_id} cannot be accepted. Current status: {order.status}.'
            }, status=400)
            
    return JsonResponse({
        'success': False,
        'message': 'Only POST method is allowed.'
    }, status=405)

@user_passes_test(is_coadmin)
def mark_messages_read(request):
    if request.method == 'POST':
        message_ids = json.loads(request.body).get('message_ids', [])
        
        if message_ids:
            # Update messages in bulk
            DealChatMessage.objects.filter(id__in=message_ids, receiver=request.user, is_read=False).update(is_read=True)
            return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error'}, status=400)

# Notification functions
@login_required
def notifications_list(request):
    chat_messages = ChatMessage.objects.all().order_by('timestamp')
    """View to display all notifications for the current user"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Paginate notifications if there are many
    paginator = Paginator(notifications, 10)  # Show 10 notifications per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get other context data for navbar
    if request.user.is_authenticated:
        cart_items = Cart.objects.filter(user=request.user)
        cart_count = cart_items.count()
        unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()
    else:
        cart_items = []
        cart_count = 0
        unread_notifications = 0
    
    context = {
        'notifications': page_obj,
        'cart_items': cart_items,
        'cart_count': cart_count,
        'unread_notifications': unread_notifications,
        'chat_messages': chat_messages,
    }
    
    return render(request, 'notifications.html', context)

@login_required
def mark_notification_read(request, notification_id):
    """Mark a specific notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    
    # If Ajax request
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    # If normal request, redirect to the notification's link or back to notifications list
    if notification.link:
        return redirect(notification.link)
    return redirect('notifications_list')

@login_required
def mark_all_notifications_read(request):
    """Mark all notifications for the current user as read"""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    
    # If Ajax request
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    return redirect('notifications_list')

def create_notification(user, notification_type, title, message, link=None):
    """Helper function to create a notification"""
    notification = Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        link=link
    )
    return notification

# Add this function at the end of your views.py file
def get_unread_notifications_count(request):
    """API endpoint to get the number of unread notifications"""
    if request.user.is_authenticated:
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return JsonResponse({'count': count})
    return JsonResponse({'count': 0})

# API endpoint to get notifications in JSON format
@login_required
def get_notifications_api(request):
    """API endpoint to get notifications in JSON format for the dropdown"""
    limit = request.GET.get('limit', 5)
    try:
        limit = int(limit)
    except ValueError:
        limit = 5
    
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:limit]
    
    # Convert to JSON-serializable format
    notifications_data = []
    for notification in notifications:
        notifications_data.append({
            'id': notification.id,
            'notification_type': notification.notification_type,
            'title': notification.title,
            'message': notification.message,
            'link': notification.link,
            'is_read': notification.is_read,
            'created_at': notification.created_at.isoformat(),
        })
    
    return JsonResponse({'notifications': notifications_data})

@login_required
def request_withdrawal(request):
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount', 0))
        notes = request.POST.get('notes', '')
        
        # Validate if amount is positive and not zero
        if amount <= 0:
            messages.error(request, 'Withdrawal amount must be greater than zero.')
            return redirect('withdrawal_history')
        
        # Check if user has sufficient balance
        if amount > request.user.profile.wallet_balance:
            messages.error(request, 'Insufficient wallet balance for this withdrawal.')
            return redirect('withdrawal_history')
        
        # Handle image upload
        proof_image = None
        if request.FILES.get('proof_image'):
            proof_image = request.FILES['proof_image']
        
        # Create withdrawal request
        withdrawal = WalletWithdrawal.objects.create(
            user=request.user,
            amount=amount,
            notes=notes,
            proof_image=proof_image
        )
        
        # Create notification for admin
        Notification.objects.create(
            user=User.objects.filter(is_superuser=True).first(),  # To the admin
            notification_type='system',
            title='New Withdrawal Request',
            message=f'{request.user.username} has requested a withdrawal of Rs {amount}',
            link='/admin/Accounts/walletwithdrawal/'
        )
        
        messages.success(request, 'Your withdrawal request has been submitted successfully.')
        return redirect('withdrawal_history')
    
    return render(request, 'request_withdrawal.html', {
        'wallet_balance': request.user.profile.wallet_balance
    })

@login_required
def withdrawal_history(request):
    withdrawals = WalletWithdrawal.objects.filter(user=request.user).order_by('-created_at')
    
    return render(request, 'withdrawal_history.html', {
        'withdrawals': withdrawals,
        'wallet_balance': request.user.profile.wallet_balance
    })

@login_required
def cancel_withdrawal(request, withdrawal_id):
    withdrawal = get_object_or_404(WalletWithdrawal, id=withdrawal_id, user=request.user)
    
    if withdrawal.status != 'pending':
        messages.error(request, 'Only pending withdrawal requests can be canceled.')
        return redirect('withdrawal_history')
    
    withdrawal.delete()
    messages.success(request, 'Your withdrawal request has been canceled successfully.')
    return redirect('withdrawal_history')

# Admin view for managing withdrawal requests
@login_required
@user_passes_test(lambda u: u.is_staff or hasattr(u, 'coadmin_profile'))
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
    
    return render(request, 'coadmin_withdrawals.html', {
        'withdrawals': withdrawals,
        'pending_count': pending_count,
        'status_filter': status_filter,
        'search_query': search_query
    })

@login_required
@user_passes_test(lambda u: u.is_staff or hasattr(u, 'coadmin_profile'))
def process_withdrawal(request, withdrawal_id):
    withdrawal = get_object_or_404(WalletWithdrawal, id=withdrawal_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        admin_notes = request.POST.get('admin_notes', '')
        
        if action == 'approve':
            # Check if user still has sufficient balance
            if withdrawal.amount > withdrawal.user.profile.wallet_balance:
                messages.error(request, f'User has insufficient balance. Current balance: Rs {withdrawal.user.profile.wallet_balance}')
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
                message=f'Your withdrawal request for Rs {withdrawal.amount} has been approved.',
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
                message=f'Your withdrawal request for Rs {withdrawal.amount} has been rejected.',
                link='/withdrawal-history/'
            )
            
            messages.success(request, f'Withdrawal request for {withdrawal.user.username} has been rejected.')
        
        return redirect('admin_withdrawals')
    
    return render(request, 'process_withdrawal.html', {
        'withdrawal': withdrawal
    })

@login_required
def record_share(request):
    """Record a share action"""
    if request.method == 'POST':
        platform = request.POST.get('platform')
        product_id = request.POST.get('product_id')
        
        if platform in dict(ShareRecord.PLATFORM_CHOICES):
            try:
                product = Product.objects.get(id=product_id) if product_id else None
            except Product.DoesNotExist:
                product = None
                
            share = ShareRecord(
                user=request.user,
                platform=platform,
                product=product,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
            share.save()
            
            # Get updated stats
            stats = ShareRecord.get_share_stats(request.user)
            return JsonResponse({
                'success': True,
                'stats': stats
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

@login_required
def get_share_stats(request):
    """Get share statistics for the current user"""
    stats = ShareRecord.get_share_stats(request.user)
    return JsonResponse(stats)
    
    
    
    