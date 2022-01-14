from django.db import models


class JPNIC(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = "AS"

    name = models.CharField("名前", unique=True, max_length=100)
    is_active = models.BooleanField("有効", blank=True)
    is_ipv6 = models.BooleanField("IPv6", blank=False)

    asn = models.IntegerField("ASN")
    ca_path = models.CharField("中間CA証明書", unique=True, max_length=200)
    cert_path = models.CharField("Cert", unique=True, max_length=200)
    key_path = models.CharField("key", unique=True, max_length=200)

    def __str__(self):
        return self.name

