from django.db import models


class JPNIC(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = "AS"

    name = models.CharField("名前", unique=True, max_length=100)
    is_active = models.BooleanField("有効", blank=True)
    is_ipv6 = models.BooleanField("IPv6", blank=False)
    asn = models.IntegerField("ASN")
    ca = models.CharField("中間CA証明書", max_length=1000, default="")
    p12_base64 = models.CharField("p12 base64", max_length=1000, default="")
    p12_pass = models.CharField("p12 Pass", max_length=200, default="")

    def __str__(self):
        return self.name
