import datetime

from django.conf import settings
from slack_sdk import WebhookClient

from jpnic_admin.jpnic import verify_expire_ca, verify_expire_p12_file
from jpnic_admin.models import JPNIC as JPNICModel


class NoticeResource:
    def to_slack(self):
        webhook = WebhookClient(settings.SLACK_WEBHOOK_URL)
        download_base_url = settings.DOMAIN_URL
        jpnic_models = JPNICModel.objects.filter(is_active=True)
        now = datetime.datetime.now()
        now_str = now.strftime('%Y-%m-%d')
        ids = []
        for jpnic_model in jpnic_models:
            ids.append(str(jpnic_model.id))
        response = webhook.send(
            text="fallback",
            blocks=[
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "資源情報のダウンロード",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*データ取得日付*: `" + now_str + "`"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": now_str + "のデータです。下記よりダウンロードできます。:memo:"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "ダウンロード(" + now_str + ")",
                                "emoji": True
                            },
                            "url": download_base_url + "/info/resource/export/?jpnic_ids=" + ','.join(
                                ids) + "&select_date=" + now_str
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "ダウンロード(現時点)",
                                "emoji": True
                            },
                            "url": download_base_url + "/info/resource/export/?jpnic_ids=" + ','.join(
                                ids) + "&select_date="
                        }
                    ]
                },
                {
                    "type": "divider"
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": ":memo: ダウンロードデータはzipファイルになります。"
                        }
                    ]
                }
            ]
        )
        assert response.status_code == 200
        assert response.body == "ok"


class NoticeCertExpired:
    def get_icon(self, expire_type=0):
        if expire_type == 1:
            return "warning"
        elif expire_type == 2:
            return "no_entry"
        return "white_check_mark"

    def to_slack(self):
        webhook = WebhookClient(settings.SLACK_WEBHOOK_URL)
        ca_expiry_date = verify_expire_ca()
        cert_array = []
        for jpn in JPNICModel.objects.filter(is_active=True):
            p12_expire = verify_expire_p12_file(p12_base64=jpn.p12_base64, p12_pass=jpn.p12_pass)
            cert_array.append({
                "type": "mrkdwn",
                "text": ":" + self.get_icon(
                    expire_type=p12_expire.get("expire", 0)) + ": *" + jpn.name + ":* " + p12_expire.get(
                    "after").strftime('%Y-%m-%d %H:%M:%S')
            })

        response = webhook.send(
            text="fallback",
            blocks=[
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "証明書期限通知",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*ルート証明書*"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": ":" + self.get_icon(expire_type=ca_expiry_date['expire']) + ": *ルート証明書*: " +
                                    ca_expiry_date['after']
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*各AS毎の証明書*"
                    }
                },
                {
                    "type": "context",
                    "elements": cert_array
                },
                {
                    "type": "divider"
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": ":white_check_mark: 更新の必要なし"
                        },
                        {
                            "type": "mrkdwn",
                            "text": ":warning: 90日未満で証明書失効"
                        },
                        {
                            "type": "mrkdwn",
                            "text": ":no_entry: 失効済み"
                        }
                    ]
                }
            ]
        )
        assert response.status_code == 200
        assert response.body == "ok"
