#!/usr/bin/env python
"""
Quick management scripts for Hamro Sports store.
Run these commands from Django shell:
  python manage.py shell < helpful_commands.py
"""

from core.models import Item, HeroSlide, Category
from decimal import Decimal

print("=" * 60)
print("HAMRO SPORTS - MANAGEMENT COMMANDS")
print("=" * 60)

# Show store statistics
print("\n📊 STORE STATISTICS")
print("-" * 60)
total_items = Item.objects.count()
active_items = Item.objects.filter(active=True).count()
featured_items = Item.objects.filter(featured=True).count()
on_sale = Item.objects.filter(discount_price__isnull=False).count()

print(f"Total Items: {total_items}")
print(f"Active Items: {active_items}")
print(f"Featured Items: {featured_items}")
print(f"Items on Sale: {on_sale}")

# Show categories
print("\n🏷️  ITEMS BY CATEGORY")
print("-" * 60)
categories = {
    "FB": "Football / Soccer",
    "BK": "Basketball",
    "TN": "Tennis & Racket Sports",
    "RN": "Running & Fitness",
    "OW": "Outdoor & Hiking",
    "AP": "Sports Apparel & Accessories",
}

for code, name in categories.items():
    count = Item.objects.filter(category=code, active=True).count()
    print(f"  {name}: {count}")

# Show pricing statistics
print("\n💰 PRICING STATISTICS")
print("-" * 60)
avg_price = Item.objects.filter(active=True).values('price').average() or 0
min_price = Item.objects.filter(active=True).values('price').order_by('price').first()
max_price = Item.objects.filter(active=True).values('price').order_by('-price').first()

print(f"Average Price: ₹{avg_price:.2f}")
print(f"Cheapest Item: ₹{min_price['price'] if min_price else 0:.2f}")
print(f"Most Expensive: ₹{max_price['price'] if max_price else 0:.2f}")

# Show featured items
print("\n⭐ FEATURED ITEMS (Homepage Display)")
print("-" * 60)
featured = Item.objects.filter(featured=True, active=True)[:8]
for item in featured:
    print(f"  • {item.title} ({item.category}) - ₹{item.current_price}")

# Show hero slides
print("\n🎬 HERO CAROUSEL SLIDES")
print("-" * 60)
slides = HeroSlide.objects.filter(active=True).order_by('sort_order')
for i, slide in enumerate(slides, 1):
    has_image = "✓" if slide.image else "✗"
    print(f"  {i}. {slide.title} [{has_image}]")

# Show low stock items
print("\n⚠️  LOW STOCK ITEMS (< 10)")
print("-" * 60)
low_stock = Item.objects.filter(active=True, stock__lt=10).order_by('stock')
if low_stock.exists():
    for item in low_stock:
        print(f"  • {item.title}: {item.stock} remaining")
else:
    print("  All items well stocked!")

# Useful commands reference
print("\n" + "=" * 60)
print("USEFUL DJANGO SHELL COMMANDS")
print("=" * 60)

commands = """
# Add a featured flag to items
from core.models import Item
Item.objects.filter(category='FB').update(featured=True)

# Mark items on sale
Item.objects.filter(pk__in=[1,2,3]).update(label='D')

# Disable all products
Item.objects.all().update(active=False)

# Update stock for a category
Item.objects.filter(category='BK').update(stock=20)

# Find products by brand
Item.objects.filter(brand='Nike').count()

# Deactivate hero slides
from core.models import HeroSlide
HeroSlide.objects.filter(title='Old Slide').update(active=False)

# Get total inventory value
sum(item.current_price * item.stock for item in Item.objects.all())
"""

print(commands)
