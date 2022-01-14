from django.contrib import admin
from django.conf import settings

from jpnic_gui.models import JPNIC

admin.site.site_title = settings.SITE_TITLE
admin.site.site_header = settings.SITE_HEADER
admin.site.index_title = 'メニュー'


# admin.site.login_template = "measure/admin/login.html"


@admin.register(JPNIC)
class JPNICAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "is_active",
        "is_ipv6",
        "asn",
        "ca_path",
        "cert_path",
        "key_path"
    )
    list_filter = ("is_active",)
    search_fields = ("name",)
