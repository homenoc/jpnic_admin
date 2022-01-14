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

    # select_time = forms.DateField(
    #     label='データ日時',
    #     input_formats=['%Y-%m-%d'],
    #     widget=forms.DateTimeInput(format='%Y-%m-%d'),
    #     required=False
    # )

    def get_queryset(self):
        if not self.is_valid():
            return V4List.objects.all()

        cleaned_data = self.cleaned_data

        # 条件
        conditions = {}

        select_time = cleaned_data.get('select_time')
        addr_type = cleaned_data.get('addr_type')
        address = cleaned_data.get('address')
        disp_filter = cleaned_data.get('display_filter')

        if addr_type == "v6":
            conditions["is_ipv6"] = True
        q = Q(**conditions)

        print(address)
        # 住所/住所(English)一部含むフィルタ
        if address != "":
            q &= Q(address__contains=address) | Q(address_en__contains=address)

        # のフィルタ
        if select_time is not None:
            q &= ~Q(start_at__gt=select_time)

        if addr_type == True:
            return V6List.objects.select_related('admin_jpnic').prefetch_related('tech_jpnic').filter(q)
        else:
            return V4List.objects.select_related('admin_jpnic').prefetch_related('tech_jpnic').filter(q)
