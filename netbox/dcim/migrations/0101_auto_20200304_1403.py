# Generated by Django 2.2.10 on 2020-03-04 14:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dcim', '0100_application'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='acquisition_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='device',
            name='garantee_end_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
