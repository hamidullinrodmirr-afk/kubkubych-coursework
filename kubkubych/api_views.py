from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Простой healthcheck для мониторинга и оркестрации контейнеров."""
    return Response({'status': 'ok'})


@api_view(['GET'])
@permission_classes([AllowAny])
def sentry_test(request):
    """Намеренно бросает исключение для проверки Sentry (только при DEBUG)."""
    if not settings.DEBUG:
        return Response({'detail': 'Эндпоинт доступен только в режиме отладки.'}, status=403)
    raise RuntimeError('Sentry test exception: проверка мониторинга КубКубыч.')
