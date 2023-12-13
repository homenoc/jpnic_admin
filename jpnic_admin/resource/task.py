import copy
import datetime
import re
import sys
import time
import traceback

from bs4 import BeautifulSoup
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from jpnic_admin.jpnic import JPNIC, request_to_sjis, request_error, JPNICReqError
from jpnic_admin.models import JPNIC as JPNICModel
from jpnic_admin.log.models import Task as TaskModel
from jpnic_admin.log.models import TaskError as TaskErrorModel
from jpnic_admin.resource.models import (
    AddrList,
    JPNICHandle,
    AddrListTechHandle,
    ResourceList,
    ResourceAddressList,
)


def text_check(text="", org=""):
    if org in settings.ORG_FILTER or len(settings.ORG_FILTER) == 0:
        return text
    return ""


def manual_task(type1=None, jpnic_id=None):
    if not type1 or not jpnic_id:
        return
    base = JPNICModel.objects.get(is_active=True, id=jpnic_id)
    latest_log = TaskModel.objects.filter(jpnic_id=base.id, type1=type1).order_by("-last_checked_at").first()
    now = copy.deepcopy(timezone.now())
    exec_task(type1, base, latest_log, now)


def get_task(type1=None):
    if not type1:
        return
    bases = JPNICModel.objects.filter(is_active=True)
    for base in bases:
        if not base.is_active:
            continue
        now = copy.deepcopy(timezone.now())
        latest_log = TaskModel.objects.filter(type1=type1, jpnic_id=base.id).order_by("-last_checked_at").first()
        #  count-fail_countが1以上の場合はすっ飛ばす　(Only 資源情報)<=負荷軽減策
        if type1 == "資源情報" and latest_log is not None:
            now_zero = datetime.datetime.combine(now, datetime.time(0, 0, 0))
            if (now_zero < latest_log.last_checked_at) & (latest_log.count - latest_log.fail_count > 0):
                continue
        if (not settings.DEBUG) and base.collection_interval == 0:
            continue
        if (not latest_log) or now > latest_log.last_checked_at + datetime.timedelta(minutes=base.collection_interval):
            print(base.asn, type1, "START")
            exec_task(type1, base, latest_log, now)
            print(base.asn, "END")
        time.sleep(1)


def exec_task(type1, base, log, now):
    fail = None
    base_copied = copy.deepcopy(base)
    log_copied = copy.deepcopy(log)
    try:
        if type1 == "アドレス情報":
            GetAddr(base=base_copied, log=log_copied, now=now).search_list()
        elif type1 == "資源情報":
            GetAddr(base=base_copied, log=log_copied, now=now).get_resource()
    except Exception as e:
        exc = sys.exception()
        fail = {
            "type": str(type(e)),
            "message": "%s" % (str(traceback.format_tb(exc.__traceback__)))
        }
    update_task_log(type1, base, log, now, fail)


@transaction.atomic
def update_task_log(type1, base, latest_log, now, fail):
    # ログが今日分かどうか確認
    if latest_log:
        today_start_time = datetime.datetime.combine(now, datetime.time(0, 0, 0))
        today_end_time = datetime.datetime.combine(now, datetime.time(23, 59, 59))
        if today_start_time <= latest_log.created_at <= today_end_time:
            latest_log.last_checked_at = now
            latest_log.count = latest_log.count + 1
            if fail:
                latest_log.fail_count = latest_log.fail_count + 1
                TaskErrorModel(
                    created_at=now, type=fail.get("type"), message=fail.get("message"), task_id=latest_log.id
                ).save()
            latest_log.save()
            return

    fail_count = 0
    if fail:
        fail_count = 1
    taskModel = TaskModel(
        created_at=now,
        last_checked_at=now,
        jpnic_id=base.id,
        type1=type1,
        count=1,
        fail_count=fail_count,
    )
    taskModel.save()
    if fail:
        TaskErrorModel(created_at=now, type=fail.get("type"), message=fail.get("message"), task_id=taskModel.id).save()


