from django.db import migrations


def seed_coupon(apps, schema_editor):
    Coupon = apps.get_model('core', 'Coupon')
    Coupon.objects.get_or_create(code='SAVE10', defaults={'amount': 10.0})


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_coupon),
    ]
