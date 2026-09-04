from django.db import migrations


def seed_hero_slides(apps, schema_editor):
    HeroSlide = apps.get_model('core', 'HeroSlide')
    
    hero_slides = [
        {
            'title': 'Elevate Your Game',
            'subtitle': 'Premium sports equipment for athletes of all levels. From football to fitness, we have everything you need.',
            'button_text': 'Shop Collection',
            'button_url': '/#products',
            'active': True,
            'sort_order': 1,
        },
        {
            'title': 'Train Harder',
            'subtitle': 'Professional-grade fitness gear and equipment to push your limits and achieve your goals.',
            'button_text': 'Explore Fitness',
            'button_url': '/#category-RN',
            'active': True,
            'sort_order': 2,
        },
        {
            'title': 'Play Better',
            'subtitle': 'From football to basketball to tennis - we stock the top brands and latest sports equipment.',
            'button_text': 'Browse Sports',
            'button_url': '/#categories',
            'active': True,
            'sort_order': 3,
        },
        {
            'title': 'Explore The Outdoors',
            'subtitle': 'Hiking, camping and outdoor adventure gear for your next expedition.',
            'button_text': 'Adventure Gear',
            'button_url': '/#category-OW',
            'active': True,
            'sort_order': 4,
        },
        {
            'title': 'Summer Sports Special',
            'subtitle': 'Save up to 40% on premium sports equipment and apparel this season.',
            'button_text': 'View Deals',
            'button_url': '/?label=D',
            'active': True,
            'sort_order': 5,
        },
    ]
    
    for slide_data in hero_slides:
        HeroSlide.objects.get_or_create(
            title=slide_data['title'],
            defaults=slide_data
        )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_seed_sports_items'),
    ]

    operations = [
        migrations.RunPython(seed_hero_slides),
    ]
