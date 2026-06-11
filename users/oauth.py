from urllib.parse import urlencode

import requests
from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


def get_jwt_tokens(user: User) -> dict[str, str]:
    """Генерация пары JWT-токенов для пользователя.

    Args:
        user: Пользователь, для которого выпускаются токены.

    Returns:
        Словарь с ключами ``access`` и ``refresh``.
    """
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


def get_or_create_oauth_user(email: str, first_name: str, last_name: str, provider: str) -> User:
    """Найти или создать пользователя по email из OAuth-провайдера.

    Args:
        email: Email из ответа провайдера.
        first_name: Имя пользователя.
        last_name: Фамилия пользователя.
        provider: Название провайдера (``google`` / ``vk``).

    Returns:
        Существующий либо вновь созданный пользователь.
    """
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        user = User.objects.create_user(
            email=email,
            first_name=first_name or '',
            last_name=last_name or '',
            password=None,
        )
    return user


class GoogleLoginView(APIView):
    """Редирект на страницу авторизации Google."""

    permission_classes = [AllowAny]

    def get(self, request: Request) -> HttpResponseRedirect:
        """Формирует URL авторизации Google и перенаправляет на него."""
        params = {
            'client_id': settings.GOOGLE_CLIENT_ID,
            'redirect_uri': settings.GOOGLE_REDIRECT_URI,
            'response_type': 'code',
            'scope': 'openid email profile',
            'access_type': 'offline',
            'prompt': 'select_account',
        }
        url = f'https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}'
        return redirect(url)


class GoogleCallbackView(APIView):
    """Обработка callback от Google: обмен кода на токен и выдача JWT."""

    permission_classes = [AllowAny]

    def get(self, request: Request) -> HttpResponseRedirect:
        """Обменивает код авторизации на профиль Google и выдаёт JWT.

        Args:
            request: HTTP-запрос с параметрами ``code`` либо ``error``.

        Returns:
            Редирект на страницу входа (при ошибке) или на страницу
            завершения входа с токенами.
        """
        code = request.query_params.get('code')
        error = request.query_params.get('error')

        if error or not code:
            return redirect('/login/?error=google_denied')

        token_resp = requests.post(
            'https://oauth2.googleapis.com/token',
            data={
                'code': code,
                'client_id': settings.GOOGLE_CLIENT_ID,
                'client_secret': settings.GOOGLE_CLIENT_SECRET,
                'redirect_uri': settings.GOOGLE_REDIRECT_URI,
                'grant_type': 'authorization_code',
            },
            timeout=10,
        )

        if token_resp.status_code != 200:
            return redirect('/login/?error=google_token')

        access_token = token_resp.json().get('access_token')

        user_resp = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10,
        )

        if user_resp.status_code != 200:
            return redirect('/login/?error=google_profile')

        data = user_resp.json()
        email = data.get('email')
        if not email:
            return redirect('/login/?error=google_no_email')

        user = get_or_create_oauth_user(
            email=email,
            first_name=data.get('given_name', ''),
            last_name=data.get('family_name', ''),
            provider='google',
        )

        tokens = get_jwt_tokens(user)
        return redirect(
            f'/login/callback/?access={tokens["access"]}&refresh={tokens["refresh"]}'
        )


class VKLoginView(APIView):
    """Редирект на страницу авторизации ВКонтакте."""

    permission_classes = [AllowAny]

    def get(self, request: Request) -> HttpResponseRedirect:
        """Формирует URL авторизации ВКонтакте и перенаправляет на него."""
        params = {
            'client_id': settings.VK_CLIENT_ID,
            'redirect_uri': settings.VK_REDIRECT_URI,
            'display': 'page',
            'scope': 'email',
            'response_type': 'code',
            'v': '5.131',
        }
        url = f'https://oauth.vk.com/authorize?{urlencode(params)}'
        return redirect(url)


class VKCallbackView(APIView):
    """Обработка callback от ВКонтакте: обмен кода на токен и выдача JWT."""

    permission_classes = [AllowAny]

    def get(self, request: Request) -> HttpResponseRedirect:
        """Обменивает код авторизации на профиль ВКонтакте и выдаёт JWT.

        Args:
            request: HTTP-запрос с параметрами ``code`` либо ``error``.

        Returns:
            Редирект на страницу входа (при ошибке) или на страницу
            завершения входа с токенами.
        """
        code = request.query_params.get('code')
        error = request.query_params.get('error')

        if error or not code:
            return redirect('/login/?error=vk_denied')

        token_resp = requests.get(
            'https://oauth.vk.com/access_token',
            params={
                'client_id': settings.VK_CLIENT_ID,
                'client_secret': settings.VK_CLIENT_SECRET,
                'redirect_uri': settings.VK_REDIRECT_URI,
                'code': code,
            },
            timeout=10,
        )

        if token_resp.status_code != 200:
            return redirect('/login/?error=vk_token')

        token_data = token_resp.json()
        access_token = token_data.get('access_token')
        email = token_data.get('email')
        vk_user_id = token_data.get('user_id')

        if not email:
            return redirect('/login/?error=vk_no_email')

        user_resp = requests.get(
            'https://api.vk.com/method/users.get',
            params={
                'user_ids': vk_user_id,
                'fields': 'first_name,last_name',
                'access_token': access_token,
                'v': '5.131',
            },
            timeout=10,
        )

        first_name = ''
        last_name = ''
        if user_resp.status_code == 200:
            users_data = user_resp.json().get('response', [])
            if users_data:
                first_name = users_data[0].get('first_name', '')
                last_name = users_data[0].get('last_name', '')

        user = get_or_create_oauth_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            provider='vk',
        )

        tokens = get_jwt_tokens(user)
        return redirect(
            f'/login/callback/?access={tokens["access"]}&refresh={tokens["refresh"]}'
        )
