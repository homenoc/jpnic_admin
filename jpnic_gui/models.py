from django.db import models


class JPNIC(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = "AS"

    name = models.CharField("名前", unique=True, max_length=100)
    is_active = models.BooleanField("有効", blank=True)
    is_ipv6 = models.BooleanField("IPv6", blank=False)

    asn = models.IntegerField("ASN")
    ca_path = models.CharField("中間CA証明書", max_length=200, default="")
    cert_path = models.CharField("Cert", max_length=200, default="")
    key_path = models.CharField("key", max_length=200, default="")
    p12_path = models.CharField("P12", max_length=200, default="")
    p12_pass = models.CharField("P12 Pass", max_length=200, default="")

    def __str__(self):
        return self.name
