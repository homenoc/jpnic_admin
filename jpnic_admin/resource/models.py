from django.db import models

from jpnic_admin.models import JPNIC, MediumTextField


class JPNICHandle(models.Model):
    class Meta:
        ordering = (
            "-last_checked_at",
            "-created_at",
            "jpnic_id",
            "id",
        )
        index_together = [
            ["created_at", "last_checked_at", "jpnic_handle", "jpnic_id"],
            ["last_checked_at", "jpnic_handle", "jpnic_id"],
        ]

    created_at = models.DateTimeField("取得開始時刻", db_index=True)
    last_checked_at = models.DateTimeField("最終更新時刻", db_index=True)
    jpnic_handle = models.CharField("JPNICハンドル", max_length=20, db_index=True)
    name = models.CharField("名前", max_length=120, null=True, blank=True)
    name_en = models.CharField("名前(英語)", max_length=120, null=True, blank=True)
    email = models.CharField("メールアドレス", max_length=50, null=True, blank=True)
    org = models.CharField("組織名", max_length=120, null=True, blank=True)
    org_en = models.CharField("組織名(英語)", max_length=120, null=True, blank=True)
    post_code = models.CharField("郵便番号", max_length=20, null=True, blank=True)
    address = models.CharField("住所", max_length=200, null=True, blank=True)
    address_en = models.CharField("住所(英語)", max_length=200, null=True, blank=True)
    division = models.CharField("部署", max_length=120, null=True, blank=True)
    division_en = models.CharField("部署(英語)", max_length=120, null=True, blank=True)
    title = models.CharField("肩書", max_length=120, null=True, blank=True)
    title_en = models.CharField("肩書(英語)", max_length=120, null=True, blank=True)
    tel = models.CharField("電話番号", max_length=100, null=True, blank=True)
    fax = models.CharField("Fax", max_length=100, null=True, blank=True)
    notify_address = models.CharField("通知アドレス", max_length=100, null=True, blank=True)
    apply_from_email = models.CharField("申請者メールアドレス", max_length=100, null=True, blank=True)
    updated_at = models.DateTimeField("情報更新時刻", null=True, blank=True, db_index=True)
    recep_number = models.CharField("受付番号", null=True, blank=True, max_length=30)  # アドレスから取得した場合はblank
    jpnic = models.ForeignKey(JPNIC, on_delete=models.CASCADE)

    def __str__(self):
        return self.jpnic_handle


