from django.db import models


class JPNICHandle(models.Model):
    class Meta:
        ordering = ("id", "last_enabled_at", "created_at")
        index_together = [
            ["created_at", "last_enabled_at", "jpnic_handle", "asn", "ip_version"],
            ["last_enabled_at", "jpnic_handle", "asn", "ip_version"],
        ]

    created_at = models.DateTimeField("取得開始時刻", auto_now_add=True, db_index=True)
    last_enabled_at = models.DateTimeField("最終有効時刻", null=True, blank=True, db_index=True)
    jpnic_handle = models.CharField("JPNICハンドル", max_length=20, db_index=True)
    name = models.CharField("名前", max_length=120)
    name_en = models.CharField("名前(英語)", max_length=120)
    email = models.CharField("メールアドレス", max_length=50)
    org = models.CharField("組織名", max_length=120)
    org_en = models.CharField("組織名(英語)", max_length=120)
    post_code = models.CharField("郵便番号", max_length=20, blank=True)
    address = models.CharField("住所", max_length=200, blank=True)
    address_en = models.CharField("住所(英語)", max_length=200, blank=True)
    division = models.CharField("部署", max_length=120, blank=True)
    division_en = models.CharField("部署(英語)", max_length=120, blank=True)
    title = models.CharField("肩書", max_length=120, blank=True)
    title_en = models.CharField("肩書(英語)", max_length=120, blank=True)
    tel = models.CharField("電話番号", max_length=100, blank=True)
    fax = models.CharField("Fax", max_length=100, blank=True)
    notify_address = models.CharField("通知アドレス", max_length=100, blank=True)
    apply_from_email = models.CharField("申請者メールアドレス", max_length=100, blank=True)
    updated_at = models.DateTimeField("情報更新時刻", null=True, blank=True, db_index=True)
    recep_number = models.CharField("受付番号", blank=True, max_length=30)  # アドレスから取得した場合はblank
    asn = models.IntegerField("AS番号")
    ip_version = models.IntegerField("IP Version")

    def __str__(self):
        return self.jpnic_handle


class AddrList(models.Model):
    class Meta:
        ordering = ("id", "last_checked_at", "ip_address")
        index_together = [
            [
                "asn",
                "ip_version",
                "network_name",
                "address",
                "address_en",
                "ip_address",
                "admin_handle",
                "assign_date",
                "type",
                "division",
            ],
            ["created_at", "last_checked_at", "asn", "ip_version", "network_name", "address", "address_en"],
            ["last_checked_at", "asn", "ip_version", "network_name", "address", "address_en"],
        ]

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
        (DIVISION_SUB_ALLOCATE, "v4(SUBA)/v6(再割当)"),
    )

    created_at = models.DateTimeField("取得開始時刻", auto_now_add=True, db_index=True)
    last_checked_at = models.DateTimeField("最終更新時刻", auto_now=True, db_index=True)
    ip_address = models.CharField("IPアドレス", max_length=100, db_index=True)
    network_name = models.CharField("ネットワーク名", max_length=30)
    assign_date = models.DateTimeField("割振・割当年月日", null=True, blank=True)
    return_date = models.DateTimeField("返却年月日", null=True, blank=True)
    org = models.CharField("組織名", max_length=120)
    org_en = models.CharField("組織名(英語)", max_length=120)
    resource_admin_short = models.CharField("資源管理者略称", max_length=50)
    recep_number = models.CharField("受付番号", max_length=30)
    deli_number = models.CharField("審議番号", max_length=30, null=True, blank=True)
    type = models.CharField("種別", max_length=30, choices=TYPE_CHOICES)  # v4only
    division = models.CharField("区分", max_length=30, choices=DIVISION_CHOICES)
    post_code = models.CharField("郵便番号", max_length=20)
    address = models.CharField("住所", max_length=200)
    address_en = models.CharField("住所(英語)", max_length=200)
    nameserver = models.CharField("ネームサーバ", max_length=200, blank=True)
    ds_record = models.CharField("DSレコード", max_length=500, blank=True)
    abuse = models.CharField("Abuse", max_length=500, blank=True)
    notify_address = models.CharField("通知アドレス", max_length=100, blank=True)
    apply_from_email = models.CharField("申請者メールアドレス", max_length=100, blank=True)
    asn = models.IntegerField("AS番号")
    ip_version = models.IntegerField("IP Version")
    admin_handle = models.CharField("JPNICハンドル", max_length=20, db_index=True)
    updated_at = models.DateTimeField("情報更新時刻", null=True, blank=True, db_index=True)

    def __str__(self):
        return self.ip_address


class AddrListTechHandle(models.Model):
    addr_list = models.ForeignKey(AddrList, on_delete=models.CASCADE)
    jpnic_handle = models.CharField("JPNICハンドル", max_length=20, db_index=True)
