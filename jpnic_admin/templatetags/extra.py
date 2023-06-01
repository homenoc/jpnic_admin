import datetime

from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def url_replace(request, **kwargs):
    params = request.GET.copy()
    for k, v in kwargs.items():
        params[k] = v
    return params.urlencode()


@register.simple_tag
def to_int(value):
    if not value:
        return None
    return int(value)


@register.simple_tag
def time_to_str(gmt):
    jst = gmt + datetime.timedelta(hours=0)
    if not gmt:
        return "取得失敗"
    return jst.strftime("%Y/%m/%d %H:%M")


@register.simple_tag
def to_jst(gmt):
    jst = gmt + datetime.timedelta(hours=9)
    if not gmt:
        return "取得失敗"
    return jst.strftime("%Y/%m/%d %H:%M(JST)")


@register.simple_tag
def get_usage(addr_count, total_addr):
    return "{:.2%}".format(addr_count / total_addr)


@register.simple_tag
def get_addr_count(ip_version, addr=None):
    if addr is None:
        return 0
    if ip_version == 4:
        return 2 ** (32 - int(str(addr).split("/")[1]))
    elif ip_version == 6:
        return 2 ** (128 - int(str(addr).split("/")[1]))
    else:
        return 0


@register.simple_tag
def get_resource_notify():
    return str(settings.NOTICE_MINUTE) + " " + str(settings.NOTICE_HOUR) + " " + str(settings.NOTICE_DAY) + " " + str(
        settings.NOTICE_MONTH) + " *"


@register.simple_tag
def beta():
    return settings.BETA
