from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
# added for referal 
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid
import string
import random

# added for referal 



def generate_referral_code():
    """Generate a unique referral code"""
    letters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(letters) for i in range(8))

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to ='profile',default='1.jpg',blank=True,null=True)
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    auth_token = models.CharField(max_length=100)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # for e/d btn>>
    show_request_manager_btn = models.BooleanField(default=False)
    
    # for referal>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    referral_code = models.CharField(max_length=8, unique=True, default=generate_referral_code)
    referred_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
    points = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    

    def __str__(self):
        return self.user.username
    
# for referral>>>>>>>>>>>>>>>>>>>>    
class Referral(models.Model):
    referrer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_referrals')
    referred = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_referrals')
    created_at = models.DateTimeField(auto_now_add=True)
    is_successful = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('referrer', 'referred')
    
    def __str__(self):
        return f"{self.referrer.username} referred {self.referred.username}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created and not Profile.objects.filter(user=instance).exists():
        Profile.objects.create(user=instance)  # Only create if no profile exists for this user

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

# for referral>>>>>>>>>>>>>>>>>>>>

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
def get_default_seller():
    return User.objects.first().id

class Product(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products',default=get_default_seller)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    commission = models.DecimalField(max_digits=10, decimal_places=2, help_text="Commission amount per sale",default=True)
    stock = models.PositiveIntegerField()
    sold = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/')
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Discount amount (e.g., 10 for $10 off)")

    def __str__(self):
        return self.name
    def get_average_rating(self):
        reviews = self.reviews.all()
        if reviews:
            total_rating = sum(review.rating for review in reviews)
            average = total_rating / len(reviews)
            return round(average, 1)  # Round to 1 decimal place
        return 0
    
    
    def get_rating_count(self):
        return self.reviews.count()
    
    def get_discounted_price(self):
        """Calculate and return the discounted price."""
        if self.discount_amount > 0:
            discounted_price = self.price - self.discount_amount
            # Ensure the discounted price doesn't go below 0
            return max(discounted_price, Decimal('0.00'))
        return self.price

class Order(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20, default='N/A')
    # Add this to your Order model
    order_group = models.CharField(max_length=50, blank=True, null=True)
    
    # Location fields
    province = models.CharField(max_length=50, default='Province Name')
    city = models.CharField(max_length=50, default='Default City')
    street_address = models.TextField()
    delivery_instructions = models.TextField(blank=True, null=True)
    
    # Order details
    quantity = models.PositiveIntegerField(default=1)
    payment_method = models.CharField(max_length=50, default='Cash on Delivery')
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Order status
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order #{self.id} - {self.customer_name}"
    
    
class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user_name = models.CharField(max_length=100)
    rating = models.IntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.product.name} by {self.user_name}"
    def save(self, *args, **kwargs):
        # Ensure rating is between 1 and 5
        if self.rating < 1:
            self.rating = 1
        elif self.rating > 5:
            self.rating = 5
        super().save(*args, **kwargs)


class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username}: {self.message} at {self.timestamp}'  
        
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def total_price(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.quantity})"
    

# class CartOrderItem(models.Model):
#     cart_order = models.ForeignKey(CartOrder, on_delete=models.CASCADE, related_name='items')
#     product = models.ForeignKey(Product, on_delete=models.CASCADE)
#     quantity = models.PositiveIntegerField(default=1)
#     price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of order
#     total = models.DecimalField(max_digits=10, decimal_places=2)
    
#     def __str__(self):
#         return f"{self.quantity} x {self.product.name}"
    
#     def save(self, *args, **kwargs):
#         # Calculate total if not set
#         if not self.total:
#             self.total = self.price * Decimal(self.quantity)
#         super().save(*args, **kwargs)

