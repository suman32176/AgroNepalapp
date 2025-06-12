from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.db.models import F
from .models import Order, Profile, Product
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount

@receiver(pre_save, sender=Order)
def update_seller_wallet_and_product_stats_on_delivery(sender, instance, **kwargs):
    """
    Signal handler that:
    1. Updates the seller's wallet balance when an order status changes to 'delivered'
    2. Increments the product's 'sold' field by the order quantity
    
    This function:
    - Checks if this is an existing order (not a new one)
    - Retrieves the previous state of the order
    - Checks if the status changed from something else to 'delivered'
    - If so, updates the seller's wallet and product stats
    """
    # Skip if this is a new order being created
    if not instance.pk:
        return
    
    try:
        # Get the order before the update
        old_order = Order.objects.get(pk=instance.pk)
        
        # Check if status changed to 'delivered'
        if old_order.status != 'delivered' and instance.status == 'delivered':
            # Get the product and its seller
            product = instance.product
            seller = product.seller
            
            if seller:
                # Calculate the amount to add to wallet
                # This includes the product price minus any commission
                amount_to_add = product.price - product.commission
                
                # Update the seller's wallet balance
                Profile.objects.filter(user=seller).update(
                    wallet_balance=F('wallet_balance') + amount_to_add
                )
                
                # Update the product's sold count
                # Increment by the order quantity
                Product.objects.filter(pk=product.pk).update(
                    sold=F('sold') + instance.quantity
                )
                
                print(f"Added {amount_to_add} to {seller.username}'s wallet for order #{instance.id}")
                print(f"Incremented sold count for product '{product.name}' by {instance.quantity}")
    except Order.DoesNotExist:
        # Order doesn't exist yet, this is a new order
        pass
    except Exception as e:
        # Log any errors but don't prevent the order from being saved
        print(f"Error updating seller wallet or product stats: {str(e)}")

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created and not Profile.objects.filter(user=instance).exists():
        Profile.objects.create(user=instance)  # Only create if no profile exists for this user

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

@receiver(post_save, sender=SocialAccount)
def verify_google_user(sender, instance, created, **kwargs):
    """
    Automatically verify users who register through Google
    """
    if created and instance.provider == 'google':
        try:
            profile = Profile.objects.get(user=instance.user)
            profile.is_verified = True
            profile.save()
        except Profile.DoesNotExist:
            pass  # Profile will be created by the other signal handler

