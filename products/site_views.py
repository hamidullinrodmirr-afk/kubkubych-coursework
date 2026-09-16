from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from .forms import ProductForm
from .models import Product


def _is_admin(user):
    return user.is_authenticated and user.role == user.Role.ADMIN


admin_required = user_passes_test(_is_admin, login_url='/admin/login/')


@admin_required
def product_manage_list(request):
    queryset = Product.objects.select_related('category').exclude(is_active=False).order_by('name')
    paginator = Paginator(queryset, 10)
    try:
        products = paginator.page(request.GET.get('page', 1))
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    return render(request, 'products/manage_list.html', {'products': products})


@admin_required
def product_create(request):
    form = ProductForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        product = form.save(commit=True)
        messages.success(request, f'Набор «{product.name}» создан.')
        return HttpResponseRedirect(reverse('product-manage-list'))
    return render(request, 'products/manage_form.html', {'form': form, 'title': 'Добавить набор'})


@admin_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == 'POST' and form.is_valid():
        form.save(commit=True)
        messages.success(request, f'Набор «{product.name}» обновлён.')
        return HttpResponseRedirect(reverse('product-manage-list'))
    return render(request, 'products/manage_form.html', {'form': form, 'title': 'Изменить набор'})


@admin_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f'Набор «{name}» удалён.')
        return HttpResponseRedirect(reverse('product-manage-list'))
    return render(request, 'products/manage_delete.html', {'product': product})
