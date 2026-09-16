# Отчёт по лабораторной работе 6
## Файлы и формирование PDF в Django

### Цель работы
Реализовать хранение файла товара и генерацию PDF через административное действие.

### Файловые поля
Product содержит ImageField image, URLField image_url и FileField specification_file. Файл спецификации загружается в product-specifications/. ModelForm принимает его через request.FILES; HTML-форма использует multipart/form-data.

FileField сохраняет ссылку на файл, а не его содержимое в отдельной колонке модели. MEDIA_ROOT задаёт каталог хранения, MEDIA_URL — URL-префикс. При DEBUG маршруты включают локальную раздачу media средствами Django.

### PDF-действие
В ProductAdmin подключён export_specs_pdf. Оно принимает QuerySet выделенных товаров и формирует ответ:
~~~python
response = HttpResponse(content_type='application/pdf')
response['Content-Disposition'] = (
    'attachment; filename="product-specifications.pdf"'
)
pdf = canvas.Canvas(response)
~~~

Для каждого товара в PDF записываются артикул, название, остаток и базовая цена. При достижении нижней границы листа создаётся новая страница. После pdf.save() ответ возвращается браузеру как скачиваемый документ.

Используется стандартный шрифт ReportLab: поддержка кириллицы и перенос длинных названий требуют отдельной настройки. Поэтому наличие генератора не равнозначно проверке качества всех русскоязычных PDF.

### Локализация и кэш
LANGUAGE_CODE установлен в ru-ru, TIME_ZONE — Europe/Moscow, USE_I18N и USE_TZ включены. Подключён LocMemCache. При этом отдельное кэшируемое представление не реализовано: настройки backend лишь предоставляют инфраструктуру.

### Результат и вывод
В товарную модель добавлен файл спецификации, в админку — действие генерации PDF. Миграция Product применена согласно showmigrations. Проверка Django не обнаружила ошибок конфигурации. Отдельный тест содержимого PDF и применения кэша не зафиксирован.

### Файлы реализации
products/models.py, products/forms.py, products/admin.py, templates/products/manage_form.html, kubkubych/settings.py и kubkubych/urls.py.
