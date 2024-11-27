from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from mobile_app_control.models import MobileAppVersion

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