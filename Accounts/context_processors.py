from .models import Cart, Notification

def cart_processor(request):
    """Context processor to add cart count and items to all templates"""
    if request.user.is_authenticated:
        cart_items = Cart.objects.filter(user=request.user)
        cart_count = cart_items.count()
        cart_total = sum(item.total_price() for item in cart_items)
        return {
            'cart_items': cart_items,
            'cart_count': cart_count,
            'cart_total': cart_total
        }
    return {
        'cart_items': [],
        'cart_count': 0,
        'cart_total': 0
    }

def notification_processor(request):
    """Context processor to add notification count to all templates"""
    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()
        return {
            'unread_notifications': unread_notifications,
        }
    return {
        'unread_notifications': 0,
    } 