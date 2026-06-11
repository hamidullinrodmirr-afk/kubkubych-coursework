from typing import Any

from django.views.generic import TemplateView


class IndexView(TemplateView):
    """Главная страница."""

    template_name = 'index.html'


class DoctorListView(TemplateView):
    """Каталог врачей."""

    template_name = 'doctors/list.html'


class DoctorDetailView(TemplateView):
    """Страница врача."""

    template_name = 'doctors/detail.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Добавляет идентификатор врача в контекст шаблона.

        Args:
            **kwargs: Параметры URL-маршрута.

        Returns:
            Контекст шаблона с ключом ``doctor_id``.
        """
        ctx = super().get_context_data(**kwargs)
        ctx['doctor_id'] = kwargs['pk']
        return ctx


class ServiceListView(TemplateView):
    """Каталог услуг."""

    template_name = 'services/list.html'


class AppointmentCreateView(TemplateView):
    """Мастер записи на приём."""

    template_name = 'appointments/create.html'


class LoginView(TemplateView):
    """Страница входа."""

    template_name = 'auth/login.html'


class RegisterView(TemplateView):
    """Страница регистрации."""

    template_name = 'auth/register.html'


class ProfileView(TemplateView):
    """Личный кабинет."""

    template_name = 'profile/index.html'


class OAuthCallbackView(TemplateView):
    """Страница завершения входа через OAuth."""

    template_name = 'auth/oauth_callback.html'
