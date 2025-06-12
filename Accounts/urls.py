from django.urls import path, include
from . import views
from .views import (home,login_attempt,register_attempt,success,token_send,verify,error_page,dashboard,logout_attempt,change_password,profile,add_product,product_detail,product,chat_room,send_message,cart_view,add_to_cart,remove_from_cart,order,order_details,submit_review,resend_verification,
                  request_withdrawal, withdrawal_history, cancel_withdrawal, admin_withdrawals, process_withdrawal)




urlpatterns = [
    path('', home, name='home'),
    # path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('login/', login_attempt, name='login_attempt'), 
    path('register/', register_attempt, name='register_attempt'),
    
    # for referral>>>>
    path('refer/<str:referral_code>/', register_attempt, name='register_with_referral'),    
    
    path('token', token_send, name = 'token_send'),
    path('success', success, name = 'success'),
    path('verify/<auth_token>', verify, name = 'verify'),
    path('error', error_page, name='error'),
    path('dashboard/', dashboard, name='dashboard'),
    path('logout', logout_attempt, name='logout_attempt'),
    path('change_password', change_password, name='change_password'),
    path('profile/', views.profile, name='profile'),
    path('accounts/', include('allauth.urls')),
    
    # for deal >
    path('deals', views.deals_list, name='deals'),
    path('deal_list/<int:pk>/', views.deal_detail, name='deal_detail'),
    path('add_deal/', views.add_deal, name='add_deal'),
    path('<int:pk>/edit/', views.edit_deal, name='edit_deal'),
    path('deal/<int:pk>/delete/', views.delete_deal, name='delete_deal'),

    path('add-product/', views.add_product, name='add_product'),
    path('product/', views.product, name='product'),
    path('product/<int:id>/', views.product_detail, name='product_detail'),
    path('product/<int:id>/review/', submit_review, name='submit_review'),
    path('product/<int:id>/delete/', views.delete_product, name='delete_product'),
    path('chat/', chat_room, name='chat_room'),
    path('send_message/', send_message, name='send_message'),
    # cart
    path('cart/', cart_view, name='cart'),
    path('cart/add/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:cart_id>/', remove_from_cart, name='remove_from_cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:cart_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('update_cart/<int:item_id>/', views.update_cart, name='update_cart'),
    path('remove_from_cart/<int:item_id>/', views.remove_from_cart_ajax, name='remove_from_cart_ajax'),
    path('clear_cart/', views.clear_cart, name='clear_cart'),
    
    # path('cart-checkout/', views.cart_checkout, name='cart_checkout'),
    # path('cart-order-confirmation/<int:order_id>/', views.cart_order_confirmation, name='cart_order_confirmation'),
    path('cart-orders/', views.cart_order_history, name='cart_order_history'),
    path('update-cart-order-status/<int:order_id>/', views.update_cart_order_status, name='update_cart_order_status'),
    path('cancel-cart-order/<int:order_id>/', views.cancel_cart_order, name='cancel_cart_order'),
    path('cart/checkout/', views.cart_checkout, name='cart_checkout'),
    path('cart/confirmation/<int:order_id>/', views.cart_order_confirmation, name='cart_order_confirmation'),
    path('cart/confirmation/<int:order_id>/', views.cart_order_confirmation, name='order_confirmation'),
    
    # AJAX endpoints for cart checkout
    path('get-cities/', views.get_cities, name='get_cities'),
    path('calculate-shipping/', views.calculate_shipping_ajax, name='calculate_shipping'),
    # cart
    path('order/<int:product_id>/', views.order, name='order'),
    path('order_details/', views.order_details, name='order_details'),
    path('order/<int:order_id>/update-status/', views.update_order_status, name='update_order_status'),
    path('order/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    path('calculate_shipping_ajax/', views.calculate_shipping_ajax, name='calculate_shipping_ajax'),
    # path('order-group-confirmation/<str:order_group>/', views.order_confirmation, name='order_group_confirmation'),
    # path('admin/orders/<int:order_id>/update-status/', views.admin_update_order_status, name='admin_update_order_status'),
    
    path('job/', views.job_page, name='job'),
    path('hi/', views.hi, name='hi'),
    path('home2/', views.home2, name='home2'),
    path('resend-verification/', resend_verification, name='resend_verification'),


    # for category pages
    path('categories/', views.categories_view, name='categories'),
    path('category/<int:category_id>/', views.category_detail_view, name='category_detail'),
    
    # Search functionality
    path('search/', views.search_products, name='search_products'),
    
    # Newsletter signup
    path('newsletter-signup/', views.newsletter_signup, name='newsletter_signup'),    
    path('send_hello_email/', views.send_hello_email, name='send_hello_email'),
    path('seller/', views.seller_dashboard, name='seller_dashboard'),    
    path('edit-product/<int:product_id>/', views.edit_product, name='edit_product'),
    
    #for liked product
    path('toggle-wishlist/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    
    
    
    # for caadmin>>>>>>>>>>>>>>>>
    path('coadmin_form/', views.coadmin_form, name='coadmin_form'),
    # path('orders/', views.orders_dashboard, name='orders_dashboard'),
    path('coadmin/', views.coadmin_page, name='coadmin_dashboard'),
   
    # path('accept-order/<int:order_id>/', views.accept_order, name='accept_order'),
    
    # Deal chat URLs
    path('deal/<int:deal_id>/chat/', views.deal_chat, name='deal_chat'),
    path('deal/<int:deal_id>/chat/<int:user_id>/', views.deal_chat_with_user, name='deal_chat_with_user'),
    path('send_deal_message/', views.send_deal_message, name='send_deal_message'),
    path('check_new_deal_messages/', views.check_new_deal_messages, name='check_new_deal_messages'),
    
    # Enhanced coadmin dashboard URLs
    path('coadmin/orders/', views.coadmin_orders, name='coadmin_orders'),
    path('coadmin/products/', views.coadmin_products, name='coadmin_products'),
    path('coadmin/deals/', views.coadmin_deals, name='coadmin_deals'),
    path('coadmin/messages/', views.coadmin_messages, name='coadmin_messages'),
    path('coadmin/accept-order/<int:order_id>/', views.accept_order, name='accept_order'),
    path('coadmin/messages/mark-read/', views.mark_messages_read, name='mark_messages_read'),
    
    # Notification URLs
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/<int:notification_id>/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('api/notifications/count/', views.get_unread_notifications_count, name='get_unread_notifications_count'),
    path('api/notifications/', views.get_notifications_api, name='get_notifications_api'),

    # Withdrawal system URLs
    path('withdrawal-request/', request_withdrawal, name='request_withdrawal'),
    path('withdrawal-history/', withdrawal_history, name='withdrawal_history'),
    path('withdrawal/<int:withdrawal_id>/cancel/', cancel_withdrawal, name='cancel_withdrawal'),
    
    # Admin withdrawal management
    path('coadmin/withdrawals/', admin_withdrawals, name='admin_withdrawals'),
    path('coadmin/withdrawal/<int:withdrawal_id>/process/', process_withdrawal, name='process_withdrawal'),
]