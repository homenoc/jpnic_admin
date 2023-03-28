import copy
import datetime
import re
import threading

from apscheduler.schedulers.background import BackgroundScheduler
from bs4 import BeautifulSoup
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from jpnic_admin.jpnic import JPNIC, request_to_sjis, request_error, JPNICReqError
from jpnic_admin.models import JPNIC as JPNICModel
from jpnic_admin.resource.models import (
    AddrList,
    JPNICHandle,
    AddrListTechHandle,
    ResourceList,
    ResourceAddressList,
)


# 情報取得関数
def get_addr_process():
    bases = JPNICModel.objects.filter(is_active=True)
    for base in bases:
        if (
            not base.last_resource1_checked_at
        ) or datetime.datetime.now() > base.last_resource1_checked_at + datetime.timedelta(
            minutes=base.collection_interval
        ):
            t = threading.Thread(target=get_addr, args=(copy.deepcopy(base),))
            t.setDaemon(True)
            t.start()
            base.last_resource1_checked_at = timezone.now()
            base.save()


def get_resource_process():
    bases = JPNICModel.objects.filter(is_active=True)
    for base in bases:
        if (
            not base.last_resource2_checked_at
        ) or datetime.datetime.now() > base.last_resource2_checked_at + datetime.timedelta(
            minutes=base.collection_interval
        ):
            t = threading.Thread(target=get_resource, args=(copy.deepcopy(base),))
            t.setDaemon(True)
            t.start()
            base.last_resource2_checked_at = timezone.now()
            base.save()


def get_addr(base):
    GetAddr(base=base).search_list()


def get_resource(base):
    GetAddr(base=base).get_resource()


def start_getting_addr():
    # start_process()
    scheduler = BackgroundScheduler()
    scheduler.add_job(get_addr_process, "interval", seconds=5)
    scheduler.start()


def start_getting_resource():
    # start_process()
    scheduler = BackgroundScheduler()
    scheduler.add_job(get_resource_process, "interval", seconds=5)
    scheduler.start()


def convert_datetime(text, date_format="%Y/%m/%d"):
    try:
        return timezone.datetime.strptime(text, date_format)
    except:
        return None


