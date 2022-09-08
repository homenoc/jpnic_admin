import datetime

from django import template

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
def to_jst(gmt):
    jst = gmt + datetime.timedelta(hours=9)
    print(gmt + datetime.timedelta(hours=9))
    if not gmt:
        return "取得失敗"
    return jst.strftime("%Y/%m/%d %H:%M(JST)")

