# Generated by Django 4.1 on 2023-03-07 16:25

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="JPNIC",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "first_checked_at",
                    models.DateTimeField(
                        blank=True, db_index=True, null=True, verbose_name="初回取得開始時刻"
                    ),
                ),
                (
                    "last_resource1_checked_at",
                    models.DateTimeField(blank=True, null=True, verbose_name="resource1の最終更新時刻"),
                ),
                (
                    "last_resource2_checked_at",
                    models.DateTimeField(blank=True, null=True, verbose_name="resource2の最終更新時刻"),
                ),
                ("name", models.CharField(max_length=100, unique=True, verbose_name="名前")),
                ("is_active", models.BooleanField(blank=True, verbose_name="有効")),
                ("is_ipv6", models.BooleanField(verbose_name="IPv6")),
                ("ada", models.BooleanField(verbose_name="データの自動取得")),
                ("collection_interval", models.IntegerField(default=60, verbose_name="収集頻度(分)")),
                ("asn", models.IntegerField(verbose_name="ASN")),
                (
                    "p12_base64",
                    models.CharField(default="", max_length=10000, verbose_name="p12 base64"),
                ),
                ("p12_pass", models.CharField(default="", max_length=200, verbose_name="p12 Pass")),
            ],
            options={
                "verbose_name": "AS",
                "verbose_name_plural": "AS",
            },
        ),
    ]
