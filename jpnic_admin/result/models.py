import json
from django.db import models


class JPNICHandle(models.Model):
    get_start_date = models.DateTimeField("取得開始時刻")
    get_date = models.DateTimeField("取得更新時刻")
    is_ipv6 = models.BooleanField("IPv6", blank=False)
    jpnic_handle = models.CharField("JPNICハンドル", max_length=20, db_index=True)
    name = models.CharField("名前", max_length=50, db_index=True)
    name_en = models.CharField("名前(英語)", max_length=50, db_index=True)
    email = models.CharField("メールアドレス", max_length=50, db_index=True)
    org = models.CharField("組織名", max_length=50, db_index=True)
    org_en = models.CharField("組織名(英語)", max_length=50, db_index=True)
    division = models.CharField("部署", max_length=30, null=True, blank=True, db_index=True)
    division_en = models.CharField("部署(英語)", max_length=30, null=True, blank=True, db_index=True)
    tel = models.CharField("電話番号", max_length=100, null=True, blank=True, db_index=True)
    fax = models.CharField("Fax", max_length=100, null=True, blank=True, db_index=True)
    asn = models.ForeignKey("jpnic_admin.JPNIC", related_name="jpnic_handle", on_delete=models.CASCADE)
    update_date = models.DateTimeField("更新時刻")

    def __str__(self):
        return self.jpnic_handle


class V4List(models.Model):
    TYPE_PA = "pa"
    TYPE_HISTORICAL_PI = "historical_pi"
    TYPE_SPECIAL_PI = "special_pi"
    TYPE_CHOICES = (
        (TYPE_PA, "PA"),
        (TYPE_HISTORICAL_PI, "歴史的PI"),
        (TYPE_SPECIAL_PI, "特殊用途PI"),
    )

    DIVISION_ALLOCATE = "allocate"
    DIVISION_ASSIGN_INFRA = "assign_infra"
    DIVISION_ASSIGN_USER = "assign_user"
    DIVISION_SUB_ALLOCATE = "sub_allocate"
    DIVISION_CHOICES = (
        (DIVISION_ALLOCATE, "割振"),
        (DIVISION_ASSIGN_INFRA, "インフラ割当"),
        (DIVISION_ASSIGN_USER, "ユーザ割当"),
        (DIVISION_SUB_ALLOCATE, "SUBA"),
    )

    get_start_date = models.DateTimeField("取得開始時刻")
    get_date = models.DateTimeField("取得更新時刻")
    ip_address = models.CharField("IPアドレス", max_length=100, db_index=True)
    size = models.IntegerField("サイズ")
    network_name = models.CharField("ネットワーク名", max_length=30)
    assign_date = models.DateTimeField("割振・割当年月日")
    return_date = models.DateTimeField("返却年月日", null=True, blank=True)
    org = models.CharField("組織名", max_length=50)
    org_en = models.CharField("組織名(英語)", max_length=50, db_index=True)
    resource_admin_short = models.CharField("資源管理者略称", max_length=50)
    recep_number = models.CharField("受付番号", max_length=30)
    deli_number = models.CharField("審議番号", max_length=30, null=True, blank=True)
    type = models.CharField("種別", max_length=30, choices=TYPE_CHOICES)
    division = models.CharField("区分", max_length=30, choices=DIVISION_CHOICES)
    post_code = models.CharField("郵便番号", max_length=20, db_index=True)
    address = models.CharField("住所", max_length=200, db_index=True)
    address_en = models.CharField("住所(英語)", max_length=200, db_index=True)
    name_server = models.CharField("ネームサーバ", max_length=100, null=True, blank=True)
    ds_record = models.CharField("DSレコード", max_length=100, null=True, blank=True)
    notify_address = models.CharField("通知アドレス", max_length=100, null=True, blank=True)
    asn = models.ForeignKey("jpnic_admin.JPNIC", related_name="v4lists", on_delete=models.CASCADE)
    admin_jpnic = models.ForeignKey("result.JPNICHandle", related_name="v4lists", null=True, on_delete=models.CASCADE)
    tech_jpnic = models.ManyToManyField(JPNICHandle)

    def __str__(self):
        return self.ip_address


class V6List(models.Model):
    DIVISION_ALLOCATE = "allocate"
    DIVISION_ASSIGN_INFRA = "assign_infra"
    DIVISION_ASSIGN_USER = "assign_user"
    DIVISION_SUB_ALLOCATE = "sub_allocate"
    DIVISION_CHOICES = (
        (DIVISION_ALLOCATE, "割振"),
        (DIVISION_ASSIGN_INFRA, "インフラ割当"),
        (DIVISION_ASSIGN_USER, "ユーザ割当"),
        (DIVISION_SUB_ALLOCATE, "再割当"),
    )

    get_start_date = models.DateTimeField("取得開始時刻")
    get_date = models.DateTimeField("取得更新時刻")
    ip_address = models.CharField("IPアドレス", max_length=100, db_index=True)
    network_name = models.CharField("ネットワーク名", max_length=30)
    assign_date = models.DateTimeField("割振・割当年月日")
    return_date = models.DateTimeField("返却年月日", null=True, blank=True)
    org = models.CharField("組織名", max_length=50, db_index=True)
    org_en = models.CharField("組織名(英語)", max_length=50, db_index=True)
    resource_admin_short = models.CharField("資源管理者略称", max_length=50)
    recep_number = models.CharField("受付番号", max_length=30)
    deli_number = models.CharField("審議番号", max_length=30, null=True, blank=True)
    division = models.CharField("区分", max_length=30, choices=DIVISION_CHOICES)
    post_code = models.CharField("郵便番号", max_length=20, db_index=True)
    address = models.CharField("住所", max_length=200, db_index=True)
    address_en = models.CharField("住所(英語)", max_length=200, db_index=True)
    name_server = models.CharField("ネームサーバ", max_length=100, null=True, blank=True)
    ds_record = models.CharField("DSレコード", max_length=100, null=True, blank=True)
    notify_address = models.CharField("通知アドレス", max_length=100, null=True, blank=True)
    asn = models.ForeignKey("jpnic_admin.JPNIC", related_name="v6lists", on_delete=models.CASCADE)
    admin_jpnic = models.ForeignKey("result.JPNICHandle", related_name="v6lists", null=True, on_delete=models.CASCADE)
    tech_jpnic = models.ManyToManyField(JPNICHandle)

    def __str__(self):
        return self.ip_address
