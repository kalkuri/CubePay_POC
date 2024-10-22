from django.contrib import admin
from .models import Pilgrim

class PilgrimAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'aadhar_number', 'gender', 'phone_number', 'unique_id', 'is_expired', 'valid_until', 'compartment_1', 'compartment_2', 'compartment_3', 'compartment_4')
    search_fields = ('name', 'aadhar_number', 'unique_id')
    list_filter = ('gender', 'valid_until')

    def has_delete_permission(self, request, obj=None):
        # Optionally restrict delete permission
        return False  # Disallow deletion of Pilgrim records

# Register your models here
admin.site.register(Pilgrim, PilgrimAdmin)
