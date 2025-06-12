from django.contrib import admin
from .models import Profile, Category, Product, Order, Review, ChatMessage, Cart,Referral, Deal,NewsletterSubscriber,LikedProduct,CoAdmin,DealChatMessage

# Register your models here.

# @admin.register(Profile)
# class ProfileAdmin(admin.ModelAdmin):
#     list_display = ['user', 'is_verified', 'created_at']
#     search_fields = ['user__username']
#     list_filter = ['is_verified']


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user','referral_code', 'referred_by', 'points', 'is_verified', 'created_at']
    search_fields = ['user__username', 'referral_code']
    list_filter = ['is_verified','created_at']

@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ('referrer', 'referred', 'created_at', 'is_successful')
    search_fields = ('referrer__username', 'referred__username')
    list_filter = ('created_at', 'is_successful')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'is_available']
    list_filter = ['category', 'is_available']
    search_fields = ['name', 'category__name']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'customer_email', 'status', 'total_price', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'province')
    search_fields = ('customer_name', 'customer_email', 'product__name')
    ordering = ('-created_at',)
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'user_name', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user_name', 'product__name')
    ordering = ('-created_at',)
    readonly_fields = ('id', 'created_at')

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'timestamp')
    search_fields = ('user__username', 'message')
    list_filter = ('timestamp',)
    date_hierarchy = 'timestamp'

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'quantity', 'added_at']
    search_fields = ['user__username', 'product__name']
    list_filter = ['added_at']



@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ['title', 'seller', 'price', 'discount_price', 'is_active', 'created_at']
    search_fields = ['title', 'seller__username']
    list_filter = ['is_active', 'created_at', 'updated_at']
    
    
   
@admin.register(NewsletterSubscriber) 
class NewsletterSubscriber(admin.ModelAdmin):
     list_display = ['name','email','consent','subscribed_at']
     list_filter = ['subscribed_at']

admin.site.register(LikedProduct)



@admin.register(CoAdmin)
class CoAdminAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone_number', 'date_of_birth')
    search_fields = ('name', 'email', 'phone_number')
    

class DealChatMessageAdmin(admin.ModelAdmin):
    list_display = ('deal', 'sender', 'receiver', 'message', 'timestamp', 'is_read')
    search_fields = ('sender__username', 'receiver__username', 'message')
    list_filter = ('timestamp', 'is_read')
    date_hierarchy = 'timestamp'

admin.site.register(DealChatMessage, DealChatMessageAdmin)
