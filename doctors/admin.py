from django.contrib import admin
from .models import Specialty, Doctor, Schedule


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


class ScheduleInline(admin.TabularInline):
    model = Schedule
    extra = 1


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'experience_years', 'consultation_price', 'is_available')
    list_filter = ('is_available', 'specialties')
    search_fields = ('user__last_name', 'user__first_name', 'user__email')
    filter_horizontal = ('specialties',)
    raw_id_fields = ('user',)
    inlines = [ScheduleInline]

    @admin.display(description='ФИО')
    def get_full_name(self, obj):
        return obj.user.full_name


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'day_of_week', 'start_time', 'end_time', 'slot_duration')
    list_filter = ('day_of_week',)
