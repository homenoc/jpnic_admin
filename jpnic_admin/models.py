from django.db import models


class JPNIC(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = "AS"

    first_checked_at = models.DateTimeField("初回取得開始時刻", null=True, blank=True, db_index=True)
    last_resource1_checked_at = models.DateTimeField("resource1の最終更新時刻", null=True, blank=True)
    last_resource2_checked_at = models.DateTimeField("resource2の最終更新時刻", null=True, blank=True)
    name = models.CharField("名前", unique=True, max_length=100)
    is_active = models.BooleanField("有効", blank=True)
    is_ipv6 = models.BooleanField("IPv6", blank=False)
    ada = models.BooleanField("データの自動取得", blank=False)
    collection_interval = models.IntegerField("収集頻度(分)", blank=False, default=60)
    asn = models.IntegerField("ASN")
    p12_base64 = models.CharField("p12 base64", max_length=10000, default="")
    p12_pass = models.CharField("p12 Pass", max_length=200, default="")

    def __str__(self):
        return self.name


# class RequestLog(models.Model):
#     class Meta:
#         verbose_name = verbose_name_plural = "申請ログ"
#
#     name = models.CharField("名前", max_length=100)
#     # result = models.CharField("結果", max_length=65530)
