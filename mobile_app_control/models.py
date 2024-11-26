import os
from django.db import models
from django.core.files.storage import default_storage

class MobileAppVersion(models.Model):
    version = models.CharField(max_length=20)
    build_number = models.CharField(max_length=20)
    force_to_update = models.BooleanField(default=True)
    remove_cache_on_update = models.BooleanField(default=False)
    remove_data_on_update = models.BooleanField(default=False)
    remove_cache_and_data_on_update = models.BooleanField(default=False)
    main_file = models.FileField(upload_to='apks/')
    x86_64_file = models.FileField(upload_to='apks/', blank=True, null=True)
    armeabi_v7a_file = models.FileField(upload_to='apks/', blank=True, null=True)
    arm64_v8a_file = models.FileField(upload_to='apks/', blank=True, null=True)
    upload_date = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Keep only one object in the database
        if MobileAppVersion.objects.exists():
            existing = MobileAppVersion.objects.first()
            if existing.pk != self.pk:
                # Delete existing files if different
                for field in ['main_file', 'x86_64_file', 'armeabi_v7a_file', 'arm64_v8a_file']:
                    old_file = getattr(existing, field)
                    new_file = getattr(self, field)
                    if old_file and old_file.name != (new_file.name if new_file else None):
                        if default_storage.exists(old_file.name):
                            default_storage.delete(old_file.name)
                # Update the existing record instead of creating a new one
                self.pk = existing.pk

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Mobile App Version {self.version} (Build {self.build_number})"
    
    class Meta:
        db_table = "rdl_odms_mobile_app"
        verbose_name = "ODMS Mobile App"
        verbose_name_plural = "ODMS Mobile App"

