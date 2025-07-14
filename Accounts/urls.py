from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from . import views
from . import admin_views
from .views import create_superuser_view

# Custom error handlers
def custom_404_view(request, exception):
    """Custom 404 error handler"""
    return render(request, 'errors/404.html', status=404)

def custom_500_view(request):
    """Custom 500 error handler"""
    return render(request, 'errors/500.html', status=500)

def custom_403_view(request, exception):
    """Custom 403 error handler"""
    return render(request, 'errors/403.html', status=403)

def custom_400_view(request, exception):
    """Custom 400 error handler"""
    return render(request, 'errors/400.html', status=400)

urlpatterns = [
    path('create-superuser/', create_superuser_view),
    # Basic pages
    path('', views.safe_home, name='home'),
    path('login/', views.safe_login_attempt, name='login_attempt'), 
    path('register/', views.safe_register_attempt, name='register_attempt'),
    
    # Referral system
    path('refer/<str:referral_code>/', views.safe_register_attempt, name='register_with_referral'),    
    
    # Authentication
    path('token', views.safe_token_send, name='token_send'),
    path('success', views.safe_success, name='success'),
    path('verify/<auth_token>', views.safe_verify, name='verify'),
    path('error', views.safe_error_page, name='error'),
    path('dashboard/', views.safe_dashboard, name='dashboard'),
    path('logout', views.safe_logout_attempt, name='logout_attempt'),
    path('change_password', views.safe_change_password, name='change_password'),
    path('profile/', views.safe_profile, name='profile'),
    path('accounts/', include('allauth.urls')),
    
    # Deals
    path('deals', views.safe_deals_list, name='deals'),
    path('deal_list/<int:pk>/', views.safe_deal_detail, name='deal_detail'),
    path('add_deal/', views.safe_add_deal, name='add_deal'),
    path('<int:pk>/edit/', views.safe_edit_deal, name='edit_deal'),
    path('deal/<int:pk>/delete/', views.safe_delete_deal, name='delete_deal'),

    # Products
    path('add-product/', views.safe_add_product, name='add_product'),
    path('product/', views.safe_product, name='product'),
    path('product/<int:id>/', views.safe_product_detail, name='product_detail'),
    path('product/<int:id>/review/', views.safe_submit_review, name='submit_review'),
    path('product/<int:id>/delete/', views.safe_delete_product, name='delete_product'),
    
    # Chat
    path('chat/', views.safe_chat_room, name='chat_room'),
    path('send_message/', views.safe_send_message, name='send_message'),
    
    # Cart
    path('cart/', views.safe_cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.safe_add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:cart_id>/', views.safe_remove_from_cart, name='remove_from_cart'),
    path('add-to-cart/<int:product_id>/', views.safe_add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:cart_id>/', views.safe_remove_from_cart, name='remove_from_cart'),
    path('update_cart/<int:item_id>/', views.safe_update_cart, name='update_cart'),
    path('remove_from_cart/<int:item_id>/', views.safe_remove_from_cart_ajax, name='remove_from_cart_ajax'),
    path('clear_cart/', views.safe_clear_cart, name='clear_cart'),
    
    # Cart checkout and orders
    path('cart-orders/', views.safe_cart_order_history, name='cart_order_history'),
    path('update-cart-order-status/<int:order_id>/', views.safe_update_cart_order_status, name='update_cart_order_status'),
    path('cancel-cart-order/<int:order_id>/', views.safe_cancel_cart_order, name='cancel_cart_order'),
    path('cart/checkout/', views.safe_cart_checkout, name='cart_checkout'),
    path('cart/confirmation/<int:order_id>/', views.safe_cart_order_confirmation, name='cart_order_confirmation'),
    path('cart/confirmation/<int:order_id>/', views.safe_cart_order_confirmation, name='order_confirmation'),
    
    # AJAX endpoints
    path('get-cities/', views.safe_get_cities, name='get_cities'),
    path('calculate-shipping/', views.safe_calculate_shipping_ajax, name='calculate_shipping'),
    
    # Orders
    path('order/<int:product_id>/', views.safe_order, name='order'),
    path('order_details/', views.safe_order_details, name='order_details'),
    path('order/<int:order_id>/update-status/', views.safe_update_order_status, name='update_order_status'),
    path('order/<int:order_id>/cancel/', views.safe_cancel_order, name='cancel_order'),
    path('calculate_shipping_ajax/', views.safe_calculate_shipping_ajax, name='calculate_shipping_ajax'),
    
    # Other pages
    path('job/', views.safe_job_page, name='job'),
    path('hi/', views.safe_hi, name='hi'),
    path('home2/', views.safe_home2, name='home2'),
    path('resend-verification/', views.safe_resend_verification, name='resend_verification'),

    # Categories
    path('categories/', views.safe_categories_view, name='categories'),
    path('category/<int:category_id>/', views.safe_category_detail_view, name='category_detail'),
    
    # Search and newsletter
    path('search/', views.safe_search_products, name='search_products'),
    path('newsletter-signup/', views.safe_newsletter_signup, name='newsletter_signup'),    
    path('send_hello_email/', views.safe_send_hello_email, name='send_hello_email'),
    
    # Seller dashboard
    path('seller/', views.safe_seller_dashboard, name='seller_dashboard'),    
    path('edit-product/<int:product_id>/', views.safe_edit_product, name='edit_product'),
    
    # Wishlist
    path('toggle-wishlist/<int:product_id>/', views.safe_toggle_wishlist, name='toggle_wishlist'),
    
    # Co-admin
    path('coadmin_form/', views.safe_coadmin_form, name='coadmin_form'),
    path('coadmin/', views.safe_coadmin_page, name='coadmin_dashboard'),
   
    # Deal chat
    path('deal/<int:deal_id>/chat/', views.safe_deal_chat, name='deal_chat'),
    path('deal/<int:deal_id>/chat/<int:user_id>/', views.safe_deal_chat_with_user, name='deal_chat_with_user'),
    path('send_deal_message/', views.safe_send_deal_message, name='send_deal_message'),
    path('check_new_deal_messages/', views.safe_check_new_deal_messages, name='check_new_deal_messages'),
    
    # Enhanced coadmin dashboard
    path('coadmin/orders/', views.safe_coadmin_orders, name='coadmin_orders'),
    path('coadmin/products/', views.safe_coadmin_products, name='coadmin_products'),
    path('coadmin/deals/', views.safe_coadmin_deals, name='coadmin_deals'),
    path('coadmin/messages/', views.safe_coadmin_messages, name='coadmin_messages'),
    path('coadmin/accept-order/<int:order_id>/', views.safe_accept_order, name='accept_order'),
    path('coadmin/messages/mark-read/', views.safe_mark_messages_read, name='mark_messages_read'),
    
    # Notifications
    path('notifications/', views.safe_notifications_list, name='notifications_list'),
    path('notifications/<int:notification_id>/mark-read/', views.safe_mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.safe_mark_all_notifications_read, name='mark_all_notifications_read'),
    path('api/notifications/count/', views.safe_get_unread_notifications_count, name='get_unread_notifications_count'),
    path('api/notifications/', views.safe_get_notifications_api, name='get_notifications_api'),

    # Withdrawal system
    path('withdrawal-request/', views.safe_request_withdrawal, name='request_withdrawal'),
    path('withdrawal-history/', views.safe_withdrawal_history, name='withdrawal_history'),
    path('withdrawal/<int:withdrawal_id>/cancel/', views.safe_cancel_withdrawal, name='cancel_withdrawal'),
    
    # Admin withdrawal management
    path('coadmin/withdrawals/', views.safe_admin_withdrawals, name='admin_withdrawals'),
    path('coadmin/withdrawal/<int:withdrawal_id>/process/', views.safe_process_withdrawal, name='process_withdrawal'),

    # Share functionality
    path('get_share_stats/', views.safe_get_share_stats, name='get_share_stats'),
    path('record_share/', views.safe_record_share, name='record_share'),

    # Admin dashboard specific URLs (from admin_views.py)
    path('admin/', admin_views.admin_dashboard, name='admin'), # Main admin dashboard
    path('admin/users/', admin_views.admin_users, name='admin_users'),
    path('admin/get-user-data/<int:user_id>/', admin_views.get_user_data, name='get_user_data'),
    path('admin/add-user/', admin_views.admin_add_user, name='admin_add_user'),
    path('admin/edit-user/<int:user_id>/', admin_views.admin_edit_user, name='admin_edit_user'),
    path('admin/delete-user/<int:user_id>/', admin_views.admin_delete_user, name='admin_delete_user'),
    path('admin/update-user/<int:user_id>/', admin_views.update_user, name='update_user'),
    path('admin/products/', admin_views.admin_products, name='admin_products'),
    path('admin/add-product/', admin_views.admin_add_product, name='admin_add_product'),
    path('admin/edit-product/<int:product_id>/', admin_views.admin_edit_product, name='admin_edit_product'),
    path('admin/delete-product/<int:product_id>/', admin_views.admin_delete_product, name='admin_delete_product'),
    path('admin/orders/', admin_views.admin_orders, name='admin_orders'),
    path('admin/view-order/<int:order_id>/', admin_views.admin_view_order, name='admin_view_order'),
    path('admin/update-order-status/<int:order_id>/', admin_views.admin_update_order_status, name='admin_update_order_status'),
    path('admin/categories/', admin_views.admin_categories, name='admin_categories'),
    path('admin/add-category/', admin_views.admin_add_category, name='admin_add_category'),
    path('admin/edit-category/<int:category_id>/', admin_views.admin_edit_category, name='admin_edit_category'),
    path('admin/delete-category/<int:category_id>/', admin_views.admin_delete_category, name='admin_delete_category'),
    path('admin/deals/', admin_views.admin_deals, name='admin_deals'),
    path('admin/carts/', admin_views.admin_carts, name='admin_carts'),
    path('admin/reviews/', admin_views.admin_reviews, name='admin_reviews'),
    path('admin/view-review/<int:review_id>/', admin_views.admin_view_review, name='admin_view_review'),
    path('admin/delete-review/<int:review_id>/', admin_views.admin_delete_review, name='admin_delete_review'),
    path('admin/chat/', admin_views.admin_chat, name='admin_chat'),
    path('admin/view-message/<int:message_id>/', admin_views.admin_view_message, name='admin_view_message'),
    path('admin/delete-message/<int:message_id>/', admin_views.admin_delete_message, name='admin_delete_message'),
    path('admin/referrals/', admin_views.admin_referrals, name='admin_referrals'),
    path('admin/view-referral/<int:referral_id>/', admin_views.admin_view_referral, name='admin_view_referral'),
    path('admin/withdrawals/', admin_views.admin_withdrawals, name='admin_withdrawals'),
    path('admin/process-withdrawal/<int:withdrawal_id>/', admin_views.admin_process_withdrawal, name='admin_process_withdrawal'),
    path('admin/withdrawal-history/', admin_views.admin_withdrawal_history, name='admin_withdrawal_history'),
    path('admin/view-withdrawal/<int:withdrawal_id>/', admin_views.admin_view_withdrawal, name='admin_view_withdrawal'),
    path('admin/coadmins/', admin_views.admin_coadmins, name='admin_coadmins'),
    path('admin/share-records/', admin_views.admin_share_records, name='admin_share_records'),
]

# Error handlers
handler404 = custom_404_view
handler500 = custom_500_view
handler403 = custom_403_view
handler400 = custom_400_view

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
