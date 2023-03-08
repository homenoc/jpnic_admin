# Generated by Django 4.1 on 2023-03-09 04:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AddrList",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="取得開始時刻")),
                ("last_checked_at", models.DateTimeField(auto_now=True, db_index=True, verbose_name="最終更新時刻")),
                ("ip_address", models.CharField(db_index=True, max_length=100, verbose_name="IPアドレス")),
                ("network_name", models.CharField(max_length=30, verbose_name="ネットワーク名")),
                ("assign_date", models.DateTimeField(blank=True, null=True, verbose_name="割振・割当年月日")),
                ("return_date", models.DateTimeField(blank=True, null=True, verbose_name="返却年月日")),
                ("org", models.CharField(max_length=120, verbose_name="組織名")),
                ("org_en", models.CharField(max_length=120, verbose_name="組織名(英語)")),
                ("resource_admin_short", models.CharField(max_length=50, verbose_name="資源管理者略称")),
                ("recep_number", models.CharField(max_length=30, verbose_name="受付番号")),
                ("deli_number", models.CharField(blank=True, max_length=30, null=True, verbose_name="審議番号")),
                (
                    "type",
                    models.CharField(
                        choices=[("pa", "PA"), ("historical_pi", "歴史的PI"), ("special_pi", "特殊用途PI")],
                        max_length=30,
                        verbose_name="種別",
                    ),
                ),
                (
                    "division",
                    models.CharField(
                        choices=[
                            ("allocate", "割振"),
                            ("assign_infra", "インフラ割当"),
                            ("assign_user", "ユーザ割当"),
                            ("sub_allocate", "v4(SUBA)/v6(再割当)"),
                        ],
                        max_length=30,
                        verbose_name="区分",
                    ),
                ),
                ("post_code", models.CharField(max_length=20, verbose_name="郵便番号")),
                ("address", models.CharField(max_length=200, verbose_name="住所")),
                ("address_en", models.CharField(max_length=200, verbose_name="住所(英語)")),
                ("nameserver", models.CharField(blank=True, max_length=200, verbose_name="ネームサーバ")),
                ("ds_record", models.CharField(blank=True, max_length=500, verbose_name="DSレコード")),
                ("abuse", models.CharField(blank=True, max_length=500, verbose_name="Abuse")),
                ("notify_address", models.CharField(blank=True, max_length=100, verbose_name="通知アドレス")),
                ("apply_from_email", models.CharField(blank=True, max_length=100, verbose_name="申請者メールアドレス")),
                ("asn", models.IntegerField(verbose_name="AS番号")),
                ("ip_version", models.IntegerField(verbose_name="IP Version")),
                ("admin_handle", models.CharField(db_index=True, max_length=20, verbose_name="JPNICハンドル")),
                ("updated_at", models.DateTimeField(blank=True, db_index=True, null=True, verbose_name="情報更新時刻")),
            ],
            options={
                "ordering": ("id", "last_checked_at", "ip_address"),
                "index_together": {
                    (
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
                    ),
                    ("last_checked_at", "asn", "ip_version", "network_name", "address", "address_en"),
                    ("created_at", "last_checked_at", "asn", "ip_version", "network_name", "address", "address_en"),
                },
            },
        ),
        migrations.CreateModel(
            name="JPNICHandle",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="取得開始時刻")),
                ("last_enabled_at", models.DateTimeField(blank=True, db_index=True, null=True, verbose_name="最終有効時刻")),
                ("jpnic_handle", models.CharField(db_index=True, max_length=20, verbose_name="JPNICハンドル")),
                ("name", models.CharField(max_length=120, verbose_name="名前")),
                ("name_en", models.CharField(max_length=120, verbose_name="名前(英語)")),
                ("email", models.CharField(max_length=50, verbose_name="メールアドレス")),
                ("org", models.CharField(max_length=120, verbose_name="組織名")),
                ("org_en", models.CharField(max_length=120, verbose_name="組織名(英語)")),
                ("post_code", models.CharField(blank=True, max_length=20, verbose_name="郵便番号")),
                ("address", models.CharField(blank=True, max_length=200, verbose_name="住所")),
                ("address_en", models.CharField(blank=True, max_length=200, verbose_name="住所(英語)")),
                ("division", models.CharField(blank=True, max_length=120, verbose_name="部署")),
                ("division_en", models.CharField(blank=True, max_length=120, verbose_name="部署(英語)")),
                ("title", models.CharField(blank=True, max_length=120, verbose_name="肩書")),
                ("title_en", models.CharField(blank=True, max_length=120, verbose_name="肩書(英語)")),
                ("tel", models.CharField(blank=True, max_length=100, verbose_name="電話番号")),
                ("fax", models.CharField(blank=True, max_length=100, verbose_name="Fax")),
                ("notify_address", models.CharField(blank=True, max_length=100, verbose_name="通知アドレス")),
                ("apply_from_email", models.CharField(blank=True, max_length=100, verbose_name="申請者メールアドレス")),
                ("updated_at", models.DateTimeField(blank=True, db_index=True, null=True, verbose_name="情報更新時刻")),
                ("recep_number", models.CharField(blank=True, max_length=30, verbose_name="受付番号")),
                ("asn", models.IntegerField(verbose_name="AS番号")),
                ("ip_version", models.IntegerField(verbose_name="IP Version")),
            ],
            options={
                "ordering": ("id", "last_enabled_at", "created_at"),
                "index_together": {
                    ("created_at", "last_enabled_at", "jpnic_handle", "asn", "ip_version"),
                    ("last_enabled_at", "jpnic_handle", "asn", "ip_version"),
                },
            },
        ),
        migrations.CreateModel(
            name="AddrListTechHandle",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("jpnic_handle", models.CharField(db_index=True, max_length=20, verbose_name="JPNICハンドル")),
                ("addr_list", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="resource.addrlist")),
            ],
        ),
    ]
