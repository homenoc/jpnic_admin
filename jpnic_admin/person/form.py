from django import forms
from jpnic_admin.models import JPNIC as JPNICModel


class BaseForm(forms.Form):
    jpnic_id = forms.ModelChoiceField(queryset=JPNICModel.objects, required=True)


class GetJPNICHandleForm(forms.Form):
    jpnic_id = forms.ModelChoiceField(queryset=JPNICModel.objects, required=True)

    jpnic_handle = forms.CharField(
        label="JPNICハンドル",
        required=False,
    )


class AddForm(forms.Form):
    HANDLE_GROUP = "group"
    HANDLE_JPNIC = "person"
    HANDLE_CHOICE = [
        (HANDLE_GROUP, "グループハンドル"),
        (HANDLE_JPNIC, "JPNICハンドル"),
    ]

    kind = forms.ChoiceField(
        label="グループ/JPNICハンドル",
        choices=HANDLE_CHOICE,
        initial=HANDLE_JPNIC,
        # empty_value=HANDLE_JPNIC,
        show_hidden_initial=False,
        required=False,
    )

    jpnic_hdl = forms.CharField(
        label="ハンドル",
        initial="1",
        required=False,
    )

    name_jp = forms.CharField(
        label="グループ名or氏名",
        required=False,
    )

    name = forms.CharField(
        label="グループ名or氏名(English)",
        required=False,
    )

    email = forms.EmailField(
        label="E-Mail",
        required=False,
    )

    org_nm_jp = forms.CharField(
        label="組織名",
        required=False,
    )

    org_nm = forms.CharField(
        label="組織名(English)",
        required=False,
    )

    zipcode = forms.CharField(
        label="郵便番号",
        min_length=8,
        max_length=8,
        required=False,
    )

    addr_jp = forms.CharField(
        label="住所",
        required=False,
    )

    addr = forms.CharField(
        label="住所(English)",
        required=False,
    )

    division_jp = forms.CharField(
        label="部署",
        required=False,
    )

    division = forms.CharField(
        label="部署(English)",
        required=False,
    )

    title_jp = forms.CharField(
        label="肩書",
        required=False,
    )

    title = forms.CharField(
        label="肩書(English)",
        required=False,
    )

    phone = forms.CharField(
        label="電話番号",
        required=False,
    )

    fax = forms.CharField(
        label="FAX番号",
        required=False,
    )

    email = forms.EmailField(
        label="E-Mail",
        required=False,
    )

    ntfy_mail = forms.EmailField(
        label="通知アドレス",
        required=False,
    )

    aply_from_addr = forms.EmailField(
        label="申請者アドレス",
        required=False,
    )


class UploadFile(forms.Form):
    file = forms.FileField(label="ファイル(json)", required=False)