def convert_datetime(text, date_format="%Y/%m/%d"):
    try:
        return timezone.datetime.strptime(text, date_format)
    except:
        return None


class GetAddr(JPNIC):
    def __init__(self, base=None, log=None, now=None):
        super().__init__(base=base)
        self.base = base
        self.log = log
        self.now = now

    @transaction.atomic
    def get_resource(self):
        self.init_get()
        self.get_contents_url("資源管理者情報")
        res = self.session.get(self.url, headers=self.header)
        res.encoding = "Shift_JIS"
        soup = BeautifulSoup(res.text, "html.parser")
        resource_info = soup.select("table > tr > td > table > tr > td > table > tr > td > table")
        if len(resource_info) != 2:
            print("ERROR")
            return

        latest_res_list = ResourceList.objects.filter(jpnic_id=self.base.id).order_by("-last_checked_at").first()
        last_res_addr = ResourceAddressList.objects.filter(jpnic_id=self.base.id).order_by("-last_checked_at").first()
        latest_res_addr_list = []
        if last_res_addr:
            latest_res_addr_list = ResourceAddressList.objects.filter(
                jpnic_id=self.base.id, last_checked_at__exact=last_res_addr.last_checked_at
            )

        # メインの資源管理者情報
        info_resource_list = {}
        resource_info_td = resource_info[0].findAll("td")
        for idx, td in enumerate(resource_info_td):
            if idx == 0:
                continue
            prev_text = resource_info_td[idx - 1].text.strip()
            text = td.text.strip()
            if prev_text == "資源管理者番号":
                info_resource_list["resource_no"] = text
            elif prev_text == "資源管理者略称":
                info_resource_list["resource_admin_short"] = text
            elif prev_text == "管理組織名":
                info_resource_list["org"] = text
            elif prev_text == "Organization":
                info_resource_list["org_en"] = text
            elif prev_text == "郵便番号":
                info_resource_list["postcode"] = text
            elif prev_text == "住所":
                info_resource_list["address"] = text
            elif prev_text == "Address":
                info_resource_list["address_en"] = text
            elif prev_text == "電話番号":
                info_resource_list["tel"] = text
            elif prev_text == "FAX番号":
                info_resource_list["fax"] = text
            elif prev_text == "資源管理責任者":
                info_resource_list["admin_handle"] = text
            elif prev_text == "連絡担当窓口":
                info_resource_list["email"] = text
            elif prev_text == "一般問い合わせ窓口":
                info_resource_list["common_email"] = text
            elif prev_text == "資源管理者通知アドレス":
                info_resource_list["notify_email"] = text
            elif prev_text == "アサインメントウィンドウサイズ":
                info_resource_list["assignment_size"] = text[1:]
            elif prev_text == "管理開始日":
                info_resource_list["start_date"] = convert_datetime(text=text)
            elif prev_text == "管理終了日":
                info_resource_list["end_date"] = convert_datetime(text=text)
            elif prev_text == "最終更新日":
                info_resource_list["update_date"] = convert_datetime(text=text)
        # 資源情報
        res_addr_list = []
        tmp_rs_addr_list = {}
        resource_info_td = resource_info[1].findAll("td")
        for idx, td in enumerate(resource_info_td):
            text = td.text.strip()
            # 総利用率
            if idx == 2:
                info_resource_list["assigned_addr_count"] = int(re.findall("(?<=\().+?(?=\))", text)[0].split("/")[0])
                info_resource_list["all_addr_count"] = int(re.findall("(?<=\().+?(?=\))", text)[0].split("/")[1])
            # AD ratio
            elif idx == 5:
                info_resource_list["ad_ratio"] = float(text)
            elif idx > 8:
                if idx % 3 == 0:
                    tmp_rs_addr_list["ip_address"] = text.split("\n")[0].strip()
                if idx % 3 == 1:
                    tmp_rs_addr_list["assign_date"] = convert_datetime(text=text)
                if idx % 3 == 2:
                    tmp_rs_addr_list["assigned_addr_count"] = int(re.findall("(?<=\().+?(?=\))", text)[0].split("/")[0])
                    tmp_rs_addr_list["all_addr_count"] = int(re.findall("(?<=\().+?(?=\))", text)[0].split("/")[1])
                    res_addr_list.append(tmp_rs_addr_list)
                    tmp_rs_addr_list = {}

        # 資源情報(main)
        if (
            latest_res_list is None
            or latest_res_list.assigned_addr_count != info_resource_list.get("assigned_addr_count")
            or latest_res_list.all_addr_count != info_resource_list.get("all_addr_count")
            or latest_res_list.update_date != info_resource_list.get("update_date")
        ):
            self.insert_resource_list(info=info_resource_list, html=soup.prettify())
        else:
            latest_res_list.last_checked_at = self.now
            latest_res_list.html_source = soup.prettify()
            latest_res_list.save()

        # 資源IPアドレス情報(addr list)
        for res_addr_list_one in res_addr_list:
            is_new_item = True
            for latest_res_addr in latest_res_addr_list:
                if (
                    latest_res_addr.ip_address == res_addr_list_one.get("ip_address")
                    and latest_res_addr.all_addr_count == res_addr_list_one.get("all_addr_count")
                    and latest_res_addr.assign_date == res_addr_list_one.get("assign_date")
                    and latest_res_addr.assigned_addr_count == res_addr_list_one.get("assigned_addr_count")
                ):
                    latest_res_addr.last_checked_at = self.now
                    latest_res_addr.save()
                    is_new_item = False
                    break

            if is_new_item:
                self.insert_resource_address_list(info=res_addr_list_one)

    @transaction.atomic
    def search_list(self):
        # 最新版を取得
        print("================")
        print(self.base.asn, "now", self.now)
        last_addr_list = AddrList.objects.filter(jpnic_id=self.base.id).order_by("-last_checked_at").first()
        addr_lists = []
        if last_addr_list:
            addr_lists = AddrList.objects.filter(
                jpnic_id=self.base.id, last_checked_at__exact=last_addr_list.last_checked_at
            )

        self.init_get()
        if self.base.is_ipv6:
            self.get_contents_url("登録情報検索(IPv6)")
        else:
            self.get_contents_url("登録情報検索(IPv4)")
        res = self.session.get(self.url, headers=self.header)
        res.encoding = "Shift_JIS"
        soup = BeautifulSoup(res.text, "html.parser")
        ipaddr = ""
        addr_info = {}
        # 存在しない情報のアップデート
        update_info_lists = []
        # 日付のみのアップデート
        date_update_info_only_lists = []
        page = 0
        while True:
            page += 1
            req = dict(
                destdisp=soup.find("input", attrs={"name": "destdisp"})["value"],
                ipaddr=ipaddr,
                sizeS="",
                sizeE="",
                netwrkName="",
                regDateS="",
                regDateE="",
                rtnDateS="",
                rtnDateE="",
                organizationName="",
                resceAdmSnm=soup.find("input", attrs={"name": "resceAdmSnm"})["value"],
                recepNo="",
                deliNo="",
                action="　検索　",
            )
            req_data = request_to_sjis(req)
            post_url = soup.find("form")["action"].split("/")[-1]
            res = self.session.post(self.base_url + "/" + post_url, data=req_data, headers=self.header)
            res.encoding = "Shift_JIS"

            soup = BeautifulSoup(res.text, "html.parser")
            addr_info = {}
            for idx, td in enumerate(soup.findAll("td", attrs={"class": "dataRow_mnt04"})):
                is_exist_addr_lists = False
                text = td.text.strip()
                if ((not self.base.is_ipv6) and (0 <= idx < 11)) or (self.base.is_ipv6 and (0 <= idx < 9)):
                    continue
                if ((not self.base.is_ipv6) and (idx % 11 == 0)) or (self.base.is_ipv6 and (idx % 9 == 0)):
                    addr_info["ip_address"] = text
                    addr_info["ip_address_url"] = td.find("a")["href"]
                elif (not self.base.is_ipv6) and (idx % 11 == 1):
                    addr_info["size"] = text
                elif ((not self.base.is_ipv6) and (idx % 11 == 2)) or (self.base.is_ipv6 and (idx % 9 == 1)):
                    addr_info["network_name"] = text
                elif ((not self.base.is_ipv6) and (idx % 11 == 3)) or (self.base.is_ipv6 and (idx % 9 == 2)):
                    addr_info["assign_date"] = convert_datetime(text=text)
                elif ((not self.base.is_ipv6) and (idx % 11 == 4)) or (self.base.is_ipv6 and (idx % 9 == 3)):
                    addr_info["return_date"] = convert_datetime(text=text)
                elif ((not self.base.is_ipv6) and (idx % 11 == 5)) or (self.base.is_ipv6 and (idx % 9 == 4)):
                    addr_info["org"] = text
                elif ((not self.base.is_ipv6) and (idx % 11 == 6)) or (self.base.is_ipv6 and (idx % 9 == 5)):
                    addr_info["admin_org"] = text
                elif ((not self.base.is_ipv6) and (idx % 11 == 7)) or (self.base.is_ipv6 and (idx % 9 == 6)):
                    addr_info["recept_no"] = text
                elif ((not self.base.is_ipv6) and (idx % 11 == 8)) or (self.base.is_ipv6 and (idx % 9 == 7)):
                    addr_info["deli_no"] = text
                elif ((not self.base.is_ipv6) and (idx % 11 == 9)) or (self.base.is_ipv6 and (idx % 9 == 8)):
                    addr_info["kind1"] = text
                elif (not self.base.is_ipv6) and (idx % 11 == 10):
                    addr_info["kind2"] = text
                    # page遷移時に重複除去を行う
                    if page > 1:
                        if addr_info in date_update_info_only_lists or addr_info in update_info_lists:
                            continue
                    # addr_listsから一致するものを抜き出す
                    # last_checked更新listの判定
                    for addr_list in addr_lists:
                        if (
                            addr_list.ip_address == addr_info["ip_address"]
                            and addr_list.division == addr_info["kind2"]
                            and addr_list.recep_number == addr_info["recept_no"]
                        ):
                            is_exist_addr_lists = True
                            # 存在する場合は確認OKなので、last_checkedを更新する
                            date_update_info_only_lists.append(addr_list)
                            break
                    if not is_exist_addr_lists:
                        update_info_lists.append(copy.deepcopy(addr_info))
            # 1000件以上ではない場合は抜ける
            if "該当する情報が1000件を超えました (1000件まで表示します)" not in res.text:
                break
            else:
                ipaddr = addr_info["ip_address"].split("/")[0] + "-255.255.255.255"

        # print("update_info_lists", len(update_info_lists))
        # print("date_update_info_only_lists", len(date_update_info_only_lists))
        if (
            (not self.base.option_collection_no_filter)
            and len(addr_lists) != 0
            and len(date_update_info_only_lists) == 0
        ):
            return

        # last_checked_atのみ更新
        for date_update_info_only_list in date_update_info_only_lists:
            date_update_info_only_list.last_checked_at = self.now
        AddrList.objects.bulk_update(date_update_info_only_lists, fields=["last_checked_at"])

        # すべて更新済みの場合は、JPNICハンドルの更新処理を行う
        if len(date_update_info_only_lists) != 0 and len(update_info_lists) == 0:
            print("update only jpnic handle.")
            self.update_handle()
            return

        if len(update_info_lists) == 0:
            return

        addr_info = update_info_lists[0]
        addr_info = self.get_detail_address(url=addr_info["ip_address_url"], info=addr_info)

        jpnic_handles = []
        # 管理者連絡窓口
        # データベースに含まれている場合はSKIP(最新情報は申請履歴より更新)
        if not JPNICHandle.objects.filter(jpnic_id=self.base.id, jpnic_handle=addr_info["admin_handle"]).exists():
            try:
                jpnic_handles.append(self.get_jpnic_handle(jpnic_handle=addr_info["admin_handle"]))
            except JPNICReqError as exc:
                print(exc)

        # 技術連絡担当者
        for tech_jpnic in addr_info["tech_handle"]:
            if tech_jpnic == addr_info["admin_handle"]:
                continue
            # データベースに含まれている場合はSKIP
            if JPNICHandle.objects.filter(jpnic_id=self.base.id, jpnic_handle=tech_jpnic).exists():
                continue
            try:
                jpnic_handles.append(self.get_jpnic_handle(jpnic_handle=tech_jpnic))
            except JPNICReqError as exc:
                print(exc)

        # addr_listを新規登録
        addr_list_id = self.insert_addr_list(addr_info)
        self.update_latest_data(handles=jpnic_handles)
        for tech_handle in addr_info["tech_handle"]:
            AddrListTechHandle(addr_list_id=addr_list_id, jpnic_handle=tech_handle).save()

        # if len(infos) == 0:
        #     raise JPNICReqError("該当するデータが見つかりませんでした。", res.text)

    def get_detail_address(self, url=None, network_id=None, info={}):
        if network_id is None:
            self.url = settings.JPNIC_BASE_URL + url
        else:
            self.url = self.base_url + "/entryinfo_v4.do?netwrk_id=" + network_id
        res = self.session.get(self.url, headers=self.header)
        res.encoding = "Shift_JIS"
        soup = BeautifulSoup(res.text, "html.parser")
        request_error(soup, res.text)
        addr_info = soup.select("table > tr > td > table > tr > td > table > tr > td > table")[0].findAll(
            "td", attrs={"class": "dataRow05"}
        )
        tech_jpnic_info = []
        tech_jpnic_info_url = []
        abuse = []
        nameserver = []
        base_title = ""
        for idx, td in enumerate(addr_info):
            if idx == 0:
                continue
            prev_text = addr_info[idx - 1].text.strip()
            text = td.text.strip()
            if prev_text == "組織名":
                info["org"] = text
            elif prev_text == "Organization":
                info["org_en"] = text
            elif prev_text == "郵便番号":
                info["postcode"] = text
            elif prev_text == "住所":
                info["address"] = text
            elif prev_text == "Address":
                info["address_en"] = text
            elif prev_text == "管理者連絡窓口":
                info["admin_handle"] = text
                info["admin_jpnic_url"] = td.find("a").get("href")
            elif prev_text == "技術連絡担当者":
                base_title = prev_text
                tech_jpnic_info.append(text)
                tech_jpnic_info_url.append(td.find("a").get("href"))
            elif prev_text == "Abuse":
                base_title = prev_text
                abuse.append(text)
            elif prev_text == "ネームサーバ":
                base_title = prev_text
                nameserver.append(text)
            elif prev_text == "通知アドレス":
                base_title = prev_text
                info["notify_address"] = text
            elif prev_text == "最終更新":
                info["update_date"] = convert_datetime(text=text, date_format="%Y/%m/%d %H:%M")
            elif prev_text == "" and idx % 2 == 1:
                if base_title == "技術連絡担当者":
                    tech_jpnic_info.append(text)
                    tech_jpnic_info_url.append(td.find("a").get("href"))
                elif base_title == "ネームサーバ":
                    nameserver.append(text)
        info["tech_handle"] = tech_jpnic_info
        info["tech_jpnic_url"] = tech_jpnic_info_url
        info["abuse"] = abuse
        info["nameserver"] = nameserver

        return info

    def get_jpnic_handle(self, jpnic_handle=""):
        res = self.session.get(
            self.base_url + "/" + "entryinfo_handle.do?jpnic_hdl=" + jpnic_handle,
            headers=self.header,
        )
        res.encoding = "Shift_JIS"
        soup = BeautifulSoup(res.text, "html.parser")
        jpnic_handle_info = soup.select("table > tr > td > table > tr > td > table")[0].findAll("td")
        handle_info = {"jpnic_hdl": jpnic_handle}
        phone = []
        fax = []
        base_title = ""

        for idx, td in enumerate(jpnic_handle_info):
            if idx == 0:
                continue
            prev_text = jpnic_handle_info[idx - 1].text.strip()
            text = td.text.strip()

            if prev_text == "グループハンドル":
                handle_info["kind"] = "group"
            if prev_text == "JPNICハンドル":
                handle_info["kind"] = "person"
            if prev_text in ("グループ名", "氏名"):
                handle_info["name"] = text
            if prev_text in ("Group Name", "Last, First"):
                handle_info["name_en"] = text
            if prev_text in ("電子メール", "電子メイル"):
                handle_info["email"] = text
            if prev_text == "組織名":
                handle_info["org"] = text
            if prev_text == "Organization":
                handle_info["org_en"] = text
            if prev_text == "部署":
                handle_info["division"] = text
            if prev_text == "Division":
                handle_info["division_en"] = text
            if prev_text == "肩書":
                handle_info["title"] = text
            if prev_text == "Title":
                handle_info["title_en"] = text
            if prev_text == "電話番号":
                base_title = prev_text
                phone.extend(text.split())
            if prev_text in ("Fax番号", "FAX番号"):
                base_title = "FAX番号"
                fax.extend(text.split())
            if prev_text == "最終更新":
                base_title = prev_text
                handle_info["update_date"] = convert_datetime(text=text, date_format="%Y/%m/%d %H:%M")
            if prev_text == "" and idx % 2 == 1:
                if base_title == "電話番号":
                    phone.extend(text.split())
                elif base_title == "Fax番号":
                    fax.extend(text.split())
        handle_info["phone"] = phone
        handle_info["fax"] = fax
        if handle_info["org"] == "" and handle_info["name"] == "":
            raise JPNICReqError("該当のJPNIC Handleが見つかりませんでした。", res.text)
        return handle_info

    def get_recept(self, url=None, recept_no=None, info={}):
        if recept_no is None:
            self.url = settings.JPNIC_BASE_URL + url
        else:
            self.url = self.base_url + "/applyform.do?recepNo=" + recept_no
        res = self.session.get(self.url, headers=self.header)
        res.encoding = "Shift_JIS"
        soup = BeautifulSoup(res.text, "html.parser")
        request_error(soup, res.text)
        if "ネットワーク名" in res.text:
            print("IPv4割当報告申請")
        elif "変更理由" in res.text:
            print("IPv4ネットワーク情報変更申請")
        elif "グループハンドル/JPNICハンドル" in res.text:
            # print("グループハンドル/JPNICハンドル")
            for line in soup.find_all("pre")[0].text.splitlines():
                line_split = line.split("：")
                title = line_split[0]
                body = "".join(title[1:]).strip()
                if title == "グループハンドル/JPNICハンドル":
                    if "JPNICハンドル" in body:
                        info["kind"] = "person"
                    elif "グループハンドル" in body:
                        info["kind"] = "group"
                elif title == "グループハンドル（またはJPNICハンドル）":
                    info["jpnic_handle"] = body
                elif title == "グループ名（または氏名）":
                    info["name"] = body
                elif title == "Group Name（Last, First)":
                    info["name_en"] = body
                elif title == "電子メール":
                    info["email"] = body
                elif title == "組織名":
                    info["org"] = body
                elif title == "Organization":
                    info["org_en"] = body
                elif title == "住所":
                    info["address"] = body
                elif title == "Address":
                    info["address_en"] = body
                elif title == "部署":
                    info["division"] = body
                elif title == "Division":
                    info["division_en"] = body
                elif title == "肩書":
                    info["title"] = body
                elif title == "Title":
                    info["title_en"] = body
                elif title == "電話番号":
                    info["tel"] = body
                elif title == "FAX番号":
                    info["fax"] = body
                elif title == "通知アドレス":
                    info["notice_address"] = body
                elif title == "申請者メールアドレス":
                    info["fax"] = body
        return info

    def insert_jpnic_handle(self, jpnic_handles):
        for jpnic_handle in jpnic_handles:
            org_name = jpnic_handle.get("org")
            recep_number = jpnic_handle.get("recep_number", "")
            new_handle_model = JPNICHandle(
                created_at=self.now,
                last_checked_at=self.now,
                jpnic_handle=jpnic_handle.get("jpnic_hdl"),
                name=text_check(text=jpnic_handle.get("name"), org=org_name),
                name_en=text_check(text=jpnic_handle.get("name_en"), org=org_name),
                email=text_check(text=jpnic_handle.get("email"), org=org_name),
                org=org_name,
                org_en=jpnic_handle.get("org_en"),
                division=text_check(text=jpnic_handle.get("division"), org=org_name),
                division_en=text_check(text=jpnic_handle.get("division_en"), org=org_name),
                title=text_check(text=jpnic_handle.get("title"), org=org_name),
                title_en=text_check(text=jpnic_handle.get("title_en"), org=org_name),
                tel=text_check(text=",".join(jpnic_handle.get("phone")), org=org_name),
                fax=text_check(text=",".join(jpnic_handle.get("fax")), org=org_name),
                updated_at=jpnic_handle.get("update_date"),
                recep_number=recep_number,
                jpnic_id=self.base.id,
            )
            new_handle_model.save()

    def insert_addr_list(self, addr_info):
        org_name = addr_info.get("org")
        insert_addrlist = AddrList(
            created_at=self.now,
            last_checked_at=self.now,
            ip_address=addr_info.get("ip_address"),
            network_name=addr_info.get("network_name"),
            assign_date=addr_info.get("assign_date"),
            return_date=addr_info.get("return_date"),
            org=org_name,
            org_en=addr_info.get("org_en"),
            resource_admin_short=addr_info.get("admin_org"),
            recep_number=addr_info.get("recept_no"),
            deli_number=addr_info.get("deli_no"),
            type=addr_info.get("kind1"),
            division=addr_info.get("kind2"),
            post_code=text_check(text=addr_info.get("postcode"), org=org_name),
            address=text_check(text=addr_info.get("address"), org=org_name),
            address_en=text_check(text=addr_info.get("address_en"), org=org_name),
            nameserver=",".join(addr_info.get("nameserver")),
            abuse=",".join(addr_info.get("abuse")),
            updated_at=addr_info.get("update_date"),
            admin_handle=addr_info.get("admin_handle"),
            jpnic_id=self.base.id,
        )
        insert_addrlist.save()
        return insert_addrlist.id

    def insert_resource_list(self, info, html=""):
        insert_resource_list = ResourceList(
            created_at=self.now,
            last_checked_at=self.now,
            resource_no=info.get("resource_no"),
            resource_admin_short=info.get("resource_admin_short"),
            org=info.get("org"),
            org_en=info.get("org_en"),
            post_code=info.get("postcode"),
            address=info.get("address"),
            address_en=info.get("address_en"),
            tel=info.get("tel"),
            fax=info.get("fax"),
            admin_handle=info.get("admin_handle"),
            email=info.get("email"),
            common_email=info.get("common_email"),
            notify_email=info.get("notify_email"),
            assignment_size=info.get("assignment_size"),
            start_date=info.get("start_date"),
            end_date=info.get("end_date"),
            update_date=info.get("update_date"),
            all_addr_count=info.get("all_addr_count"),
            assigned_addr_count=info.get("assigned_addr_count"),
            ad_ratio=info.get("ad_ratio"),
            html_source=html,
            jpnic_id=self.base.id,
        )
        insert_resource_list.save()

    def insert_resource_address_list(self, info):
        insert_resource_address_list = ResourceAddressList(
            created_at=self.now,
            last_checked_at=self.now,
            ip_address=info.get("ip_address"),
            assign_date=info.get("assign_date"),
            all_addr_count=info.get("all_addr_count"),
            assigned_addr_count=info.get("assigned_addr_count"),
            jpnic_id=self.base.id,
        )
        insert_resource_address_list.save()

    def update_handle(self):
        # 最初に取得を始めた日付を取得
        first_task_info = (
            TaskModel.objects.filter(jpnic_id=self.base.id, type1="アドレス情報").order_by("last_checked_at").first()
        )
        if first_task_info is None:
            print("ログデータがありません")

        self.get_contents_url("申請一覧")
        res = self.session.get(self.url, headers=self.header)
        res.encoding = "Shift_JIS"
        soup = BeautifulSoup(res.text, "html.parser")
        req = dict(
            destdisp=soup.find("input", attrs={"name": "destdisp"})["value"],
            sort=1,
            startRecepNo="",
            endRecepNo="",
            deliNo="",
            aplyKind="",
            aplyClass=501,
            resceAdmSnm="",
            aplyDateS=first_task_info.created_at.strftime("%Y/%m/%d"),
            aplyDateE="",
            completDateS="",
            completDateE="",
            statusId="",
            order="DESC",
        )
        req_data = request_to_sjis(req)
        post_url = soup.find("form")["action"].split("/")[-1]
        res = self.session.post(self.base_url + "/" + post_url, data=req_data, headers=self.header)
        res.encoding = "Shift_JIS"
        soup = BeautifulSoup(res.text, "html.parser")
        handle_lists = JPNICHandle.objects.filter(jpnic_id=self.base.id)
        info = {}
        is_find = True
        for idx, td in enumerate(soup.find_all("table")[6].findAll("td", attrs={"class": "dataRow_mnt01"})):
            text = td.text.strip()
            if 0 <= idx < 8:
                continue
            if idx % 8 == 0:
                info["recept_no"] = text
                info["recept_no_url"] = td.find("a")["href"]
            elif idx % 8 == 1:
                info["deli_no"] = text
            elif idx % 8 == 2:
                info["kind1"] = text
            elif idx % 8 == 3:
                info["kind2"] = text
            elif idx % 8 == 4:
                info["apply_people"] = convert_datetime(text)
            elif idx % 8 == 5:
                info["apply_date"] = convert_datetime(text)
            elif idx % 8 == 6:
                info["complete_date"] = convert_datetime(text)
            elif idx % 8 == 7:
                info["status"] = text
                for handle_list in handle_lists:
                    # recept_noがない場合は飛ばす
                    if handle_list.recep_number != info["recept_no"]:
                        is_find = False
                        break
                if not is_find:
                    break
        if is_find:
            print("SKIP: update jpnic_handle")
            self.update_latest_data()
            return
        try:
            handle_info = self.get_recept(url=info["recept_no_url"])
        except:
            print("ERROR")
            return

        handle_info["recep_number"] = info["recept_no"]
        self.update_latest_data(handles=[].append(handle_info))

    # ハンドル系の最新日付アップデート処理
    def update_latest_data(self, handles=None):
        last_handle = JPNICHandle.objects.filter(jpnic_id=self.base.id).order_by("-last_checked_at").first()
        base_handle_lists = []
        if last_handle:
            base_handle_lists = JPNICHandle.objects.filter(
                jpnic_id=self.base.id, last_checked_at__exact=last_handle.last_checked_at
            )
        handle_update_lists = []

        if handles:
            for base_handle in base_handle_lists:
                is_exists = False
                for input_handle in handles:
                    if check_handle(input_handle, base_handle.jpnic_handle):
                        is_exists = True
                        break
                if not is_exists:
                    handle_update_lists.append(base_handle)
            for handle in handles:
                self.insert_jpnic_handle(handle)
        else:
            handle_update_lists = base_handle_lists
        for handle_update in handle_update_lists:
            handle_update.last_checked_at = self.now
        JPNICHandle.objects.bulk_update(handle_update_lists, fields=["last_checked_at"])


def check_handle(target_handle, base_jpnic_handle):
    if 'jpnic_handle' in target_handle:
        return target_handle["jpnic_handle"] == base_jpnic_handle
    else:
        return target_handle["jpnic_hdl"] == base_jpnic_handle
