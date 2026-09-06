from django.contrib import admin
from .models import Address, Coupon, HeroSlide, Item, Order, OrderItem, OrderMessage, Payment, Refund, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "full_name", "phone", "one_click_purchasing")
    search_fields = ("user__username", "user__email", "full_name", "phone")


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("title", "brand", "category", "price", "discount_price", "stock", "featured", "active", "label")
    list_filter = ("category", "featured", "active", "label", "brand", "created_at")
    search_fields = ("title", "description", "brand")
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ("stock", "featured", "active", "label")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ('Product Information', {
            'fields': ('title', 'slug', 'brand', 'description', 'category')
        }),
        ('Pricing', {
            'fields': ('price', 'discount_price')
        }),
        ('Stock & Visibility', {
            'fields': ('stock', 'active', 'featured', 'label')
        }),
        ('Metadata', {
            'fields': ('image', 'created_at', 'updated_at')
        }),
    )


@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    list_display = ("title", "sort_order", "active", "button_text")
    list_editable = ("sort_order", "active")
    search_fields = ("title", "subtitle")
    fieldsets = (
        ('Slide Content', {
            'fields': ('title', 'subtitle', 'image')
        }),
        ('Button', {
            'fields': ('button_text', 'button_url')
        }),
        ('Display Settings', {
            'fields': ('sort_order', 'active')
        }),
    )
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" width="200" />'
        return "No image"
    image_preview.allow_tags = True
    image_preview.short_description = 'Image Preview'


class OrderItemInline(admin.TabularInline):
    model = Order.items.through
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("ref_code", "user", "status", "ordered", "payment", "ordered_date")
    list_filter = ("status", "ordered", "being_delivered", "received")
    search_fields = ("ref_code", "user__username", "user__email")
    readonly_fields = ("start_date", "ordered_date")
    list_select_related = ("user", "payment")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "provider", "amount", "status", "transaction_id", "timestamp")
    list_filter = ("provider", "status")
    search_fields = ("transaction_id", "gateway_reference", "user__username")
    readonly_fields = ("timestamp", "updated_at", "gateway_response")


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "email", "accepted")
    list_filter = ("accepted",)
    search_fields = ("email", "order__ref_code")
    list_editable = ("accepted",)


admin.site.register(OrderItem)
admin.site.register(OrderMessage)
admin.site.register(Address)
admin.site.register(Coupon)

admin.site.site_header = "Hamro Sports Administration"
admin.site.site_title = "Hamro Sports Admin"
admin.site.index_title = "Store management"
