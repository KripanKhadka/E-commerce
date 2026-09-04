from decimal import Decimal
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.shortcuts import reverse

CATEGORY_CHOICES = (
    ("FB", "Football / Soccer"),
    ("BK", "Basketball"),
    ("TN", "Tennis & Racket Sports"),
    ("RN", "Running & Fitness"),
    ("OW", "Outdoor & Hiking"),
    ("AP", "Sports Apparel & Accessories"),
)

LABEL_CHOICES = (
    ("P", "New"),
    ("S", "Trending"),
    ("D", "Sale"),
)

ADDRESS_CHOICES = (("B", "Billing"), ("S", "Shipping"))

PAYMENT_PROVIDER_CHOICES = (("esewa", "eSewa"),)
PAYMENT_STATUS_CHOICES = (
    ("pending", "Pending"),
    ("completed", "Completed"),
    ("failed", "Failed"),
    ("refunded", "Refunded"),
)

ORDER_STATUS_CHOICES = (
    ("pending", "Payment pending"),
    ("confirmed", "Confirmed"),
    ("processing", "Processing"),
    ("shipping", "Out for delivery"),
    ("delivered", "Delivered"),
    ("cancelled", "Cancelled"),
)


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    stripe_customer_id = models.CharField(max_length=50, blank=True, null=True)
    one_click_purchasing = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


class Item(models.Model):
    title = models.CharField(max_length=120)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    category = models.CharField(choices=CATEGORY_CHOICES, max_length=2)
    label = models.CharField(choices=LABEL_CHOICES, max_length=1, default="P")
    slug = models.SlugField(unique=True)
    description = models.TextField()
    image = models.ImageField(upload_to="products/")
    brand = models.CharField(max_length=50, blank=True, default="Generic")
    stock = models.PositiveIntegerField(default=10)
    featured = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-featured", "-created_at")

    def __str__(self):
        return self.title

    @property
    def current_price(self):
        return self.discount_price if self.discount_price is not None else self.price

    @property
    def is_on_sale(self):
        return self.discount_price is not None and self.discount_price < self.price

    def get_absolute_url(self):
        return reverse("core:product", kwargs={"slug": self.slug})

    def get_add_to_cart_url(self):
        return reverse("core:add-to-cart", kwargs={"slug": self.slug})

    def get_remove_from_cart_url(self):
        return reverse("core:remove-from-cart", kwargs={"slug": self.slug})


class OrderItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ordered = models.BooleanField(default=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} × {self.item.title}"

    def get_total_item_price(self):
        return self.quantity * self.item.price

    def get_total_discount_item_price(self):
        return self.quantity * (self.item.discount_price or Decimal("0"))

    def get_amount_saved(self):
        if self.item.discount_price is None:
            return Decimal("0")
        return self.get_total_item_price() - self.get_total_discount_item_price()

    def get_final_price(self):
        return self.quantity * self.item.current_price


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ref_code = models.CharField(max_length=24, blank=True, null=True, unique=True)
    items = models.ManyToManyField(OrderItem)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField()
    ordered = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default="pending")

    shipping_address = models.ForeignKey(
        "Address", related_name="shipping_address", on_delete=models.SET_NULL, blank=True, null=True
    )
    billing_address = models.ForeignKey(
        "Address", related_name="billing_address", on_delete=models.SET_NULL, blank=True, null=True
    )
    payment = models.ForeignKey("Payment", on_delete=models.SET_NULL, blank=True, null=True)
    coupon = models.ForeignKey("Coupon", on_delete=models.SET_NULL, blank=True, null=True)

    being_delivered = models.BooleanField(default=False)
    received = models.BooleanField(default=False)
    refund_requested = models.BooleanField(default=False)
    refund_granted = models.BooleanField(default=False)

    def __str__(self):
        return self.ref_code or f"Order #{self.pk}"

    def get_subtotal(self):
        return sum((item.get_final_price() for item in self.items.all()), Decimal("0.00"))

    def get_total(self):
        total = self.get_subtotal()
        if self.coupon:
            total = max(Decimal("0.00"), total - self.coupon.amount)
        return total

    def item_count(self):
        return sum(item.quantity for item in self.items.all())


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    street_address = models.CharField(max_length=160)
    apartment_address = models.CharField(max_length=100, blank=True)
    zip = models.CharField(max_length=20, blank=True)
    address_type = models.CharField(max_length=1, choices=ADDRESS_CHOICES, default="S")
    default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} — {self.street_address}"


class Payment(models.Model):
    stripe_charge_id = models.CharField(max_length=50, blank=True)
    provider = models.CharField(max_length=10, choices=PAYMENT_PROVIDER_CHOICES)
    status = models.CharField(max_length=12, choices=PAYMENT_STATUS_CHOICES, default="pending")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_id = models.CharField(max_length=100, blank=True)
    gateway_reference = models.CharField(max_length=120, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return f"{self.provider.title()} — NPR {self.amount} — {self.status}"


class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.code


class Refund(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    reason = models.TextField()
    accepted = models.BooleanField(default=False)
    email = models.EmailField()

    def __str__(self):
        return f"Refund #{self.pk}"


class OrderMessage(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="messages")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    body = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message for {self.order.ref_code or self.order.pk}"


class HeroSlide(models.Model):
    title = models.CharField(max_length=120)
    subtitle = models.CharField(max_length=220, blank=True)
    image = models.ImageField(upload_to="slides/")
    button_text = models.CharField(max_length=40, default="Shop now")
    button_url = models.CharField(max_length=200, default="/#products")
    active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "-id")

    def __str__(self):
        return self.title


def userprofile_receiver(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)


post_save.connect(userprofile_receiver, sender=settings.AUTH_USER_MODEL)