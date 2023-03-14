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
def start_process():
    base_objects = JPNICModel.objects.filter(is_active=True)
    for base_object in base_objects:
        if datetime.datetime.now() > base_object.last_resource1_checked_at + datetime.timedelta(
            minutes=base_object.collection_interval
        ):
            t = threading.Thread(
                target=get_detail_address,
                args=(copy.deepcopy(base_object),),
            )
            print("before", base_object.last_resource1_checked_at)
            t.setDaemon(True)
            t.start()
            now = timezone.now()
            print("now", now)
            base_object.last_resource1_checked_at = now
            base_object.save()


def start_resource_process():
    base_objects = JPNICModel.objects.filter(is_active=True)
    for base_object in base_objects:
        if datetime.datetime.now() > base_object.last_resource2_checked_at + datetime.timedelta(
            minutes=base_object.collection_interval
        ):
            t = threading.Thread(target=get_resource, args=base_object)
            t.setDaemon(True)
            t.start()
            base_object.last_resource2_checked_at = timezone.now()
            base_object.save()


def get_detail_address(base):
    GetAddr(base=base).search_list()


def get_resource(base):
    GetAddr(base=base).get_resource()


def start():
    # start_process()
    scheduler = BackgroundScheduler()
    scheduler.add_job(start_process, "interval", seconds=5)
    scheduler.start()


