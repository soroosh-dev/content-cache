# Generated by Django 4.2.5 on 2023-09-29 13:54

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BaseFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filename', models.CharField(max_length=120)),
                ('creation_time', models.DateTimeField(auto_now_add=True)),
                ('last_update_time', models.DateTimeField(auto_now=True)),
                ('size', models.IntegerField()),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='cachedfiles', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='TextFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('minify', models.BooleanField(default=False)),
                ('minification_time', models.FloatField(blank=True, null=True)),
                ('minification_memory', models.IntegerField(blank=True, null=True)),
                ('base_file', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='txtdetails', to='cachemanager.basefile')),
            ],
        ),
        migrations.CreateModel(
            name='ImageFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('convert_to_webp', models.BooleanField(default=False)),
                ('convertion_time', models.FloatField(blank=True, null=True)),
                ('convertion_memory', models.IntegerField(blank=True, null=True)),
                ('base_file', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='imgdetails', to='cachemanager.basefile')),
            ],
        ),
    ]
