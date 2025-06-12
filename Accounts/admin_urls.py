from django.urls import path
from . import admin_views

urlpatterns = [
    # Dashboard
    path('', admin_views.admin_dashboard, name='admin_dashboard'),
    path('admin/', admin_views.admin_dashboard, name='admin'),
    path('dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    
    # Users & Profiles
    path('users/', admin_views.admin_users, name='admin_users'),
    path('add-user/', admin_views.admin_add_user, name='admin_add_user'),
    path('edit-user/<int:user_id>/', admin_views.admin_edit_user, name='admin_edit_user'),
    path('delete-user/<int:user_id>/', admin_views.admin_delete_user, name='admin_delete_user'),
    path('admin/get-user-data/<int:user_id>/', admin_views.get_user_data, name='get_user_data'),
    path('admin/update-user/<int:user_id>/', admin_views.update_user, name='update_user'),
    path('admin/get-user-data/<int:user_id>/', admin_views.get_user_data, name='get_user_data'),
    
    # Co-Admins
    path('coadmins/', admin_views.admin_coadmins, name='admin_coadmins'),
    
    # Referrals
    path('referrals/', admin_views.admin_referrals, name='admin_referrals'),
    path('view-referral/<int:referral_id>/', admin_views.admin_view_referral, name='admin_view_referral'),
    
    # Categories
    path('categories/', admin_views.admin_categories, name='admin_categories'),
    path('add-category/', admin_views.admin_add_category, name='admin_add_category'),
    path('edit-category/<int:category_id>/', admin_views.admin_edit_category, name='admin_edit_category'),
    path('delete-category/<int:category_id>/', admin_views.admin_delete_category, name='admin_delete_category'),
    
    # Products
    path('products/', admin_views.admin_products, name='admin_products'),
    path('add-product/', admin_views.admin_add_product, name='admin_add_product'),
    path('edit-product/<int:product_id>/', admin_views.admin_edit_product, name='admin_edit_product'),
    path('delete-product/<int:product_id>/', admin_views.admin_delete_product, name='admin_delete_product'),
    
    # Orders
    path('orders/', admin_views.admin_orders, name='admin_orders'),
    path('view-order/<int:order_id>/', admin_views.admin_view_order, name='admin_view_order'),
    path('update-order-status/<int:order_id>/', admin_views.admin_update_order_status, name='admin_update_order_status'),
    path('print-order/<int:order_id>/', admin_views.admin_view_order, name='admin_print_order'),
    path('admin/orders/update-status/<int:order_id>/', admin_views.update_order_status, name='update_order_status'),
    
    # Reviews
    path('reviews/', admin_views.admin_reviews, name='admin_reviews'),
    path('view-review/<int:review_id>/', admin_views.admin_view_review, name='admin_view_review'),
    path('delete-review/<int:review_id>/', admin_views.admin_delete_review, name='admin_delete_review'),
    
    # Chat Messages
    path('chat/', admin_views.admin_chat, name='admin_chat'),
    path('view-message/<int:message_id>/', admin_views.admin_view_message, name='admin_view_message'),
    path('delete-message/<int:message_id>/', admin_views.admin_delete_message, name='admin_delete_message'),
    
    # Deals
    path('deals/', admin_views.admin_deals, name='admin_deals'),
    
    # Shopping Carts
    path('carts/', admin_views.admin_carts, name='admin_carts'),
    
    
    
    # Withdrawals
    path('withdrawals/', admin_views.admin_withdrawals, name='admin_withdrawals'),
    path('process-withdrawal/<int:withdrawal_id>/', admin_views.admin_process_withdrawal, name='admin_process_withdrawal'),
    path('withdrawal-history/', admin_views.admin_withdrawal_history, name='admin_withdrawal_history'),
    path('withdrawal/<int:withdrawal_id>/', admin_views.admin_view_withdrawal, name='admin_view_withdrawal'),
]