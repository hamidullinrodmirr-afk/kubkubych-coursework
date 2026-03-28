from django.views.generic import TemplateView


class IndexView(TemplateView):
    template_name = 'index.html'


class DoctorListView(TemplateView):
    template_name = 'doctors/list.html'


class DoctorDetailView(TemplateView):
    template_name = 'doctors/detail.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['doctor_id'] = kwargs['pk']
        return ctx


class ServiceListView(TemplateView):
    template_name = 'services/list.html'


class AppointmentCreateView(TemplateView):
    template_name = 'appointments/create.html'


class LoginView(TemplateView):
    template_name = 'auth/login.html'


class RegisterView(TemplateView):
    template_name = 'auth/register.html'


class ProfileView(TemplateView):
    template_name = 'profile/index.html'


class OAuthCallbackView(TemplateView):
    template_name = 'auth/oauth_callback.html'
