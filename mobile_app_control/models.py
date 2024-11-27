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

    def delete_old_files(self):
        """Deletes old files from storage if they are being replaced."""
        if self.pk:  # Check if the object already exists
            existing = MobileAppVersion.objects.filter(pk=self.pk).first()
            if existing:
                for field_name in ['main_file', 'x86_64_file', 'armeabi_v7a_file', 'arm64_v8a_file']:
                    old_file = getattr(existing, field_name)
                    new_file = getattr(self, field_name)
                    if old_file and (not new_file or old_file.name != new_file.name):
                        if default_storage.exists(old_file.name):
                            default_storage.delete(old_file.name)

    def save(self, *args, **kwargs):
        # Ensure only one instance exists in the database
        if MobileAppVersion.objects.exists() and not self.pk:
            MobileAppVersion.objects.exclude(pk=self.pk).delete()

        # Delete old files before saving the new instance
        self.delete_old_files()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Delete associated files when the object is deleted."""
        for field_name in ['main_file', 'x86_64_file', 'armeabi_v7a_file', 'arm64_v8a_file']:
            file = getattr(self, field_name)
            if file and default_storage.exists(file.name):
                default_storage.delete(file.name)
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Mobile App Version {self.version} (Build {self.build_number})"
    
    class Meta:
        db_table = "rdl_odms_mobile_app"
        verbose_name = "ODMS Mobile App"
        verbose_name_plural = "ODMS Mobile App"

