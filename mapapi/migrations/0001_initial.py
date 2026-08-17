import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Spot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('lat', models.FloatField()),
                ('lng', models.FloatField()),
                ('main_image', models.ImageField(blank=True, null=True, upload_to='spots/main/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Photo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='spots/gallery/')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved')], default='pending', max_length=10)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('spot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='photos', to='mapapi.spot')),
            ],
            options={
                'ordering': ['uploaded_at'],
            },
        ),
    ]
