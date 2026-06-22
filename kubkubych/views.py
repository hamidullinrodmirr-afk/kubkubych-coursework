from typing import Any

from django.views.generic import TemplateView


class IndexView(TemplateView):
    template_name = 'index.html'


class CatalogView(TemplateView):
    template_name = 'catalog/list.html'


class ProductDetailView(TemplateView):
    template_name = 'catalog/detail.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['product_id'] = kwargs['pk']
        return context


class CartView(TemplateView):
    template_name = 'cart/index.html'


class CheckoutView(TemplateView):
    template_name = 'orders/checkout.html'


class AboutView(TemplateView):
    template_name = 'pages/about.html'


class MissionView(TemplateView):
    template_name = 'pages/mission.html'


class DeliveryView(TemplateView):
    template_name = 'pages/delivery.html'


class LoginView(TemplateView):
    template_name = 'auth/login.html'


class RegisterView(TemplateView):
    template_name = 'auth/register.html'


class ProfileView(TemplateView):
    template_name = 'profile/index.html'


class OAuthCallbackView(TemplateView):
    template_name = 'auth/oauth_callback.html'
