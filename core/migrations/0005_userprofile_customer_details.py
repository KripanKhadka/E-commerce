from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0004_store_upgrade")]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="full_name",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="phone",
            field=models.CharField(blank=True, max_length=20),
        ),
    ]
