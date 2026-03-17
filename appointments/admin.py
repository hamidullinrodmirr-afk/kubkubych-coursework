from django.contrib import admin
from .models import Appointment, MedicalRecord


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('client', 'doctor', 'pet', 'service', 'date', 'time_slot', 'status')
    list_filter = ('status', 'date')
    search_fields = ('client__last_name', 'client__email', 'doctor__user__last_name')
    raw_id_fields = ('client', 'doctor', 'pet', 'service')
    date_hierarchy = 'date'


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ('pet', 'doctor', 'diagnosis_short', 'created_at')
    search_fields = ('diagnosis', 'pet__name', 'doctor__user__last_name')
    raw_id_fields = ('appointment', 'pet', 'doctor')

    @admin.display(description='Диагноз')
    def diagnosis_short(self, obj):
        return obj.diagnosis[:80] + '...' if len(obj.diagnosis) > 80 else obj.diagnosis
