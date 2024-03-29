from django.db import models


class MediumTextField(models.TextField):
    def db_type(self, connection):
        if connection.settings_dict["ENGINE"] == "django.db.backends.mysql":
            return "mediumtext"
        else:
            return super(MediumTextField, self).db_type(connection=connection)


class JPNIC(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = "AS"

    name = models.CharField("名前", unique=True, max_length=100)
    is_active = models.BooleanField("有効", blank=True)
    is_ipv6 = models.BooleanField("IPv6", blank=False)
    option_collection_no_filter = models.BooleanField("取得フィルタを解除(オプション)", blank=False, default=False)
    collection_interval = models.IntegerField("収集頻度(分)", blank=False, default=60)
    asn = models.IntegerField("ASN")
    p12_base64 = models.CharField("p12 base64", max_length=10000, default="")
    p12_pass = models.CharField("p12 Pass", max_length=200, default="")

    def __str__(self):
        return self.name
