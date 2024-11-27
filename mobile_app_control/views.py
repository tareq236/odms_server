from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import MobileAppVersion
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

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
    

@api_view(['GET'])
def app_info(request):
    try:
        # Fetch the latest app version data
        version_instance = MobileAppVersion.objects.first()
        if not version_instance:
            return Response({"success": True, "message": "No app version data available."}, status=status.HTTP_404_NOT_FOUND)

        # Prepare the data dynamically
        data = {
            "version": version_instance.version,
            "buildNumber": version_instance.build_number,
            "forceToUpdate": version_instance.force_to_update,
            "removeCacheOnUpdate": version_instance.remove_cache_on_update,
            "removeDataOnUpdate": version_instance.remove_data_on_update,
            "removeCacheAndDataOnUpdate": version_instance.remove_cache_and_data_on_update,
            "downloadLink": request.build_absolute_uri(version_instance.main_file.url) if version_instance.main_file else None,
            "downloadLinkList": [
                {
                    "architecture": "x86_64",
                    "link": request.build_absolute_uri(version_instance.x86_64_file.url) if version_instance.x86_64_file else None
                },
                {
                    "architecture": "armeabi-v7a",
                    "link": request.build_absolute_uri(version_instance.armeabi_v7a_file.url) if version_instance.armeabi_v7a_file else None
                },
                {
                    "architecture": "arm64-v8a",
                    "link": request.build_absolute_uri(version_instance.arm64_v8a_file.url) if version_instance.arm64_v8a_file else None
                }
            ]
        }
        return Response({"success": True, "result": data}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"success": True, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