class Deal(models.Model):
    # Basic Information
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Price Information (keeping for compatibility)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Media
    image = models.ImageField(upload_to='deals/')
    
    # Relationships
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deals')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # New Wholesale-specific fields
    min_order = models.PositiveIntegerField(null=True, blank=True, help_text="Minimum order quantity")
    lead_time = models.CharField(max_length=100, null=True, blank=True, help_text="Estimated time from order to delivery")
    origin = models.CharField(max_length=100, null=True, blank=True, help_text="Country or region of manufacture")
    shipping_terms = models.CharField(max_length=50, null=True, blank=True, help_text="Standard international shipping terms")
    certifications = models.TextField(null=True, blank=True, help_text="Certifications, compliance standards, or quality assurances")
    
    # Shipping destinations
    ship_domestic = models.BooleanField(default=False, help_text="Available for domestic shipping")
    ship_international = models.BooleanField(default=False, help_text="Available for international shipping")
    ship_north_america = models.BooleanField(default=False, help_text="Available for shipping to North America")
    ship_europe = models.BooleanField(default=False, help_text="Available for shipping to Europe")
    ship_asia = models.BooleanField(default=False, help_text="Available for shipping to Asia")
    ship_australia = models.BooleanField(default=False, help_text="Available for shipping to Australia/Oceania")
    ship_africa = models.BooleanField(default=False, help_text="Available for shipping to Africa")
    ship_south_america = models.BooleanField(default=False, help_text="Available for shipping to South America")
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Wholesale Opportunity"
        verbose_name_plural = "Wholesale Opportunities"

class Contact(models.Model):
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name='contacts')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Contact for {self.deal.title} by {self.name}"
    
    


class NewsletterSubscriber(models.Model):
    name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(unique=True)
    consent = models.BooleanField(default=False)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
    
    
    
class LikedProduct(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"
    

from django.core.validators import RegexValidator

class DealChatMessage(models.Model):
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name='chat_messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_deal_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_deal_messages')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender.username} to {self.receiver.username}: {self.message[:30]}" 
    
    class Meta:
        ordering = ['timestamp']

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('order', 'Order Update'),
        ('product', 'Product Update'),
        ('deal', 'Deal Update'),
        ('system', 'System Notification'),
        ('commission', 'Referral Commission'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=100)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True, null=True)  # Optional link to redirect when clicked
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    class Meta:
        ordering = ['-created_at']

class CoAdmin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='coadmin_profile')
    name = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='co_admin_photos/', blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    phone_number = models.CharField(
        max_length=15,
        validators=[RegexValidator(regex=r'^\+?\d{10,15}$', message="Enter a valid phone number.")]
    )
    email = models.EmailField(unique=True)
    nationality_card_front = models.ImageField(upload_to='nationality_cards/', blank=True, null=True)
    nationality_card_back = models.ImageField(upload_to='nationality_cards/', blank=True, null=True)
    dob_certificate = models.ImageField(upload_to='dob_certificates/', blank=True, null=True)
    date_of_birth = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Co-Administrator"
        verbose_name_plural = "Co-Administrators"

    def __str__(self):
        return self.name

    @property
    def full_nationality_card(self):
        return f"{self.nationality_card_front.url} and {self.nationality_card_back.url}" if self.nationality_card_front and self.nationality_card_back else "Not Provided"
    
    
    
    

# New model for tracking referral commissions
class ReferralCommission(models.Model):
    referrer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='earned_commissions')
    referred_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='generated_commissions')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='commissions')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.referrer.username} earned ₹{self.commission_amount} from {self.referred_user.username}'s purchase"
        
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Referral Commission"
        verbose_name_plural = "Referral Commissions"



class WalletWithdrawal(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='withdrawals')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    proof_image = models.ImageField(upload_to='withdrawal_proofs/', blank=True, null=True)
    notes = models.TextField(blank=True, null=True, help_text="Seller's notes regarding the withdrawal")
    admin_notes = models.TextField(blank=True, null=True, help_text="Admin notes regarding the withdrawal")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - ${self.amount} ({self.status})"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Wallet Withdrawal"
        verbose_name_plural = "Wallet Withdrawals"





