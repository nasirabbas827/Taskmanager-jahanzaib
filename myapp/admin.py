from django.contrib import admin
from .models import User , Task

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'role', 'created_at', 'updated_at')
    list_filter = ('role', 'created_at')
    search_fields = ('name', 'email')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (None, {
            'fields': ('name', 'email', 'password_hash', 'role')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

admin.site.register(Task)