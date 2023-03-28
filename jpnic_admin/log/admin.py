from django.contrib import admin

from jpnic_admin.log.models import Task, TaskError


@admin.register(Task)
class Task(admin.ModelAdmin):
    list_display = ("id", "created_at", "last_checked_at", "jpnic_id", "type1", "count", "fail_count")
    list_filter = ("type1",)
    search_fields = ("last_checked_at",)


@admin.register(TaskError)
class TaskError(admin.ModelAdmin):
    list_display = ("id", "created_at", "type", "message")
    list_filter = ()
    search_fields = ("created_at",)