class GetAddr(JPNIC):
    def __init__(self, base=None):
        if base is None:
            print("Error: getting base info")
            return
        super().__init__(base.asn, base.is_ipv6)
        self.base = base

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
                    res_addr_list.append(tmp_rs_addr_list)
                    tmp_rs_addr_list = {}

        now = copy.deepcopy(timezone.now())
        # 資源情報(main)
        if (
            latest_res_list is None
            or latest_res_list.assigned_addr_count != info_resource_list.get("assigned_addr_count")
            or latest_res_list.all_addr_count != info_resource_list.get("all_addr_count")
            or latest_res_list.update_date != info_resource_list.get("update_date")
        ):
            self.insert_resource_list(info=info_resource_list)
        else:
            print(now)
            latest_res_list.last_checked_at = now
            latest_res_list.save()

        # 資源IPアドレス情報(addr list)
        for res_addr_list_one in res_addr_list:
            is_new_item = True
            for latest_res_addr in latest_res_addr_list:
                if (
                    latest_res_addr.ip_address == res_addr_list_one.get("ip_address")
                    and latest_res_addr.assign_date == res_addr_list_one.get("assign_date")
                    and latest_res_addr.assigned_addr_count == res_addr_list_one.get("assigned_addr_count")
                ):
                    print(now)
                    latest_res_addr.last_checked_at = now
                    latest_res_addr.save()
                    is_new_item = False
                    break

            if is_new_item:
                self.insert_resource_address_list(info=res_addr_list_one, now=now)
        # print("resource_list", info_resource_list)
        # print("resource_address_list", res_addr_list)

    def search_list(self):
        # 最新版を取得
        last_addr_list = AddrList.objects.filter(jpnic_id=self.base.id).order_by("-last_checked_at").first()
        addr_lists = []
        addr_list_exists = False
        if last_addr_list:
            addr_lists = AddrList.objects.filter(
                jpnic_id=self.base.id, last_checked_at__exact=last_addr_list.last_checked_at
            )
            addr_list_exists = addr_lists.exists()

        # 初回時に初回取得時間を記録する
        if not addr_list_exists:
            asn_info = JPNICModel.objects.get(id=self.base.id)
            asn_info.first_checked_at = timezone.now()
            asn_info.save()

        self.init_get()
        if self.base.is_ipv6:
            self.get_contents_url("登録情報検索(IPv6)")
        else:
            self.get_contents_url("登録情報検索(IPv4)")
        res = self.session.get(self.url, headers=self.header)
        res.encoding = "Shift_JIS"
        soup = BeautifulSoup(res.text, "html.parser")
        ipaddr = ""
        is_over_list = True
        addr_info = {}
        no_update_data = True
        updated_info_lists = []
        while is_over_list:
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
            # 1000件以上か確認
            if "該当する情報が1000件を超えました (1000件まで表示します)" in res.text:
                is_over_list = True
            else:
                is_over_list = False

            soup = BeautifulSoup(res.text, "html.parser")
            addr_info = {}
            max_len = enumerate(soup.findAll("td", attrs={"class": "dataRow_mnt04"}))
            for idx, td in enumerate(soup.findAll("td", attrs={"class": "dataRow_mnt04"})):
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
                    # 1000件超え対処用
                    if max_len == idx + 1:
                        ipaddr = addr_info["ip_address"]
                    is_exist_addr_lists = False
                    # addr_listsから一致するものを抜き出す
                    for addr_list in addr_lists:
                        if (
                            addr_list.ip_address == addr_info["ip_address"]
                            and addr_list.recep_number == addr_info["recept_no"]
                        ):
                            is_exist_addr_lists = True
                            # 存在する場合は確認OKなので、last_checkedを更新する
                            updated_info_lists.append(addr_list)
                            break
                    if not is_exist_addr_lists:
                        no_update_data = False
                        break

        now = timezone.now()
        with transaction.atomic():
            # last_checked_atだけ更新
            for updated_info_list in updated_info_lists:
                updated_info_list.last_checked_at = now
                updated_info_list.save()

        # JPNICハンドルの更新処理
        if no_update_data:
            print("update only jpnic handle.")
            self.update_handle()
            return
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

        with transaction.atomic():
            # addr_listを新規登録
            addr_list_id = self.insert_addr_list(addr_info, now)
            self.insert_jpnic_handle(now, jpnic_handles)
            for tech_handle in addr_info["tech_handle"]:
                AddrListTechHandle(addr_list_id=addr_list_id, jpnic_handle=tech_handle).save()

        return
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

    def insert_jpnic_handle(self, now, jpnic_handles, recep_number=""):
        for jpnic_handle in jpnic_handles:
            new_handle_model = JPNICHandle(
                last_checked_at=now,
                jpnic_handle=jpnic_handle.get("jpnic_hdl"),
                name=jpnic_handle.get("name"),
                name_en=jpnic_handle.get("name_en"),
                email=jpnic_handle.get("email"),
                org=jpnic_handle.get("org"),
                org_en=jpnic_handle.get("org_en"),
                division=jpnic_handle.get("division"),
                division_en=jpnic_handle.get("division_en"),
                title=jpnic_handle.get("title", ""),
                title_en=jpnic_handle.get("title_en", ""),
                tel=",".join(jpnic_handle.get("phone")),
                fax=",".join(jpnic_handle.get("fax")),
                updated_at=jpnic_handle.get("update_date"),
                recep_number=recep_number,
                jpnic_id=self.base.id,
            )
            new_handle_model.save()

    def insert_addr_list(self, addr_info, now):
        insert_addrlist = AddrList(
            last_checked_at=now,
            ip_address=addr_info.get("ip_address"),
            network_name=addr_info.get("network_name"),
            assign_date=addr_info.get("assign_date"),
            return_date=addr_info.get("return_date"),
            org=addr_info.get("org"),
            org_en=addr_info.get("org_en"),
            resource_admin_short=addr_info.get("admin_org"),
            recep_number=addr_info.get("recept_no"),
            deli_number=addr_info.get("deli_no"),
            type=addr_info.get("kind1"),
            division=addr_info.get("kind2"),
            post_code=addr_info.get("postcode"),
            address=addr_info.get("address"),
            address_en=addr_info.get("address_en"),
            nameserver=",".join(addr_info.get("nameserver")),
            abuse=",".join(addr_info.get("abuse")),
            updated_at=addr_info.get("update_date"),
            admin_handle=addr_info.get("admin_handle"),
            jpnic_id=self.base.id,
        )
        insert_addrlist.save()
        return insert_addrlist.id

    def insert_resource_list(self, info):
        insert_resource_list = ResourceList(
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
            jpnic_id=self.base.id,
        )
        insert_resource_list.save()

    def insert_resource_address_list(self, info, now):
        insert_resource_address_list = ResourceAddressList(
            last_checked_at=now,
            ip_address=info.get("ip_address"),
            assign_date=info.get("assign_date"),
            assigned_addr_count=info.get("assigned_addr_count"),
            jpnic_id=self.base.id,
        )
        insert_resource_address_list.save()

    def update_handle(self):
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
            aplyDateS=self.base.first_checked_at.strftime("%Y/%m/%d"),
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
            return
        try:
            handle_info = self.get_recept(url=info["recept_no_url"])
        except:
            print("ERROR")
            return

        now = timezone.now()
        with transaction.atomic():
            # TODO: JPNICハンドルとlast_checked_at=Nullを使って対象のテーブルを探し当てて、last_checked_atを更新する
            tmp_handle = JPNICHandle.objects.get(
                jpnic_handle=handle_info["jpnic_handle"],
                last_checked_at__gt=self.base.last_resource1_checked_at,
                jpnic_id=self.base.id,
            )
            tmp_handle.last_checked_at = now
            tmp_handle.save()
            self.insert_jpnic_handle(now, jpnic_handles=[].append(handle_info), recep_number=info["recept_no"])
