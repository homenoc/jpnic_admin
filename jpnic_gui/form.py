import datetime

from django import forms
from django.db.models import Q

from jpnic_gui.result.models import V4List, V6List


class SearchForm(forms.Form):
    addr_type = forms.BooleanField(
        label='IPv6',
        initial=0,
        required=False,
    )

    address = forms.CharField(
        label="住所/住所(English)(一部含む)",
        required=False,
    )

    select_date = forms.DateField(
        label='データ日時',
        input_formats=['%Y-%m-%d'],
        initial=datetime.date.today,
        widget=forms.DateTimeInput(format='%Y-%m-%d'),
        required=False
    )

    def get_queryset(self):
        if not self.is_valid():
            return V4List.objects.all()

        cleaned_data = self.cleaned_data

        # 条件
        conditions = {}

        select_date = cleaned_data.get('select_date')
        addr_type = cleaned_data.get('addr_type')
        address = cleaned_data.get('address')

        if addr_type == "v6":
            conditions["is_ipv6"] = True
        q = Q(**conditions)

        # 住所/住所(English)一部含むフィルタ
        if address != "":
            q &= Q(address__contains=address) | Q(address_en__contains=address)

        # 日付フィルタ
        # フィルタなし時現在の日付にする
        if select_date is None:
            select_date = datetime.date.today()
        if select_date is not None:
            q &= Q(get_date__gte=select_date) & Q(get_date__lte=select_date + datetime.timedelta(days=1))

        if addr_type:
            return V6List.objects.select_related('admin_jpnic').prefetch_related('tech_jpnic').filter(q)
        else:
            return V4List.objects.select_related('admin_jpnic').prefetch_related('tech_jpnic').filter(q)
