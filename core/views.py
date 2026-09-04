import base64
import hashlib
import hmac
import json
import uuid
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView, ListView, View

from .forms import AccountForm, CouponForm, RefundForm, RegisterForm
from .models import (
    Address,
    Coupon,
    HeroSlide,
    Item,
    Order,
    OrderItem,
    OrderMessage,
    Payment,
    Refund,
    UserProfile,
)


def order_for_user(user):
    return Order.objects.filter(user=user, ordered=False).prefetch_related("items__item").first()


def make_ref_code():
    return uuid.uuid4().hex[:12].upper()


def absolute_url(request, name, **kwargs):
    return request.build_absolute_uri(reverse(name, kwargs=kwargs))


def complete_paid_order(order, payment, gateway_response=None):
    with transaction.atomic():
        order = Order.objects.select_for_update().get(pk=order.pk)
        payment = Payment.objects.select_for_update().get(pk=payment.pk)
        if payment.status == "completed" and order.ordered:
            return True

        for order_item in order.items.select_related("item"):
            item = Item.objects.select_for_update().get(pk=order_item.item_id)
            if item.stock < order_item.quantity:
                payment.status = "failed"
                payment.gateway_response = gateway_response or {"error": "Insufficient stock"}
                payment.save(update_fields=["status", "gateway_response", "updated_at"])
                return False

        for order_item in order.items.select_related("item"):
            item = Item.objects.select_for_update().get(pk=order_item.item_id)
            item.stock -= order_item.quantity
            item.save(update_fields=["stock", "updated_at"])
            order_item.ordered = True
            order_item.save(update_fields=["ordered"])

        payment.status = "completed"
        payment.gateway_response = gateway_response or {}
        payment.save(update_fields=["status", "gateway_response", "updated_at"])

        order.payment = payment
        order.ordered = True
        order.status = "confirmed"
        order.ordered_date = timezone.now()
        if not order.ref_code:
            order.ref_code = make_ref_code()
        order.save(update_fields=["payment", "ordered", "status", "ordered_date", "ref_code"])
    return True


class RegisterView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("core:account")
        return render(request, "registration/register.html", {"form": RegisterForm()})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect("core:account")
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome to Hamro Sports. Your account is ready.")
            return redirect("core:account")
        return render(request, "registration/register.html", {"form": form})


@login_required
def account(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = AccountForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your account details have been updated.")
            return redirect("core:account")
    else:
        form = AccountForm(user=request.user)
    orders = Order.objects.filter(user=request.user, ordered=True).prefetch_related("items__item", "payment").order_by("-ordered_date")
    return render(request, "account.html", {"form": form, "profile": profile, "orders": orders})


class HomeView(ListView):
    model = Item
    template_name = "home.html"
    paginate_by = 12

    def get_queryset(self):
        return Item.objects.filter(active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        categories = [
            ("FB", "Football / Soccer", "Match balls, boots and training essentials."),
            ("BK", "Basketball", "Hoops-ready equipment and performance wear."),
            ("TN", "Tennis & Racket Sports", "Racquets, balls and court essentials."),
            ("RN", "Running & Fitness", "Comfort and performance for every session."),
            ("OW", "Outdoor & Hiking", "Practical gear for trails and weekend adventures."),
            ("AP", "Apparel & Accessories", "Everyday sportswear and useful extras."),
        ]
        context["hero_slides"] = HeroSlide.objects.filter(active=True).exclude(image='')
        context["featured_items"] = Item.objects.filter(active=True, featured=True).exclude(image='')[:8]
        context["categories"] = categories
        context["grouped_items"] = [
            {"code": code, "title": title, "description": desc,
             "items": Item.objects.filter(active=True, category=code).exclude(image='')[:6]}
            for code, title, desc in categories
        ]
        return context


class ItemDetailView(DetailView):
    model = Item
    template_name = "product.html"
    queryset = Item.objects.filter(active=True)


@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug, active=True)
    if item.stock < 1:
        messages.error(request, "This product is currently out of stock.")
        return redirect(item.get_absolute_url())

    order = order_for_user(request.user)
    order_item, created = OrderItem.objects.get_or_create(
        item=item, user=request.user, ordered=False, defaults={"quantity": 1}
    )
    if not order:
        order = Order.objects.create(user=request.user, ordered_date=timezone.now())
        order.items.add(order_item)
        messages.success(request, f"{item.title} was added to your cart.")
    elif not created:
        if order_item.quantity >= item.stock:
            messages.warning(request, "You cannot add more than the available stock.")
        else:
            order_item.quantity += 1
            order_item.save(update_fields=["quantity"])
            messages.success(request, "Cart quantity updated.")
    else:
        order.items.add(order_item)
        messages.success(request, f"{item.title} was added to your cart.")
    return redirect("core:order-summary")


@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order = order_for_user(request.user)
    if not order:
        return redirect("core:order-summary")
    order_item = order.items.filter(item=item).first()
    if not order_item:
        return redirect("core:order-summary")
    if order_item.quantity > 1:
        order_item.quantity -= 1
        order_item.save(update_fields=["quantity"])
    else:
        order.items.remove(order_item)
        order_item.delete()
    if not order.items.exists():
        order.delete()
    return redirect("core:order-summary")


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, "order_summary.html", {"object": order_for_user(request.user)})