class AddrList(models.Model):
    class Meta:
        ordering = (
            "-last_checked_at",
            "-created_at",
            "ip_address",
            "jpnic_id",
            "id",
        )
        index_together = [
            [
                "jpnic_id",
                "network_name",
                "address",
                "address_en",
                "ip_address",
                "admin_handle",
                "assign_date",
                "type",
                "division",
            ],
            ["created_at", "last_checked_at", "jpnic_id", "network_name", "address", "address_en"],
            ["last_checked_at", "jpnic_id", "network_name", "address", "address_en"],
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

    created_at = models.DateTimeField("取得開始時刻", db_index=True)
    last_checked_at = models.DateTimeField("最終更新時刻", db_index=True)
    ip_address = models.CharField("IPアドレス", max_length=100, db_index=True)
    network_name = models.CharField("ネットワーク名", max_length=30)
    assign_date = models.DateTimeField("割振・割当年月日", null=True, blank=True)
    return_date = models.DateTimeField("返却年月日", null=True, blank=True)
    org = models.CharField("組織名", max_length=120, null=True, blank=True)
    org_en = models.CharField("組織名(英語)", max_length=120, null=True, blank=True)
    resource_admin_short = models.CharField("資源管理者略称", max_length=50)
    recep_number = models.CharField("受付番号", max_length=30, null=True, blank=True)
    deli_number = models.CharField("審議番号", max_length=30, null=True, blank=True)
    type = models.CharField("種別", max_length=30, choices=TYPE_CHOICES)  # v4only
    division = models.CharField("区分", max_length=30, choices=DIVISION_CHOICES)
    post_code = models.CharField("郵便番号", max_length=20, null=True, blank=True)
    address = models.CharField("住所", max_length=200, null=True, blank=True)
    address_en = models.CharField("住所(英語)", max_length=200, null=True, blank=True)
    nameserver = models.CharField("ネームサーバ", max_length=200, null=True, blank=True)
    ds_record = models.CharField("DSレコード", max_length=500, null=True, blank=True)
    abuse = models.CharField("Abuse", max_length=500, null=True, blank=True)
    notify_address = models.CharField("通知アドレス", max_length=100, null=True, blank=True)
    apply_from_email = models.CharField("申請者メールアドレス", max_length=100, null=True, blank=True)
    admin_handle = models.CharField("JPNICハンドル", max_length=20, db_index=True)
    updated_at = models.DateTimeField("情報更新時刻", null=True, blank=True, db_index=True)
    jpnic = models.ForeignKey(JPNIC, on_delete=models.CASCADE)

    def __str__(self):
        return self.ip_address


class AddrListTechHandle(models.Model):
    addr_list = models.ForeignKey(AddrList, on_delete=models.CASCADE)
    jpnic_handle = models.CharField("JPNICハンドル", max_length=20, db_index=True)


# resource
class ResourceList(models.Model):
    class Meta:
        ordering = (
            "-last_checked_at",
            "-created_at",
            "jpnic_id",
        )
        index_together = [
            ["created_at", "last_checked_at", "jpnic_id"],
            ["created_at", "last_checked_at", "jpnic_id"],
            ["last_checked_at", "jpnic_id"],
        ]

    created_at = models.DateTimeField("取得開始時刻", db_index=True)
    last_checked_at = models.DateTimeField("最終更新時刻", db_index=True)
    resource_no = models.IntegerField("資源管理者番号", db_index=True)
    resource_admin_short = models.CharField("資源管理者略称", max_length=50)
    org = models.CharField("組織名", max_length=120)
    org_en = models.CharField("組織名(英語)", max_length=120)
    post_code = models.CharField("郵便番号", max_length=20)
    address = models.CharField("住所", max_length=200)
    address_en = models.CharField("住所(英語)", max_length=200)
    tel = models.CharField("電話番号", max_length=100, blank=True)
    fax = models.CharField("Fax", max_length=100, blank=True)
    admin_handle = models.CharField("資源管理責任者", max_length=20, db_index=True)
    email = models.CharField("連絡担当窓口", max_length=50)
    common_email = models.CharField("一般問い合わせ窓口", max_length=50)
    notify_email = models.CharField("資源管理者通知アドレス", max_length=50)
    assignment_size = models.IntegerField("アサインメントウィンドウサイズ")
    start_date = models.DateTimeField("管理開始時刻")
    end_date = models.DateTimeField("管理終了時刻", null=True, blank=True)
    update_date = models.DateTimeField("最終更新時刻", null=True, blank=True, db_index=True)
    all_addr_count = models.IntegerField("総アドレス数")
    assigned_addr_count = models.IntegerField("割当数")
    ad_ratio = models.FloatField("AD Ratio")
    html_source = MediumTextField(
        verbose_name="出力HTML",
        null=True,
        blank=True,
    )
    jpnic = models.ForeignKey(JPNIC, on_delete=models.CASCADE)


class ResourceAddressList(models.Model):
    class Meta:
        ordering = (
            "-last_checked_at",
            "-created_at",
            "jpnic_id",
        )

    index_together = [
        ["created_at", "last_enabled_at", "jpnic_id"],
        ["created_at", "last_checked_at", "jpnic_id"],
        ["last_enabled_at", "jpnic_id"],
    ]

    created_at = models.DateTimeField("取得開始時刻", db_index=True)
    last_checked_at = models.DateTimeField("最終更新時刻", db_index=True)
    ip_address = models.CharField("IPアドレス", max_length=100, db_index=True)
    assign_date = models.DateTimeField("割振年月日")
    all_addr_count = models.IntegerField("アドレス数", db_index=True, default=0)
    assigned_addr_count = models.IntegerField("割当数", db_index=True)
    jpnic = models.ForeignKey(JPNIC, on_delete=models.CASCADE)
