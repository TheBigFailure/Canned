# Generated by Django 5.1.1 on 2024-10-03 11:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('candb', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='phone',
            field=models.CharField(blank=True, help_text='Phone Number', max_length=22, null=True),
        ),
    ]