@login_required
def checkout(request):
    order = order_for_user(request.user)
    if not order or not order.items.exists():
        messages.info(request, "Your cart is empty.")
        return redirect("core:home")
    if request.method == "POST":
        street = request.POST.get("street_address", "").strip()
        apartment = request.POST.get("apartment_address", "").strip()
        zip_code = request.POST.get("zip", "").strip()
        if not street:
            messages.error(request, "Please enter your delivery address.")
        else:
            address = Address.objects.create(
                user=request.user, street_address=street, apartment_address=apartment,
                zip=zip_code, address_type="S", default=True,
            )
            order.shipping_address = address
            order.billing_address = address
            order.save(update_fields=["shipping_address", "billing_address"])
            return redirect("core:payment")
    return render(request, "checkout.html", {"order": order})


@login_required
def payment(request):
    order = order_for_user(request.user)
    if not order or not order.items.exists():
        return redirect("core:order-summary")
        
    if request.method == "POST":
        payment_obj = Payment.objects.create(
            user=request.user, provider="esewa", amount=order.get_total(), status="pending"
        )

        # Bind the payment object to the active order
        order.payment = payment_obj
        order.save(update_fields=["payment"])

        return initiate_esewa(request, order, payment_obj)

    return render(request, "payment.html", {"order": order})


def esewa_signature(message):
    secret_key = getattr(settings, 'ESEWA_SECRET_KEY', '')
    return base64.b64encode(
        hmac.new(secret_key.encode(), message.encode(), hashlib.sha256).digest()
    ).decode()


def initiate_esewa(request, order, payment_obj):
    esewa_key = getattr(settings, 'ESEWA_SECRET_KEY', None)
    if not esewa_key:
        payment_obj.status = "failed"
        payment_obj.gateway_response = {"error": "ESEWA_SECRET_KEY is not configured"}
        payment_obj.save(update_fields=["status", "gateway_response", "updated_at"])
        messages.error(request, "eSewa is not configured yet. Add ESEWA_SECRET_KEY to your .env file.")
        return redirect("core:payment")

    transaction_uuid = f"HS-{order.pk}-{uuid.uuid4().hex[:8]}"
    total_decimal = order.get_total().quantize(Decimal("0.01"))
    total_str = f"{total_decimal:.2f}"
    product_code = getattr(settings, 'ESEWA_PRODUCT_CODE', 'EPAYTEST')
    form_url = getattr(settings, 'ESEWA_FORM_URL', 'https://rc-epay.esewa.com.np/api/epay/main/v2/form')

    signature = esewa_signature(
        f"total_amount={total_str},transaction_uuid={transaction_uuid},product_code={product_code}"
    )
    payment_obj.gateway_reference = transaction_uuid
    payment_obj.gateway_response = {"transaction_uuid": transaction_uuid}
    payment_obj.save(update_fields=["gateway_reference", "gateway_response", "updated_at"])

    context = {
        "form_url": form_url,
        "fields": {
            "amount": total_str, "tax_amount": "0", "total_amount": total_str,
            "transaction_uuid": transaction_uuid, "product_code": product_code,
            "product_service_charge": "0", "product_delivery_charge": "0",
            "success_url": absolute_url(request, "core:esewa-success"),
            "failure_url": absolute_url(request, "core:esewa-failure"),
            "signed_field_names": "total_amount,transaction_uuid,product_code",
            "signature": signature,
        },
    }
    return render(request, "esewa_redirect.html", context)


def _mark_failed_payment(payment, response):
    payment.status = "failed"
    payment.gateway_response = response if isinstance(response, dict) else {"response": str(response)}
    payment.save(update_fields=["status", "gateway_response", "updated_at"])


