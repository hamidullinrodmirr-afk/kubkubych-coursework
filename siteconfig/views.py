from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsAdmin
from .models import SiteSetting
from .serializers import SiteSettingSerializer


class SiteSettingView(APIView):
    """GET — публичные настройки магазина; PATCH — изменение администратором."""

    def get_permissions(self):
        return [IsAdmin()] if self.request.method == 'PATCH' else [permissions.AllowAny()]

    def get(self, request):
        return Response(SiteSettingSerializer(SiteSetting.load()).data)

    def patch(self, request):
        serializer = SiteSettingSerializer(SiteSetting.load(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
