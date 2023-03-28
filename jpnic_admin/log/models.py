from django.db import models

from jpnic_admin.models import JPNIC


class Task(models.Model):
    class Meta:
        ordering = ("-last_checked_at",)
        index_together = [
            ["created_at", "last_checked_at", "type1", "jpnic_id"],
            ["last_checked_at", "type1", "jpnic_id"],
        ]

    RESOURCE = "資源情報"
    RESOURCE_ADDRESS = "アドレス情報"

    TYPE1_CHOICES = (
        (RESOURCE, RESOURCE),
        (RESOURCE_ADDRESS, RESOURCE_ADDRESS),
    )

    created_at = models.DateTimeField("取得開始時刻", auto_now_add=True, db_index=True)
    last_checked_at = models.DateTimeField("最終更新時刻", db_index=True)
    type1 = models.CharField("type1", max_length=200, choices=TYPE1_CHOICES)
    count = models.IntegerField("リクエスト回数")
    fail_count = models.IntegerField("リクエスト失敗回数")
    fail_result = models.CharField(max_length=200, verbose_name="失敗理由", null=True, blank=True, )
    jpnic = models.ForeignKey(JPNIC, on_delete=models.CASCADE)

# RequestLog
