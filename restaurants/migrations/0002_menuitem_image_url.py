from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("restaurants", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="menuitem",
            name="image_url",
            field=models.URLField(blank=True, max_length=500),
        ),
    ]
