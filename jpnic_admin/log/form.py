from django import forms
from django.db.models import Q

from jpnic_admin.log.models import Task
from jpnic_admin.models import JPNIC as JPNICModel


class SearchForm(forms.Form):
    NONE = "NONE"
    RESOURCE = "資源情報"
    RESOURCE_ADDRESS = "アドレス情報"
    FILTER_TYPE1 = [
        (NONE, "すべて"),
        (RESOURCE, "資源情報"),
        (RESOURCE_ADDRESS, "アドレス情報"),
    ]

    jpnic_id = forms.ModelChoiceField(
        label="JPNIC証明書",
        queryset=JPNICModel.objects,
        required=True
    )

    type1 = forms.TypedChoiceField(
        label="種類",
        choices=FILTER_TYPE1,
        initial=NONE,
        empty_value=NONE,
        show_hidden_initial=False,
    )

    start_time = forms.DateTimeField(
        label="開始時間",
        input_formats=["%Y-%m-%dT%H:%M:%SZ"],
        widget=forms.DateTimeInput(format="%Y-%m-%dT%H:%M:%SZ"),
        required=False,
    )
    end_time = forms.DateTimeField(
        label="終了時間",
        input_formats=["%Y-%m-%dT%H:%M:%SZ"],
        widget=forms.DateTimeInput(format="%Y-%m-%dT%H:%M:%SZ"),
        required=False,
    )

    def get_queryset(self):
        if not self.is_valid():
            return Task.objects.all()

        cleaned_data = self.cleaned_data

        # 条件
        conditions = {}
        q = Q(**conditions)

        jpnic_id = cleaned_data.get("jpnic_id")
        type1 = cleaned_data.get("type1")
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if not type1 or not type1 == "NONE":
            q &= Q(type1=type1)

        if not jpnic_id:
            q &= Q(jpnic_id=jpnic_id)

        # 開始時間と終了時間のフィルタ
        if start_time is not None:
            q &= ~Q(end_at__lt=start_time)
        if end_time is not None:
            q &= ~Q(start_at__gt=end_time)

        return Task.objects.filter(q)
