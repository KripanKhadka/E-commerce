from django.db import migrations, models
from django.utils import timezone


def seed_slides(apps, schema_editor):
    HeroSlide = apps.get_model("core", "HeroSlide")
    Item = apps.get_model("core", "Item")
    seeds = [
        ("Train harder. Play better.", "Performance gear for football, fitness and every weekend game.", "Shop the collection"),
        ("Built for the trail.", "Reliable outdoor essentials for Nepal's roads, hills and mountains.", "Explore outdoor"),
        ("Game-day essentials.", "Fresh footwear, apparel and equipment for your next session.", "Browse products"),
    ]
    first_items = list(Item.objects.order_by("id")[:3])
    for item in first_items:
        item.featured = True
        if item.stock == 0:
            item.stock = 10
        item.save(update_fields=["featured", "stock"])
    images = [item.image for item in first_items]
    for i, (title, subtitle, button) in enumerate(seeds):
        if i < len(images) and images[i]:
            HeroSlide.objects.get_or_create(
                title=title,
                defaults={"subtitle": subtitle, "button_text": button, "button_url": "/#products",
                          "image": images[i], "sort_order": i, "active": True},
            )

def normalize_legacy_payments(apps, schema_editor):
    Payment = apps.get_model("core", "Payment")
    for payment in Payment.objects.all():
        raw = payment.stripe_charge_id or ""
        provider = "esewa" if raw.startswith("esewa") else "khalti"
        payment.provider = provider
        payment.status = "completed"
        payment.transaction_id = raw
        payment.gateway_reference = raw
        payment.save(update_fields=["provider", "status", "transaction_id", "gateway_reference"])


class Migration(migrations.Migration):
    dependencies = [("core", "0003_ordermessage")]

    operations = [
        migrations.CreateModel(
            name="HeroSlide",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=120)),
                ("subtitle", models.CharField(blank=True, max_length=220)),
                ("image", models.ImageField(upload_to="slides/")),
                ("button_text", models.CharField(default="Shop now", max_length=40)),
                ("button_url", models.CharField(default="/#products", max_length=200)),
                ("active", models.BooleanField(default=True)),
                ("sort_order", models.PositiveIntegerField(default=0)),
            ],
            options={"ordering": ("sort_order", "-id")},
        ),
        migrations.AlterField("item", "price", models.DecimalField(decimal_places=2, max_digits=12)),
        migrations.AlterField("item", "image", models.ImageField(upload_to="products/")),
        migrations.AlterField("item", "discount_price", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
        migrations.AlterField("item", "slug", models.SlugField(unique=True)),
        migrations.AddField("item", "stock", models.PositiveIntegerField(default=10)),
        migrations.AddField("item", "featured", models.BooleanField(default=False)),
        migrations.AddField("item", "active", models.BooleanField(default=True)),
        migrations.AddField("item", "created_at", models.DateTimeField(auto_now_add=True, default=timezone.now), preserve_default=False),
        migrations.AddField("item", "updated_at", models.DateTimeField(auto_now=True, default=timezone.now), preserve_default=False),
        migrations.AlterField("item", "label", models.CharField(choices=[("P","New"),("S","Trending"),("D","Sale")], default="P", max_length=1)),
        migrations.AlterField("coupon", "amount", models.DecimalField(decimal_places=2, max_digits=10)),
        migrations.AlterField("coupon", "code", models.CharField(max_length=20, unique=True)),
        migrations.AlterField("order", "ref_code", models.CharField(blank=True, max_length=24, null=True, unique=True)),
        migrations.AddField("order", "status", models.CharField(choices=[
            ("pending","Payment pending"),("confirmed","Confirmed"),("processing","Processing"),
            ("shipping","Out for delivery"),("delivered","Delivered"),("cancelled","Cancelled")
        ], default="pending", max_length=20)),
        migrations.AlterField("payment", "stripe_charge_id", models.CharField(blank=True, max_length=50)),
        migrations.AddField("payment", "provider", models.CharField(choices=[("esewa","eSewa"),("khalti","Khalti")], default="khalti", max_length=10)),
        migrations.AddField("payment", "status", models.CharField(choices=[("pending","Pending"),("completed","Completed"),("failed","Failed"),("refunded","Refunded")], default="pending", max_length=12)),
        migrations.AddField("payment", "transaction_id", models.CharField(blank=True, max_length=100)),
        migrations.AddField("payment", "gateway_reference", models.CharField(blank=True, max_length=120)),
        migrations.AddField("payment", "gateway_response", models.JSONField(blank=True, default=dict)),
        migrations.AddField("payment", "updated_at", models.DateTimeField(auto_now=True, default=timezone.now), preserve_default=False),
        migrations.RunPython(seed_slides, migrations.RunPython.noop),
        migrations.RunPython(normalize_legacy_payments, migrations.RunPython.noop),
    ]
