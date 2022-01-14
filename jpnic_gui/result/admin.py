from django.contrib import admin

from jpnic_gui.result.models import V4List, V6List, JPNICHandle


@admin.register(V4List)
class V4ListAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "ip_address",
        "network_name",
        "assign_date",
        "org",
        "resource_admin_short",
        "get_date",
        "type",
        "division",
    )
    list_filter = ("type", "division")


@admin.register(V6List)
class V6ListAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "ip_address",
        "network_name",
        "assign_date",
        "org",
        "resource_admin_short",
        "get_date",
        "division",
    )
    list_filter = ("division",)


@admin.register(JPNICHandle)
class JPNICHandleAdmin(admin.ModelAdmin):
    list_display = (
        "jpnic_handle",
        "name",
        "name_en",
        "email",
        "org",
        "org_en",
        "division",
        "division_en",
        "tel",
        "fax",
        "update_date",
    )
    list_filter = ()
