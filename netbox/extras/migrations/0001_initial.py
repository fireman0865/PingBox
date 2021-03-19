# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-06-22 18:21
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dcim', '0002_auto_20160622_1821'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExportTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('template_code', models.TextField()),
                ('mime_type', models.CharField(blank=True, max_length=15)),
                ('file_extension', models.CharField(blank=True, max_length=15)),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
            ],
            options={
                'ordering': ['content_type', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Graph',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.PositiveSmallIntegerField(choices=[(100, b'Interface'), (200, b'Provider'), (300, b'Site')])),
                ('weight', models.PositiveSmallIntegerField(default=1000)),
                ('name', models.CharField(max_length=100, verbose_name=b'Name')),
                ('source', models.CharField(max_length=500, verbose_name=b'Source URL')),
                ('link', models.URLField(blank=True, verbose_name=b'Link URL')),
            ],
            options={
                'ordering': ['type', 'weight', 'name'],
            },
        ),
        migrations.CreateModel(
            name='TopologyMap',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('slug', models.SlugField(unique=True)),
                ('device_patterns', models.TextField(help_text=b'Identify devices to include in the diagram using regular expressions,one per line. Each line will result in a new tier of the drawing. Separate multiple regexes on a line using commas. Devices will be rendered in the order they are defined.')),
                ('description', models.CharField(blank=True, max_length=100)),
                ('site', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='topology_maps', to='dcim.Site')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='UserAction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time', models.DateTimeField(auto_now_add=True)),
                ('object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('action', models.PositiveSmallIntegerField(choices=[(1, b'created'), (2, b'imported'), (3, b'modified'), (4, b'bulk edited'), (5, b'deleted'), (6, b'bulk deleted')])),
                ('message', models.TextField(blank=True)),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='actions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-time'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='exporttemplate',
            unique_together=set([('content_type', 'name')]),
        ),
    ]