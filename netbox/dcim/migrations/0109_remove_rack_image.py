# Generated by Django 2.2.10 on 2020-03-13 07:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dcim', '0108_rack_image'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='rack',
            name='image',
        ),
    ]