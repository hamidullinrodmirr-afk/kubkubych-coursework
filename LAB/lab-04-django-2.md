# Отчёт по лабораторной работе 4
## ModelForm и управление товарами через сайт

### Цель работы
Реализовать создание, изменение и удаление объекта через HTML-формы Django, обработку файлов и загрузку связанных данных.

### Форма товара
ProductForm наследует ModelForm. В Meta перечислены поля модели, виджеты, подписи, подсказки и сообщения ошибок. Описание выводится Textarea. Дополнительное поле internal_note не относится к модели и не сохраняется как постоянная заметка.

~~~python
def clean_article(self):
    return self.cleaned_data['article'].strip().upper()

def save(self, commit=True):
    product = super().save(commit=False)
    if commit:
        product.save()
        self.save_m2m()
    return product
~~~

clean_article нормализует артикул. commit=False создаёт экземпляр без записи в базу, commit=True сохраняет его. В модели Product.save формируется slug, если он не задан.

### Обработка запроса
~~~python
form = ProductForm(request.POST or None, request.FILES or None)
if request.method == 'POST' and form.is_valid():
    product = form.save(commit=True)
    messages.success(request, f'Набор «{product.name}» создан.')
    return HttpResponseRedirect(reverse('product-manage-list'))
~~~

request.POST содержит обычные поля, request.FILES — загруженные файлы. После сохранения применяется перенаправление, что уменьшает вероятность повторной отправки формы при обновлении страницы.

Редактирование передаёт существующий объект через instance. Удаление выполняется только после POST страницы подтверждения. Если на товар ссылаются защищённые позиции заказа, политика PROTECT может запретить удаление; отдельная обработка этой ошибки в HTML-представлении не реализована.

### Оптимизация и библиотеки
select_related используется для ForeignKey серии. prefetch_related и Prefetch применяются в API при детальной выдаче отзывов. Для профилирования подключён django-debug-toolbar. Связь Product–User задана через ManyToManyField с промежуточной Favorite.

### Результат и вывод
Созданы маршруты списка, добавления, изменения и удаления под /manage/products/. Представления требуют сессионную авторизацию и роль admin. Реализована валидация формы и приём файлов. Проверка конфигурации Django проходит без ошибок; фактический браузерный CRUD не выдаётся в отчёте за проведённый тест.

### Файлы реализации
products/forms.py, products/site_views.py, products/site_urls.py и templates/products/.
