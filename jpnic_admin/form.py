from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label  # placeholderにフィールドのラベルを入れる


class AddAssignment(forms.Form):
    network_name = forms.CharField(
        label="ネットワーク名",
        required=False,
    )

    org = forms.CharField(
        label="組織名",
        required=False,
    )

    org_en = forms.CharField(
        label="組織名(English)",
        required=False,
    )

    postcode = forms.CharField(
        label="郵便番号",
        min_length=8,
        max_length=8,
        required=False,
    )

    address = forms.CharField(
        label="住所",
        required=False,
    )

    address_en = forms.CharField(
        label="住所(English)",
        required=False,
    )

    name_server = forms.CharField(
        label="ネームサーバ",
        required=False,
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

    apply_email = forms.EmailField(
        label="申請者メールアドレス",
        required=False,
    )

    file = forms.FileField(label="ファイル(json)", required=False)

    def clean(self):
        cleaned_data = super().clean()
        cc_myself = cleaned_data.get("cc_myself")
        subject = cleaned_data.get("subject")

        if cc_myself and subject:
            # Only do something if both fields are valid so far.
            if "help" not in subject:
                raise ValidationError("Did not send for 'help' in the subject despite " "CC'ing yourself.")


class GetIPAddressForm(forms.Form):
    KIND_CHOICE = [(1, "割振"), (2, "ユーザ割当"), (3, "インフラ割当"), (4, "SUBA")]

    asn = forms.IntegerField(
        label="AS番号",
        required=True,
    )

    ipv6 = forms.BooleanField(label="ipv6", required=False)

    ip_address = forms.CharField(
        label="IPアドレス",
        required=False,
    )

    kind = forms.ChoiceField(
        label="種別",
        choices=KIND_CHOICE,
        required=False,
    )


class GetChangeAssignment(forms.Form):
    V4_KIND_CHOICE = [
        (0, "割り当て"),
        (2, "SUBA登録"),
        (3, "歴史的PI"),
    ]

    asn = forms.IntegerField(
        label="AS番号",
        required=True,
    )

    ipv6 = forms.BooleanField(label="ipv6", required=False)

    ip_address = forms.CharField(
        label="IP Address",
        required=False,
    )

    kind = forms.ChoiceField(
        label="種別",
        choices=V4_KIND_CHOICE,
        required=False,
    )

    def clean(self):
        cleaned_data = super().clean()
        input_asn = cleaned_data.get("asn")
        if input_asn < 1:
            raise forms.ValidationError("AS番号が正しくありません")
        input_ip_address = cleaned_data.get("ip_address")
        if not input_ip_address:
            raise forms.ValidationError("IPアドレスが正しくありません")
        if not cleaned_data.get("ipv6"):
            input_kind = cleaned_data.get("kind")
            if not input_kind:
                raise forms.ValidationError("IPv4種別を選択してください")


class ChangeV4Assignment(forms.Form):
    netwrk_nm = forms.CharField(
        label="ネットワーク名",
        required=False,
    )

    org_nm_jp = forms.CharField(
        label="組織名",
        required=False,
    )

    org_nm = forms.CharField(
        label="組織名(En)",
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

    adm_hdl = forms.CharField(
        label="管理者連絡窓口",
        required=False,
    )

    tech_hdl = forms.CharField(
        label="技術連絡担当者",
        required=False,
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
        required=False,
    )

    rtn_date = forms.DateField(
        label="返却年月日",
        input_formats=["%Y-%m-%d"],
        widget=forms.DateTimeInput(format="%Y-%m-%d"),
        required=False,
    )

    aply_from_addr = forms.EmailField(
        label="申請者メールアドレス",
        required=False,
    )


class ChangeV6Assignment(forms.Form):
    networkname = forms.CharField(
        label="ネットワーク名",
        required=False,
    )

    sosikiname = forms.CharField(
        label="組織名",
        required=False,
    )

    sosikiorg = forms.CharField(
        label="組織名(En)",
        required=False,
    )

    postcode = forms.CharField(
        label="郵便番号",
        min_length=8,
        max_length=8,
        required=False,
    )

    address = forms.CharField(
        label="住所",
        required=False,
    )

    address2 = forms.CharField(
        label="住所(English)",
        required=False,
    )

    kanrimadoguchi = forms.CharField(
        label="管理者連絡窓口",
        required=False,
    )

    gijyutureraku = forms.CharField(
        label="技術連絡担当者",
        required=False,
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
        required=False,
    )

    returndate = forms.DateField(
        label="返却年月日",
        input_formats=["%Y-%m-%d"],
        widget=forms.DateTimeInput(format="%Y-%m-%d"),
        required=False,
    )

    applymailaddr = forms.EmailField(
        label="申請者メールアドレス",
        required=False,
    )


class Base1(forms.Form):
    asn = forms.IntegerField(
        label="AS番号",
        required=True,
    )

    ipv6 = forms.BooleanField(label="ipv6", required=False)

    def clean(self):
        cleaned_data = super().clean()
        input_asn = cleaned_data.get("asn")
        if input_asn < 1:
            raise forms.ValidationError("AS番号が正しくありません")


class GetJPNICHandle(forms.Form):
    asn = forms.IntegerField(
        label="AS番号",
        required=True,
    )

    ipv6 = forms.BooleanField(label="ipv6", required=False)

    jpnic_handle = forms.CharField(
        label="JPNICハンドル",
        required=False,
    )

    def clean(self):
        cleaned_data = super().clean()
        input_asn = cleaned_data.get("asn")
        if input_asn < 1:
            raise forms.ValidationError("AS番号が正しくありません")
        input_jpnic_handle = cleaned_data.get("jpnic_handle")
        if not input_jpnic_handle:
            raise forms.ValidationError("JPNIC Handleを指定してください")


class AddGroupContact(forms.Form):
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

    ntfy_mail = forms.EmailField(
        label="通知アドレス",
        required=False,
    )

    aply_from_addr = forms.EmailField(
        label="申請者アドレス",
        required=False,
    )


class ReturnAssignment(forms.Form):
    asn = forms.IntegerField(
        label="AS番号",
        required=True,
    )

    ipv6 = forms.BooleanField(label="ipv6", required=False)

    ip_address = forms.CharField(
        label="IP Address",
        required=False,
    )

    return_date = forms.DateField(
        label="返却年月日",
        input_formats=["%Y/%m/%d"],
        initial="",
        widget=forms.DateTimeInput(format="%Y/%m/%d"),
        required=False,
    )

    notify_address = forms.CharField(label="申請者アドレス", required=False)


class UploadFile(forms.Form):
    file = forms.FileField(label="ファイル(json)", required=False)


class ASForm(forms.Form):
    name = forms.CharField(
        label="name",
        required=False,
    )

    ipv6 = forms.BooleanField(label="ipv6", required=False)

    collection_interval = forms.IntegerField(
        label="収集頻度(分)",
        required=True,
    )

    asn = forms.IntegerField(
        label="ASN",
        required=True,
    )

    p12 = forms.FileField(label="ファイル(.p12)", required=False)

    p12_pass = forms.CharField(
        label="p12パスワード",
        required=False,
    )


class ChangeCertForm(forms.Form):
    p12 = forms.FileField(label="ファイル(.p12)", required=False)

    p12_pass = forms.CharField(
        label="p12パスワード",
        required=False,
    )
