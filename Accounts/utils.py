from .models import ReferralCommission, Profile
from .models import Notification  # If you're using a Notification model
from django.contrib.auth.models import User


def give_commission_if_delivered(order):
    """
    This function checks for pending ReferralCommission records related to a delivered order.
    If any are found, it adds the commission amount to the referrer's wallet and marks the commission as given.
    """
    commissions = ReferralCommission.objects.filter(order=order, is_given=False)
    for commission in commissions:
        try:
            # Update referrer's wallet
            referrer_profile = commission.referrer.profile
            referrer_profile.wallet_balance += commission.commission_amount
            referrer_profile.save()

            # Mark the commission as given
            commission.is_given = True
            commission.save()

            # Send notification to the referrer
            create_notification(
                user=commission.referrer,
                notification_type='commission',
                title="Commission earned!",
                message=(
                    f"You earned ₹{commission.commission_amount} commission from "
                    f"{commission.referred_user.username}'s ."
                ),
                link="/profile/"
            )

        except Exception as e:
            print(f"Error giving commission: {e}")


def create_notification(user, notification_type, title, message, link=None):
    """
    Create a notification for a user.
    """
    try:
        Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            link=link
        )
    except Exception as e:
        print(f"Error creating notification: {e}")
