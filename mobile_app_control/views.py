from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import MobileAppVersion

def str_to_bool(value):
    return value in ['true', 'True', '1', 'on']
def upload_apk(request):
    if request.method == 'POST':
        # Get or create the single object
        version_instance = MobileAppVersion.objects.first() or MobileAppVersion()
        password = "rdl@odms@Rdl#impala"
        user_password = request.POST.get('password')
        if user_password != password:
            return
        # Update fields
        version_instance.version = request.POST.get('version', '1.0.0')
        version_instance.build_number = request.POST.get('build_number', '1')
        version_instance.force_to_update = str_to_bool(request.POST.get('force_to_update', 'false'))
        version_instance.remove_cache_on_update = str_to_bool(request.POST.get('remove_cache_on_update', 'false'))
        version_instance.remove_data_on_update = str_to_bool(request.POST.get('remove_data_on_update', 'false'))
        version_instance.remove_cache_and_data_on_update = str_to_bool(request.POST.get('remove_cache_and_data_on_update', 'false'))

        # Update files if provided
        if 'main_file' in request.FILES:
            version_instance.main_file = request.FILES['main_file']
        if 'x86_64_file' in request.FILES:
            version_instance.x86_64_file = request.FILES['x86_64_file']
        if 'armeabi_v7a_file' in request.FILES:
            version_instance.armeabi_v7a_file = request.FILES['armeabi_v7a_file']
        if 'arm64_v8a_file' in request.FILES:
            version_instance.arm64_v8a_file = request.FILES['arm64_v8a_file']

        # Save updated information
        version_instance.save()
        return JsonResponse({'message': 'APK updated successfully!'}, status=200)

    # Render the upload form
    return render(request, 'upload_apk.html', {
        'current_version': MobileAppVersion.objects.first()
    })