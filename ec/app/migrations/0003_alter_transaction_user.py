from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_product_additional_images_product_brand_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transaction',
            name='buyer',
        ),
        migrations.RemoveField(
            model_name='transaction',
            name='seller',
        ),
        migrations.AddField(
            model_name='transaction',
            name='user',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='auth.user'),
            preserve_default=False,
        ),
    ] 