@login_required
def esewa_success(request):
    encoded = request.GET.get("data", "")
    if not encoded:
        messages.error(request, "eSewa returned without payment data.")
        return redirect("core:payment")
    try:
        payload = json.loads(base64.b64decode(encoded).decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        messages.error(request, "The eSewa response could not be read.")
        return redirect("core:payment")

    transaction_uuid = payload.get("transaction_uuid", "")
    payment_obj = Payment.objects.filter(
        user=request.user, provider="esewa", gateway_reference=transaction_uuid
    ).order_by("-id").first()
    if not payment_obj:
        messages.error(request, "The eSewa payment record could not be found. Please check with our support.")
        return redirect("core:order-summary")

    signed_names = payload.get("signed_field_names", "")
    signed_message = ",".join(
        f"{name}={payload.get(name, '')}" for name in signed_names.split(",")
    )
    valid_signature = hmac.compare_digest(
        esewa_signature(signed_message), payload.get("signature", "")
    )
    try:
        returned_amount = Decimal(str(payload.get("total_amount")))
    except (InvalidOperation, TypeError):
        returned_amount = Decimal("-1")

    order = Order.objects.filter(payment=payment_obj).first()
    # eSewa may return status as "COMPLETE" or other variations
    status = payload.get("status", "").upper()
    if (status in ["COMPLETE", "COMPLETED"] and valid_signature
            and returned_amount == payment_obj.amount and order):
        payment_obj.transaction_id = payload.get("transaction_code", "")
        payment_obj.save(update_fields=["transaction_id", "updated_at"])
        if complete_paid_order(order, payment_obj, payload):
            messages.success(request, "eSewa payment successful. Your order is confirmed!")
            return redirect("core:order-status")
        messages.error(request, "Payment verified but order could not be processed. Please contact support.")
    else:
        if not valid_signature:
            messages.error(request, "Payment signature verification failed. Possible tampering detected.")
        elif status not in ["COMPLETE", "COMPLETED"]:
            messages.error(request, f"eSewa payment status: {status}. Payment unsuccessful.")
        elif returned_amount != payment_obj.amount:
            messages.error(request, f"Amount mismatch. Expected {payment_obj.amount}, got {returned_amount}.")
        else:
            messages.error(request, "eSewa payment could not be verified.")
        _mark_failed_payment(payment_obj, payload)
    return redirect("core:payment")


@login_required
def esewa_failure(request):
    transaction_uuid = request.GET.get("transaction_uuid", "")
    if transaction_uuid:
        payment_obj = Payment.objects.filter(
            user=request.user, provider="esewa", gateway_reference=transaction_uuid
        ).first()
        if payment_obj:
            _mark_failed_payment(payment_obj, dict(request.GET.items()))
    messages.warning(request, "The eSewa payment was cancelled or unsuccessful.")
    return redirect("core:payment")


@login_required
def add_coupon(request):
    if request.method == "POST":
        form = CouponForm(request.POST)
        if form.is_valid():
            try:
                order = order_for_user(request.user)
                coupon = Coupon.objects.get(code=form.cleaned_data["code"].upper())
                if order:
                    order.coupon = coupon
                    order.save(update_fields=["coupon"])
                    messages.success(request, f"Coupon {coupon.code} applied.")
            except Coupon.DoesNotExist:
                messages.error(request, "That coupon code is not valid.")
    return redirect("core:order-summary")


@login_required
def request_refund(request):
    if request.method == "POST":
        form = RefundForm(request.POST)
        if form.is_valid():
            order = Order.objects.filter(user=request.user, ordered=True).order_by("-ordered_date").first()
            if order:
                Refund.objects.create(order=order, **form.cleaned_data)
                order.refund_requested = True
                order.save(update_fields=["refund_requested"])
                messages.success(request, "Your refund request has been submitted.")
                return redirect("core:order-status")
        messages.error(request, "Please check the refund form.")
    return render(request, "request_refund.html", {"form": RefundForm()})


@login_required
def order_status(request):
    order = Order.objects.filter(
        user=request.user, ordered=True
    ).prefetch_related("items__item", "messages").order_by("-ordered_date").first()
    if request.method == "POST" and order:
        body = request.POST.get("body", "").strip()
        if body:
            OrderMessage.objects.create(order=order, user=request.user, body=body)
            messages.success(request, "Message sent.")
        return redirect("core:order-status")
    return render(request, "order_status.html", {"order": order})


@login_required
def order_detail(request, pk):
    """Show one completed order belonging to the logged-in customer."""
    order = get_object_or_404(
        Order.objects.prefetch_related("items__item", "messages").select_related("payment", "shipping_address", "billing_address"),
        pk=pk,
        user=request.user,
        ordered=True,
    )
    return render(request, "order_status.html", {
        "order": order,
        "is_order_detail": True,
    })


@login_required
def confirm_received(request):
    order = Order.objects.filter(user=request.user, ordered=True).order_by("-ordered_date").first()
    if order and order.being_delivered:
        order.received = True
        order.being_delivered = False
        order.status = "delivered"
        order.save(update_fields=["received", "being_delivered", "status"])
        messages.success(request, "Thanks! Your order is marked as received.")
    return redirect("core:order-status")