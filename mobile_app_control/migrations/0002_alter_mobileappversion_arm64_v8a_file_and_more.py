# Generated by Django 5.1.1 on 2024-12-26 10:26

import mobile_app_control.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mobile_app_control', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mobileappversion',
            name='arm64_v8a_file',
            field=models.FileField(blank=True, null=True, upload_to=mobile_app_control.models.DynamicFilePath('arm64-v8a')),
        ),
        migrations.AlterField(
            model_name='mobileappversion',
            name='armeabi_v7a_file',
            field=models.FileField(blank=True, null=True, upload_to=mobile_app_control.models.DynamicFilePath('armeabi-v7a')),
        ),
        migrations.AlterField(
            model_name='mobileappversion',
            name='main_file',
            field=models.FileField(upload_to=mobile_app_control.models.DynamicFilePath('main-app')),
        ),
        migrations.AlterField(
            model_name='mobileappversion',
            name='x86_64_file',
            field=models.FileField(blank=True, null=True, upload_to=mobile_app_control.models.DynamicFilePath('x86_64')),
        ),
    ]