def start_resource():
    # start_process()
    scheduler = BackgroundScheduler()
    scheduler.add_job(start_resource_process, "interval", seconds=5)
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

        latest_res_list = ResourceList.objects.filter(
            asn_id_id=self.base.id, last_checked_at__gt=self.base.last_resource2_checked_at
        )
        latest_res_addr_list = ResourceAddressList.objects.filter(
            asn_id_id=self.base.id, last_checked_at__gt=self.base.last_resource2_checked_at
        )
        print("latest_res_list", latest_res_list)
        print("latest_res_addr_list", latest_res_addr_list)
        print("latest_res_addr_list", latest_res_addr_list.count())

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

        with transaction.atomic():
            if latest_res_list.count() == 0:
                self.insert_resource_list(info=info_resource_list)
            elif latest_res_list.count() > 1:
                print("error: Count error...")
            else:
                if (
                    latest_res_list[0].assigned_addr_count != info_resource_list.get("assigned_addr_count")
                    or latest_res_list[0].all_addr_count != info_resource_list.get("all_addr_count")
                    or latest_res_list[0].update_date != info_resource_list.get("update_date")
                ):
                    latest_res_list[0].last_enabled_at = timezone.now()
                    latest_res_list[0].save()
                    self.insert_resource_list(info=info_resource_list)

            for res_addr_list_one in res_addr_list:
                if len(latest_res_addr_list) == 0:
                    self.insert_resource_address_list(info=res_addr_list_one)
                else:
                    for latest_res_addr in latest_res_addr_list:
                        if latest_res_addr.ip_address == res_addr_list_one.get("ip_address") and (
                            latest_res_addr.assign_date != res_addr_list_one.get("assign_date")
                            or latest_res_addr.assigned_addr_count != res_addr_list_one.get("assigned_addr_count")
                        ):
                            latest_res_addr.last_enabled_at = timezone.now()
                            latest_res_addr.save()
                            self.insert_resource_address_list(info=res_addr_list_one)

        print("resource_list", info_resource_list)
        print("resource_address_list", res_addr_list)

    def search_list(self):
        addr_lists = AddrList.objects.filter(
            asn=self.base.asn, ip_version=self.get_ip_version(), last_checked_at__gt=self.base.last_resource1_checked_at
        )
        addr_list_exists = addr_lists.exists()
        # 初回時に初回取得時間を記録する
        if addr_lists is None or addr_list_exists is False:
            asn_info = JPNICModel.objects.get(is_active=True, asn=self.base.asn)
            asn_info.first_checked_at = timezone.now()
            asn_info.save()

        self.init_get()
        if self.is_ipv6:
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
        with transaction.atomic():
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
                    if ((not self.is_ipv6) and (0 <= idx < 11)) or (self.is_ipv6 and (0 <= idx < 9)):
                        continue
                    if ((not self.is_ipv6) and (idx % 11 == 0)) or (self.is_ipv6 and (idx % 9 == 0)):
                        addr_info["ip_address"] = text
                        addr_info["ip_address_url"] = td.find("a")["href"]
                    elif (not self.is_ipv6) and (idx % 11 == 1):
                        addr_info["size"] = text
                    elif ((not self.is_ipv6) and (idx % 11 == 2)) or (self.is_ipv6 and (idx % 9 == 1)):
                        addr_info["network_name"] = text
                    elif ((not self.is_ipv6) and (idx % 11 == 3)) or (self.is_ipv6 and (idx % 9 == 2)):
                        addr_info["assign_date"] = convert_datetime(text=text)
                    elif ((not self.is_ipv6) and (idx % 11 == 4)) or (self.is_ipv6 and (idx % 9 == 3)):
                        addr_info["return_date"] = convert_datetime(text=text)
                    elif ((not self.is_ipv6) and (idx % 11 == 5)) or (self.is_ipv6 and (idx % 9 == 4)):
                        addr_info["org"] = text
                    elif ((not self.is_ipv6) and (idx % 11 == 6)) or (self.is_ipv6 and (idx % 9 == 5)):
                        addr_info["admin_org"] = text
                    elif ((not self.is_ipv6) and (idx % 11 == 7)) or (self.is_ipv6 and (idx % 9 == 6)):
                        addr_info["recept_no"] = text
                    elif ((not self.is_ipv6) and (idx % 11 == 8)) or (self.is_ipv6 and (idx % 9 == 7)):
                        addr_info["deli_no"] = text
                    elif ((not self.is_ipv6) and (idx % 11 == 9)) or (self.is_ipv6 and (idx % 9 == 8)):
                        addr_info["kind1"] = text
                    elif (not self.is_ipv6) and (idx % 11 == 10):
                        addr_info["kind2"] = text
                        if not addr_list_exists:
                            no_update_data = False
                            break
                        if max_len == idx + 1:
                            ipaddr = addr_info["ip_address"]
                        is_exist_addr_lists = False
                        for addr_list in addr_lists:
                            if (
                                addr_list.asn == self.base.asn
                                and addr_list.ip_address == addr_info["ip_address"]
                                and addr_list.ip_version == self.get_ip_version()
                                and addr_list.recep_number == addr_info["recept_no"]
                            ):
                                is_exist_addr_lists = True
                                # 存在する場合は確認OKなので、last_checkedを更新する
                                updated_info_lists.append(addr_list)
                                break
                        if not is_exist_addr_lists:
                            no_update_data = False
                            break
        last_checked_at = timezone.now()
        for updated_info_list in updated_info_lists:
            with transaction.atomic():
                updated_info_list.last_checked_at = last_checked_at
                updated_info_list.save()

        # JPNICハンドルの更新処理
        if no_update_data:
            print("update only jpnic handle.")
            self.apply_list()
            return
        addr_info = self.get_detail_address(url=addr_info["ip_address_url"], info=addr_info)
        # print("info", addr_info)

        jpnic_handles = []
        # 管理者連絡窓口
        # データベースに含まれている場合はSKIP(最新情報は申請履歴より更新)
        if not JPNICHandle.objects.filter(
            ip_version=self.get_ip_version(), jpnic_handle=addr_info["admin_handle"]
        ).exists():
            try:
                jpnic_handles.append(self.get_jpnic_handle(jpnic_handle=addr_info["admin_handle"]))
            except JPNICReqError as exc:
                print(exc)

        # 技術連絡担当者
        for tech_jpnic in addr_info["tech_handle"]:
            if tech_jpnic == addr_info["admin_handle"]:
                continue
            # データベースに含まれている場合はSKIP
            if JPNICHandle.objects.filter(ip_version=self.get_ip_version(), jpnic_handle=tech_jpnic).exists():
                continue
            try:
                jpnic_handles.append(self.get_jpnic_handle(jpnic_handle=tech_jpnic))
            except JPNICReqError as exc:
                print(exc)
        with transaction.atomic():
            self.insert_jpnic_handle(jpnic_handles)
            addr_list_id = self.insert_addr_list(addr_info)

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

    def insert_jpnic_handle(self, jpnic_handles, recep_number=""):
        for jpnic_handle in jpnic_handles:
            new_handle_model = JPNICHandle(
                asn=self.base.asn,
                ip_version=self.get_ip_version(),
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
            )
            new_handle_model.save()

    def insert_addr_list(self, addr_info):
        insert_addrlist = AddrList(
            asn=self.base.asn,
            ip_version=self.get_ip_version(),
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
            asn_id_id=self.base.id,
        )
        insert_resource_list.save()

    def insert_resource_address_list(self, info):
        insert_resource_address_list = ResourceAddressList(
            ip_address=info.get("ip_address"),
            assign_date=info.get("assign_date"),
            assigned_addr_count=info.get("assigned_addr_count"),
            asn_id_id=self.base.id,
        )
        insert_resource_address_list.save()

    def get_ip_version(self):
        if self.is_ipv6:
            return 6
        else:
            return 4

    def apply_list(self):
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
            aplyDateS=self.first_checked_at.strftime("%Y/%m/%d"),
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
        handle_lists = JPNICHandle.objects.filter(asn=self.base.asn, ip_version=self.get_ip_version())
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

        with transaction.atomic():
            # TODO: JPNICハンドルとlast_enabled_at=Nullを使って対象のテーブルを探し当てて、last_enabled_atを更新する
            tmp_handle = JPNICHandle.objects.get(
                jpnic_handle=handle_info["jpnic_handle"],
                asn=self.base.asn,
                ip_version=self.get_ip_version(),
            )
            tmp_handle.last_enabled_at = timezone.now()
            tmp_handle.save()
            self.insert_jpnic_handle(jpnic_handles=[].append(handle_info), recep_number=info["recept_no"])
