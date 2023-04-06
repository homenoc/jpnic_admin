import datetime

from django import forms
from django.core.exceptions import ValidationError
from django.db import connection
from django.db.models import Q, Prefetch, Count, Func, F, Min, Window, Max

from jpnic_admin.resource.models import AddrList, ResourceList, ResourceAddressList
from .resource.sql import sqlDateSelect, sql_get_latest, sqlAddrListDateFilter


class SearchForm(forms.Form):
    as_id = forms.IntegerField(
        label="AS番号",
        required=False,
    )

    network_name = forms.CharField(
        label="ネットワーク名(一部含む)",
        required=False,
    )

    address = forms.CharField(
        label="住所/住所(English)(一部含む)",
        required=False,
    )

    start_date = forms.DateField(
        label="取得日開始",
        input_formats=["%Y-%m-%d"],
        initial=datetime.date.today,
        widget=forms.DateTimeInput(format="%Y-%m-%d"),
        required=False,
    )

    end_date = forms.DateField(
        label="取得日終了",
        input_formats=["%Y-%m-%d"],
        initial=datetime.date.today,
        widget=forms.DateTimeInput(format="%Y-%m-%d"),
        required=False,
    )

    def get_queryset(self, page=1):
        if not self.is_valid():
            return None

        cleaned_data = self.cleaned_data

        as_id = cleaned_data.get("as_id")
        network_name = cleaned_data.get("network_name")
        address = cleaned_data.get("address")
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        conditions = {}
        q = Q(**conditions)

        if as_id is None:
            return None

        # AS番号フィルタ
        q &= Q(jpnic_id=as_id)

        # ネットワーク名フィルタ
        if network_name != "":
            q &= Q(network_name__contains=network_name)

        # 住所/住所(English)一部含むフィルタ
        if address != "":
            q &= Q(address__contains=address) | Q(address_en__contains=address)

        sql = sqlDateSelect
        # 日付フィルタ
        # フィルタなし時現在の日付にする
        if start_date is None or end_date is None:
            # 最新バージョン
            # get_latest_timeを取得
            last_addr_list = AddrList.objects.filter(jpnic_id=as_id).order_by("-last_checked_at").first()
            q &= Q(last_checked_at__exact=last_addr_list.last_checked_at)
            sql = sql_get_latest
            input_array = [
                last_addr_list.last_checked_at,
                as_id,
                "%%%s%%" % network_name,
                "%%%s%%" % address,
                "%%%s%%" % address,
            ]
        else:
            q &= ~(Q(created_at__gte=end_date) or Q(last_checked_at__lte=start_date))
            input_array = [
                start_date,
                end_date,
                as_id,
                "%%%s%%" % network_name,
                "%%%s%%" % address,
                "%%%s%%" % address,
            ]

        # Count
        count = AddrList.objects.filter(q).count()
        # pages数
        all_pages = count // 50
        if count % 50 != 0:
            all_pages += 1
        # range_pages
        all_range_pages = []
        for i in range(all_pages):
            all_range_pages.append(i + 1)
        # range_pages
        next_page = None
        prev_page = None
        if page < all_pages:
            next_page = page + 1
        if page != 1:
            prev_page = page - 1

        # データ出力
        with connection.cursor() as cursor:
            input_array.append(50)
            input_array.append((page - 1) * 50)
            cursor.execute(sql, input_array)
            sql_result = cursor.fetchall()
        data = []
        for result in sql_result:
            data.append(
                {
                    "id": result[0],
                    "asn": result[1],
                    "created_at": result[2],
                    "last_checked_at": result[3],
                    "kind": result[4],
                    "division": result[5],
                    "ip_address": result[6],
                    "network_name": result[7],
                    "org": result[8],
                    "postcode": result[9],
                    "address": result[10],
                    "address_en": result[11],
                    "admin_handle": result[12],
                    "admin_name": result[13],
                    "admin_email": result[14],
                    "tech_handle": result[15],
                    "tech_name": result[16],
                    "tech_email": result[17],
                }
            )

        return {
            "all_range_pages": all_range_pages,
            "all_pages": all_pages,
            "next_page": next_page,
            "prev_page": prev_page,
            "count": count,
            "info": data,
        }


class SearchResourceForm(forms.Form):
    as_id = forms.IntegerField(
        label="対象AS番号",
        required=False,
    )

    select_date = forms.DateField(
        label="取得日",
        input_formats=["%Y-%m-%d"],
        initial=datetime.date.today,
        widget=forms.DateTimeInput(format="%Y-%m-%d"),
        required=False,
    )

    def get_queryset(self):
        if not self.is_valid():
            return None

        cleaned_data = self.cleaned_data

        as_id = cleaned_data.get("as_id")
        select_date = cleaned_data.get("select_date")

        if as_id is None:
            return None

        # 条件
        conditions = {}
        q = Q(**conditions)

        # AS番号フィルタ
        q &= Q(jpnic_id=as_id)

        # 日付フィルタ
        # 最新
        if select_date:
            # created_at < select_date && select_date < last_checked_
            start_time = datetime.datetime.combine(select_date, datetime.time())
            end_time = datetime.datetime.combine(select_date, datetime.time(23, 59, 59))
            q &= ~Q(last_checked_at__lt=start_time)
            q &= ~Q(created_at__gt=end_time)
            rs_list = ResourceList.objects.filter(q).order_by("-last_checked_at").first()
            rs_addr_list = ResourceAddressList.objects.raw(
                sqlAddrListDateFilter, params={"id": as_id, "start_time": start_time, "end_time": end_time}
            )
        else:
            rs_list = ResourceList.objects.filter(jpnic_id=as_id).order_by("-last_checked_at").first()
            rs_addr_list = ResourceAddressList.objects.filter(
                jpnic_id=as_id, last_checked_at__exact=rs_list.last_checked_at
            )

        return {
            "rs_list": rs_list,
            "rs_addr_list": rs_addr_list,
        }


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

    ipv6 = forms.BooleanField(label="ipv6であるか", required=False)

    ada = forms.BooleanField(
        label="データの自動収集",
        required=False,
    )

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
