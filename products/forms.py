from django import forms

from .models import Product


class ProductForm(forms.ModelForm):
    """Форма управления набором для демонстрации CRUD в интерфейсе магазина."""

    internal_note = forms.CharField(
        label='Примечание для администратора',
        required=False,
        help_text='Служебная заметка не публикуется в карточке набора.',
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Например, проверить поставку'}),
    )

    class Meta:
        model = Product
        fields = (
            'category', 'name', 'article', 'description', 'age_from', 'age_to', 'pieces',
            'price', 'discount_percent', 'stock', 'image', 'specification_file', 'image_url', 'is_active',
        )
        labels = {'image_url': 'Ссылка на запасное изображение'}
        help_texts = {'specification_file': 'PDF или другой файл с характеристиками набора.'}
        error_messages = {'article': {'unique': 'Набор с таким артикулом уже существует.'}}
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'price': forms.NumberInput(attrs={'min': '1', 'step': '0.01'}),
            'discount_percent': forms.NumberInput(attrs={'min': '0', 'max': '80'}),
        }

    class Media:
        css = {'all': ('css/style.css',)}

    def clean_article(self):
        return self.cleaned_data['article'].strip().upper()

    def save(self, commit=True):
        product = super().save(commit=False)
        if commit:
            product.save()
            self.save_m2m()
        return product
