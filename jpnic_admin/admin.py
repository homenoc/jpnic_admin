from django.contrib import admin
from django.conf import settings

from jpnic_admin.models import JPNIC

admin.site.site_title = settings.SITE_TITLE
admin.site.site_header = settings.SITE_HEADER
admin.site.index_title = 'メニュー'


@admin.register(JPNIC)
class JPNICAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "is_active",
        "is_ipv6",
        "asn",
        "ada",
        "collection_interval",
        "p12_base64",
        "p12_pass"
    )
    list_filter = ("is_active",)
    search_fields = ("name",)
