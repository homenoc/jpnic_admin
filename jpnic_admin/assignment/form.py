from django import forms
from jpnic_admin.models import JPNIC as JPNICModel


class AddAssignment(forms.Form):
    jpnic_id = forms.ModelChoiceField(
        label="JPNIC証明書",
        queryset=JPNICModel.objects,
        required=True
    )

    ip_address = forms.CharField(
        label="IPアドレス",
        required=True,
    )

    network_name = forms.CharField(
        label="ネットワーク名",
        required=True,
    )

    org = forms.CharField(
        label="組織名",
        required=True,
    )

    org_en = forms.CharField(
        label="組織名(English)",
        required=True,
    )

    zipcode = forms.CharField(
        label="郵便番号",
        min_length=8,
        max_length=8,
        required=True,
    )

    address = forms.CharField(
        label="住所",
        required=True,
    )

    address_en = forms.CharField(
        label="住所(English)",
        required=True,
    )

    admin_handle = forms.CharField(
        label="管理者連絡窓口",
        required=False,
    )

    tech_handle = forms.CharField(
        label="技術連絡担当者",
        required=False,
    )

    abuse = forms.CharField(
        label="Abuse",
        required=False,
    )

    plan_data = forms.CharField(
        label="Plan",
        required=False,
        widget=forms.Textarea()
    )

    deli_no = forms.CharField(
        label="審議番号",
        required=False,
    )

    return_date = forms.DateField(
        label="返却年月日",
        input_formats=["%Y/%m/%d"],
        # initial=datetime.date.today,
        widget=forms.DateTimeInput(format="%Y/%m/%d"),
        required=False,
    )

    apply_from_email = forms.EmailField(
        label="申請者メールアドレス",
        required=False,
    )

    def clean(self):
        cleaned_data = super().clean()
        network_name = cleaned_data.get("network_name")
        org = cleaned_data.get("org")
        org_en = cleaned_data.get("org_en")
        postcode = cleaned_data.get("postcode")
        address = cleaned_data.get("address")
        address_en = cleaned_data.get("address_en")
        name_server = cleaned_data.get("name_server")
        deli_no = cleaned_data.get("deli_no")
        return_date = cleaned_data.get("return_date")
        apply_email = cleaned_data.get("apply_email")

        # if network_name and org and org_en and postcode and address and address_en:
    #         raise ValidationError("Did not send for 'help' in the subject despite " "CC'ing yourself.")


class SearchForm(forms.Form):
    KIND_CHOICE = [(1, "割振"), (2, "ユーザ割当"), (3, "インフラ割当"), (4, "SUBA")]

    jpnic_id = forms.ModelChoiceField(
        label="JPNIC証明書",
        queryset=JPNICModel.objects,
        required=True
    )

    ip_address = forms.CharField(
        label="IPアドレス",
        required=True,
    )

    kind = forms.ChoiceField(
        label="種別",
        choices=KIND_CHOICE,
        required=True,
    )


class SearchChangeAssignmentForm(forms.Form):
    KIND_CHOICE = [(0, "割り当て"), (2, "SUBA登録"), (3, "歴史的PI")]

    jpnic_id = forms.ModelChoiceField(
        label="JPNIC証明書",
        queryset=JPNICModel.objects,
        required=True
    )

    ip_address = forms.CharField(
        label="IPアドレス",
        required=True,
    )

    kind = forms.ChoiceField(
        label="種別",
        choices=KIND_CHOICE,
        required=True,
    )


class ChangeV4AssignmentForm(forms.Form):
    netwrk_nm = forms.CharField(
        label="ネットワーク名",
        required=True,
    )

    org_nm_jp = forms.CharField(
        label="組織名",
        required=True,
    )

    org_nm = forms.CharField(
        label="組織名(En)",
        required=True,
    )

    zipcode = forms.CharField(
        label="郵便番号",
        min_length=8,
        max_length=8,
        required=True,
    )

    addr_jp = forms.CharField(
        label="住所",
        required=True,
    )

    addr = forms.CharField(
        label="住所(English)",
        required=True,
    )

    adm_hdl = forms.CharField(
        label="管理者連絡窓口",
        required=True,
    )

    tech_hdl = forms.CharField(
        label="技術連絡担当者",
        required=True,
    )

    abuse = forms.CharField(
        label="Abuse",
        required=False,
    )

    ntfy_mail = forms.CharField(
        label="通知アドレス",
        required=False,
    )

    chg_reason = forms.CharField(
        label="変更理由",
        required=True,
    )

    rtn_date = forms.DateField(
        label="返却年月日",
        input_formats=["%Y-%m-%d"],
        widget=forms.DateTimeInput(format="%Y-%m-%d"),
        required=False,
    )

    aply_from_addr = forms.EmailField(
        label="申請者メールアドレス",
        required=True,
    )


class ChangeV6AssignmentForm(forms.Form):
    networkname = forms.CharField(
        label="ネットワーク名",
        required=True,
    )

    sosikiname = forms.CharField(
        label="組織名",
        required=True,
    )

    sosikiorg = forms.CharField(
        label="組織名(En)",
        required=True,
    )

    postcode = forms.CharField(
        label="郵便番号",
        min_length=8,
        max_length=8,
        required=True,
    )

    address = forms.CharField(
        label="住所",
        required=True,
    )

    address2 = forms.CharField(
        label="住所(English)",
        required=True,
    )

    kanrimadoguchi = forms.CharField(
        label="管理者連絡窓口",
        required=True,
    )

    gijyutureraku = forms.CharField(
        label="技術連絡担当者",
        required=True,
    )

    abuse = forms.CharField(
        label="Abuse",
        required=False,
    )

    tuuchiaddress = forms.CharField(
        label="通知アドレス",
        required=False,
    )

    henkouriyu = forms.CharField(
        label="変更理由",
        required=True,
    )

    returndate = forms.DateField(
        label="返却年月日",
        input_formats=["%Y-%m-%d"],
        widget=forms.DateTimeInput(format="%Y-%m-%d"),
        required=False,
    )

    applymailaddr = forms.EmailField(
        label="申請者メールアドレス",
        required=True,
    )


class ReturnForm(forms.Form):
    jpnic_id = forms.ModelChoiceField(
        label="JPNIC証明書",
        queryset=JPNICModel.objects,
        required=True
    )

    ip_address = forms.CharField(
        label="IP Address",
        required=True,
    )

    return_date = forms.DateField(
        label="返却年月日",
        input_formats=["%Y/%m/%d"],
        initial="",
        widget=forms.DateTimeInput(format="%Y/%m/%d"),
        required=True,
    )
    notify_address = forms.EmailField(label="申請者アドレス", required=True)


class UploadFile(forms.Form):
    file = forms.FileField(label="ファイル(json)", required=False)
