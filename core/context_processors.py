from .models import Order


def cart_summary(request):
    """Makes the cart item count available in every template (e.g. for the
    navbar badge), without every view needing to fetch it manually."""
    count = 0
    if request.user.is_authenticated:
        order = Order.objects.filter(user=request.user, ordered=False).prefetch_related("items").first()
        if order:
            count = order.item_count()
    return {"cart_item_count": count}