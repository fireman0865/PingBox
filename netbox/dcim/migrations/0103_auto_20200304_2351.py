# Generated by Django 2.2.10 on 2020-03-04 23:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dcim', '0102_applicationtype'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='application',
            options={'ordering': ['name', 'slug', 'platform', 'application_type', 'database', 'virtual_machine', 'language', 'environnement', 'version', 'application_team', 'link', 'application_maintainer', 'profilepardefaut', 'actualprofile']},
        ),
        migrations.AddField(
            model_name='application',
            name='application_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='application_type', to='dcim.ApplicationType'),
        ),
    ]
