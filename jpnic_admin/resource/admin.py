from django.contrib import admin

from jpnic_admin.resource.models import AddrList, JPNICHandle


@admin.register(AddrList)
class AddrListAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "last_checked_at",
        "ip_address",
        "network_name",
        "assign_date",
        "org",
        "resource_admin_short",
        "type",
        "division",
    )
    list_filter = ("type", "division")
    search_fields = ("last_checked_at",)


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
    )
    list_filter = ()
    search_fields = ("last_checked_at",)
