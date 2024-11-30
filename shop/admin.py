from django.contrib import admin
from django.utils.html import format_html

from .models import (EmailTemplate)


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['template_name', 'subject', 'created', 'updated']
    search_fields = ['template_name', 'subject', 'html_content', 'text_content']
    readonly_fields = ['created', 'updated']

    fieldsets = (
        (None, {
            'fields': ('template_name', 'subject')
        }),
        ('템플릿 내용', {
            'fields': ('html_content', 'text_content'),
            'classes': ('wide',)
        }),
        ('시스템 정보', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        })
    )

    def preview_html(self, obj):
        return format_html(
            '<iframe srcdoc="{}" width="100%" height="300px"></iframe>',
            obj.html_content
        )

    preview_html.short_description = 'HTML 미리보기'
