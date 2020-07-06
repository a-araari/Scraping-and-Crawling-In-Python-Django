from django.contrib import admin

from .models import tbl_page_data


@admin.register(tbl_page_data)
class tbl_page_dataAdmin(admin.ModelAdmin):
    list_display = ('task_id', 'url', 'status_process', 'pending_task')