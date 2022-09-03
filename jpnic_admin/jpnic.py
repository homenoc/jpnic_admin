import base64
import os
import re
import ssl
import subprocess
import tempfile
from urllib import parse

import requests.packages
import requests
from bs4 import BeautifulSoup
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives._serialization import Encoding, PrivateFormat
from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
from django.conf import settings
from requests.adapters import HTTPAdapter
from ssl import PROTOCOL_TLS as default_ssl_protocol

from jpnic_admin.models import JPNIC as JPNICModel


class JPNICReqError(Exception):
    pass


class SSLAdapter(HTTPAdapter):
    def __init__(self, *args, **kwargs):
        cert_path = kwargs.pop('cert_path', None)
        pass_byte = kwargs.pop('pass_byte', None)
        self.ssl_context = ssl.SSLContext(default_ssl_protocol)
        if settings.CA_PATH is not None:
            self.ssl_context.load_verify_locations(settings.CA_PATH)
        self.ssl_context.load_cert_chain(cert_path, password=pass_byte)
        os.remove(cert_path)
        super(SSLAdapter, self).__init__(*args, **kwargs)

    def init_poolmanager(self, *args, **kwargs):
        if self.ssl_context:
            kwargs['ssl_context'] = self.ssl_context
        return super(SSLAdapter, self).init_poolmanager(*args, **kwargs)


def get_request_add_change(html_bs=None, change_req={}):
    data_req = {}
    for element in html_bs.find_all('input'):
        if (element.get('name', None) is not None) and (element['name'] != 'action'):
            if element['type'] == 'radio':
                continue
            if element['name'] in change_req:
                data_req[element['name']] = change_req[element['name']]
                continue
            data_req[element['name']] = element['value']
    for element in html_bs.find_all('textarea'):
        if (element.get('name', None) is not None) and (element['name'] != 'action'):
            if element['name'] in change_req:
                data_req[element['name']] = change_req[element['name']]
                continue
            data_req[element['name']] = element.text

    return data_req


def request_to_sjis(request={}):
    req_data = ''
    for key, value in request.items():
        if value is None:
            value = ''
        req_data += parse.quote_plus(key, encoding='shift-jis') + '=' + \
                    parse.quote_plus(str(value), encoding='shift-jis') + '&'
    req_data = req_data[:-1]

    return req_data


def request_error(html_bs=None, html=''):
    all_error = html_bs.findAll('font', attrs={'color': 'red'})
    if all_error:
        error = ''
        for one_error in all_error:
            error += one_error.text + "\n"
        raise JPNICReqError(error, html)


def application_complete(html_bs=None):
    if not '申請完了' in html_bs.find('title').text:
        raise Exception('Error: request error')
    data = {
        '受付番号': '',
        '電子メールアドレス': '',
    }
    tmp_lists = html_bs.select('table > tr > td > table')[0].findAll('td')
    for idx in range(len(tmp_lists)):
        if '受付番号：' in tmp_lists[idx]:
            data['受付番号'] = tmp_lists[idx + 1].text
        if '電子メールアドレス：' in tmp_lists[idx]:
            data['電子メールアドレス'] = tmp_lists[idx + 1].text

    return data


def verify_expire_ca():
    ca_expiry = subprocess.run(["openssl", "x509", "-noout", "-dates", "-in", settings.CA_PATH],
                               capture_output=True, text=True).stdout
    not_before = ''
    not_after = ''
    for line in ca_expiry.splitlines():
        if 'notBefore' in line:
            not_before = line.replace('notBefore=', "")
        if 'notAfter' in line:
            not_after = line.replace('notAfter=', "")
    return {'before': not_before, 'after': not_after}


def verify_expire_p12_file(p12_base64='', p12_pass=''):
    p12_base64 += "=" * ((4 - len(p12_base64) % 4) % 4)
    p12 = base64.b64decode(p12_base64)
    p12_pass_bytes = bytes(p12_pass, 'utf-8')
    pk, cert, option_cert = load_key_and_certificates(
        p12,
        p12_pass_bytes
    )
    return {'before': cert.not_valid_before, 'after': cert.not_valid_after}


class JPNIC():
    def __init__(self, asn=None, ipv6=False):
        self.menu_url = None
        self.base_url = settings.JPNIC_BASE_URL
        self.is_ipv6 = ipv6
        if asn is None:
            raise Exception("AS number is undefined.")
        as_base_object = JPNICModel.objects.filter(asn=asn, is_ipv6=ipv6)
        if not as_base_object.exists():
            raise Exception("[database] no data")
        p12_base64 = as_base_object.first().p12_base64
        p12_base64 += "=" * ((4 - len(p12_base64) % 4) % 4)
        p12 = base64.b64decode(p12_base64)
        p12_pass_bytes = bytes(as_base_object.first().p12_pass, 'utf-8')
        pk, cert, option_cert = load_key_and_certificates(
            p12,
            p12_pass_bytes
        )

        tfw = tempfile.NamedTemporaryFile(delete=False)
        pk_buf = pk.private_bytes(
            Encoding.PEM,
            PrivateFormat.TraditionalOpenSSL,
            serialization.BestAvailableEncryption(password=p12_pass_bytes)
        )
        tfw.write(pk_buf)
        cert_buf = cert.public_bytes(Encoding.PEM)
        tfw.write(cert_buf)
        self.tmp_cert_path = tfw.name
        tfw.flush()
        tfw.close()
        # header
        user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) ' \
                     'Chrome/91.0.4472.114 Safari/537.36 '
        content_type = 'application/x-www-form-urlencoded'
        self.header = {
            'User-Agent': user_agent,
            'Content-Type': content_type,
            'Host': 'iphostmaster.nic.ad.jp',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
        }

        self.session = requests.Session()
        ssl_adapter = SSLAdapter(
            cert_path=self.tmp_cert_path,
            pass_byte=p12_pass_bytes
        )
        self.session.mount(self.base_url, ssl_adapter)
        self.base_url += "/jpnic"
        self.url = self.base_url + "/dispmemberlogin.do"

    def __del__(self):
        if os.path.isfile(self.tmp_cert_path):
            os.remove(self.tmp_cert_path)
            print("delete file: ", self.tmp_cert_path)
        else:
            print("[skip] delete file: ", self.tmp_cert_path)

    def init_get(self):
        # login page
        res = self.session.get(self.url, headers=self.header)
        if not res:
            raise Exception('[login sequence #1] Cannot get data.')
        target_meta_url = BeautifulSoup(res.content, 'html.parser').find('meta', attrs={'http-equiv': 'Refresh'})
        if target_meta_url['content'] is None:
            raise Exception('[login sequence #1] parse error.')
        # login(auth)
        url = self.base_url + "/" + target_meta_url['content'].split('/')[1]
        res = self.session.get(url, headers=self.header)
        if not res.ok:
            raise Exception('[login sequence #2] Cannot get data.')
        target_meta_url = BeautifulSoup(res.content, 'html.parser').find('meta', attrs={'http-equiv': 'Refresh'})
        if target_meta_url['content'] is None:
            raise Exception('[login sequence #2] parse error.')
        self.menu_url = self.base_url + "/" + target_meta_url['content'].split('url=')[1]

    def get_contents_url(self, *args):
        res = self.session.get(self.menu_url, headers=self.header)
        res.encoding = 'Shift_JIS'
        soup = BeautifulSoup(res.text, 'html.parser')
        # print(soup.find_all('a'))
        menu_path = soup.find('a', string=args[0])['href']
        self.url = self.base_url + "/" + menu_path

    def generate_req_contact(
            self,
            kind='group',
            jpnic_handle='',
            name='',
            name_en='',
            email='',
            org='',
            org_en='',
            zipcode='',
            address='',
            address_en='',
            division='',
            division_en='',
            title='',
            title_en='',
            tel='',
            fax='',
            notify_email='',
    ):

        data = {
            'kind': kind,
            'jpnic_hdl': jpnic_handle,
            'name_jp': name,
            'name': name_en,
            'email': email,
            'org_nm_jp': org,
            'org_nm': org_en,
            'zipcode': zipcode,
            'addr_jp': address,
            'addr': address_en,
            'division_jp': division,
            'division': division_en,
            'title_jp': title,
            'title': title_en,
            'phone': tel,
            'fax': fax,
            'ntfy_mail': notify_email,
        }

        return data

    def generate_req_assignment(
            self,
            ip_address='',
            network_name='',
            infra_usr_kind=1,
            org='',
            org_en='',
            zipcode='',
            address='',
            address_en='',
            admin_handle='',
            tech_handle='',
            abuse='',
            notify_email='',
            plan_data='',
            deli_no='',
            return_date='',
            apply_from_email='',
            nameservers=[],
            contacts=[],
            **kwargs
    ):
        data = {
            'ipaddr': ip_address,
            'netwrk_nm': network_name,
            'infra_usr_kind': infra_usr_kind,
            'org_nm_jp': org,
            'org_nm': org_en,
            'zipcode': zipcode,
            'addr_jp': address,
            'addr': address_en,
            'adm_hdl': admin_handle,
            'tech_hdl': tech_handle,
            'abuse': abuse,
            'ntfy_mail': notify_email,
            'plan_data': plan_data,
            'deli_no': deli_no,
            'rtn_date': return_date,
            'aply_from_addr': apply_from_email,
            'aply_from_addr_confirm': apply_from_email,
        }
        index = 0
        for nameserver in nameservers:
            data['nmsrv[' + str(index) + '].nmsrv'] = nameserver
            index += 1

        index = 0
        for contact in contacts:
            con = self.generate_req_contact(**contact)
            for key, value in con.items():
                if self.is_ipv6:
                    data['emps[' + str(index) + '].' + key] = value
                else:
                    data['emp[' + str(index) + '].' + key] = value
            index += 1

        return data

    def add_assignment(self, **kwargs):
        self.init_get()
        form_name = ""
        if self.is_ipv6:
            self.get_contents_url('IPv6割り当て報告申請　〜ユーザ用〜')
            form_name = "K01640Form"
        else:
            self.get_contents_url('IPv4割り当て報告申請　〜ユーザ用〜')
            form_name = "AssiAplyv4Regist"
        print("Menu URL:", self.url)
        contacts = kwargs.get('contacts', [])
        res = self.session.get(self.url, headers=self.header)
        res.encoding = 'Shift_JIS'
        soup = BeautifulSoup(res.text, 'html.parser')
        token = ""
        aplyid = ""
        if not self.is_ipv6:
            token = soup.find('input', attrs={'name': 'org.apache.struts.taglib.html.TOKEN'})['value']
            aplyid = soup.find('input', attrs={'name': 'aplyid'})['value']
        destdisp = soup.find('input', attrs={'name': 'destdisp'})
        post_url = soup.find('form', attrs={'name': form_name})['action'].split('/')[-1]
        contact_count = 0
        for num in range(len(contacts)):
            contact_count += 1
            contact_lists = []
            for num in range(contact_count):
                contact_lists.append({})
            req = self.generate_req_assignment(**{'contacts': contact_lists})
            if not self.is_ipv6:
                req['org.apache.struts.taglib.html.TOKEN'] = token
                req['aplyid'] = aplyid
            req['destdisp'] = destdisp['value']
            req['action'] = '[担当者情報]追加'
            req_data = request_to_sjis(req)
            res = self.session.post(self.base_url + '/' + post_url, data=req_data, headers=self.header)
            res.encoding = 'Shift_JIS'
            soup = BeautifulSoup(res.text, 'html.parser')
            if not self.is_ipv6:
                token = soup.find('input', attrs={'name': 'org.apache.struts.taglib.html.TOKEN'})['value']
                aplyid = soup.find('input', attrs={'name': 'aplyid'})['value']
            destdisp = soup.find('input', attrs={'name': 'destdisp'})
        req = self.generate_req_assignment(**kwargs)
        if not self.is_ipv6:
            req['org.apache.struts.taglib.html.TOKEN'] = token
            req['aplyid'] = aplyid
        req['destdisp'] = destdisp['value']
        req['action'] = '申請'
        req_data = request_to_sjis(req)
        res = self.session.post(self.base_url + '/' + post_url, data=req_data, headers=self.header)
        res.encoding = 'Shift_JIS'
        soup = BeautifulSoup(res.text, 'html.parser')
        request_error(soup, res.text)
        req = {}
        if not self.is_ipv6:
            req['destdisp'] = soup.find('input', attrs={'name': 'destdisp'})['value'],
            req['org.apache.struts.taglib.html.TOKEN'] = \
                soup.find('input', attrs={'name': 'org.apache.struts.taglib.html.TOKEN'})['value']
            req['aplyid'] = soup.find('input', attrs={'name': 'aplyid'})['value'],
            req['prevDispId'] = soup.find('input', attrs={'name': 'prevDispId'})['value'],
            req['inputconf'] = '確認'
        else:
            req['action'] = '確認'

        req_data = request_to_sjis(req)
        if self.is_ipv6:
            post_url = soup.find('form', attrs={'name': 'K01640Form'})['action'].split('/')[-1]
        else:
            post_url = soup.find('form', attrs={'name': 'ConfApplyForInsider'})['action'].split('/')[-1]
        print(self.base_url + '/' + post_url)
        res = self.session.post(self.base_url + '/' + post_url, data=req_data, headers=self.header)
        res.encoding = 'Shift_JIS'
        soup = BeautifulSoup(res.text, 'html.parser')
        data = application_complete(html_bs=soup)
        return {'data': data, 'html': res.text}

    def get_ip_address(self, ip_address="", kind=3):
        self.init_get()
        form_name = ""
        if self.is_ipv6:
            self.get_contents_url('登録情報検索(IPv6)')
        else:
            self.get_contents_url('登録情報検索(IPv4)')
        print("Menu URL:", self.url)
        res = self.session.get(self.url, headers=self.header)
        res.encoding = 'Shift_JIS'
        soup = BeautifulSoup(res.text, 'html.parser')
        req = {
            'destdisp': soup.find('input', attrs={'name': 'destdisp'})['value'],
            'ipaddr': ip_address,
            'sizeS': '', 'sizeE': '', 'netwrkName': '', 'regDateS': '', 'regDateE': '', 'rtnDateS': '',
            'rtnDateE': '', 'organizationName': '',
            'resceAdmSnm': soup.find('input', attrs={'name': 'resceAdmSnm'})['value'],
            'recepNo': '', 'deliNo': '',
        }
        if kind == 1:
            req['regKindAllo'] = 'on'
        elif kind == 2:
            req['regKindEvent'] = 'on'
        elif kind == 3:
            req['regKindUser'] = 'on'
        elif kind == 4:
            req['regKindSubA'] = 'on'
        req['action'] = '　検索　'
        req_data = request_to_sjis(req)
        post_url = soup.find('form')['action'].split('/')[-1]
        res = self.session.post(self.base_url + '/' + post_url, data=req_data, headers=self.header)
        res.encoding = 'Shift_JIS'
        soup = BeautifulSoup(res.text, 'html.parser')
        infos = []
        info = {}
        for idx, td in enumerate(soup.findAll('td', attrs={'class': 'dataRow_mnt04'})):
            text = td.text.strip()
            if self.is_ipv6:
                if ((idx + 1) // 9 == 0) or (idx == 8):
                    continue
                if (idx + 1) % 9 == 0:
                    info['kind'] = text
                    infos.append(info)
                    info = {}
                elif (idx + 1) % 9 == 1:
                    info['ip_address'] = text
                    info['ip_address_url'] = td.find('a')['href']
                elif (idx + 1) % 9 == 2:
                    info['network_name'] = text
                elif (idx + 1) % 9 == 3:
                    info['assign_date'] = text
                elif (idx + 1) % 9 == 4:
                    info['return_date'] = text
                elif (idx + 1) % 9 == 5:
                    info['org'] = text
                elif (idx + 1) % 9 == 6:
                    info['admin_org'] = text
                elif (idx + 1) % 9 == 7:
                    info['recept_no'] = text
                elif (idx + 1) % 9 == 8:
                    info['deli_no'] = text
            else:
                if ((idx + 1) // 11 == 0) or (idx == 10):
                    continue
                if (idx + 1) % 11 == 0:
                    info['kind2'] = text
                    infos.append(info)
                    info = {}
                elif (idx + 1) % 11 == 1:
                    info['ip_address'] = text
                    info['ip_address_url'] = td.find('a')['href']
                elif (idx + 1) % 11 == 2:
                    info['size'] = text
                elif (idx + 1) % 11 == 3:
                    info['network_name'] = text
                elif (idx + 1) % 11 == 4:
                    info['assign_date'] = text
                elif (idx + 1) % 11 == 5:
                    info['return_date'] = text
                elif (idx + 1) % 11 == 6:
                    info['org'] = text
                elif (idx + 1) % 11 == 7:
                    info['admin_org'] = text
                elif (idx + 1) % 11 == 8:
                    info['recept_no'] = text
                elif (idx + 1) % 11 == 9:
                    info['deli_no'] = text
                elif (idx + 1) % 11 == 10:
                    info['kind1'] = text

        if len(infos) == 0:
            raise JPNICReqError('該当するデータが見つかりませんでした。', res.text)
        return {'infos': infos, 'html': res.text}

    def v4_get_change_assignment(self, ip_address='', kind=0):
        self.init_get()
        ## IPv4ネットワーク情報変更申請
        self.get_contents_url('IPv4ネットワーク情報変更申請')
        print("Menu URL:", self.url)
        res = self.session.get(self.url, headers=self.header)
        res.encoding = 'Shift_JIS'
        soup = BeautifulSoup(res.text, 'html.parser')
        req = {
            'org.apache.struts.taglib.html.TOKEN':
                soup.find('input', attrs={'name': 'org.apache.struts.taglib.html.TOKEN'})['value'],
            'aplyid': soup.find('input', attrs={'name': 'aplyid'})['value'],
            'destdisp': soup.find('input', attrs={'name': 'destdisp'})['value'],
            'ipaddr': ip_address,
            'infra_usr_kind': kind,
            'action': '　確認　'
        }
        req_data = request_to_sjis(req)
        request_error(soup, res.text)
        post_url = soup.find('form', attrs={'name': 'NetInfoChangePreRegist'})['action'].split('/')[-1]
        res = self.session.post(self.base_url + '/' + post_url, data=req_data, headers=self.header)
        res.encoding = 'Shift_JIS'
        soup = BeautifulSoup(res.text, 'html.parser')
        request_error(soup, res.text)
        data = {
            'netwrk_nm': soup.find('input', attrs={'name': 'netwrk_nm'})['value'],
            'org_nm_jp': soup.find('textarea', attrs={'name': 'org_nm_jp'}).text,
            'org_nm': soup.find('textarea', attrs={'name': 'org_nm'}).text,
            'zipcode': soup.find('input', attrs={'name': 'zipcode'})['value'],
            'addr_jp': soup.find('textarea', attrs={'name': 'addr_jp'}).text,
            'addr': soup.find('textarea', attrs={'name': 'addr'}).text,
            'adm_hdl': soup.find('input', attrs={'name': 'adm_hdl'})['value'],
            'tech_hdl': soup.find('textarea', attrs={'name': 'tech_hdl'}).text,
            'abuse': soup.find('input', attrs={'name': 'abuse'})['value'],
            'ntfy_mail': soup.find('textarea', attrs={'name': 'ntfy_mail'}).text,
            'chg_reason': soup.find('textarea', attrs={'name': 'chg_reason'}).text,
            'rtn_date': soup.find('input', attrs={'name': 'rtn_date'})['value'],
            'aply_from_addr': soup.find('input', attrs={'name': 'aply_from_addr'})['value'],
            'aply_from_addr_confirm': soup.find('input', attrs={'name': 'aply_from_addr_confirm'})['value'],
        }
        ## ネームサーバ
        self.get_contents_url('IPv4逆引きネームサーバ追加・削除')
        print("Menu URL:", self.url)
        res = self.session.get(self.url, headers=self.header)
        res.encoding = 'Shift_JIS'
        soup = BeautifulSoup(res.text, 'html.parser')
        kind_name = 'assign'
        if kind == 2:
            kind_name = 'suba'
        elif kind == 3:
            kind_name = 'history'
        req = {
            'org.apache.struts.taglib.html.TOKEN':
                soup.find('input', attrs={'name': 'org.apache.struts.taglib.html.TOKEN'})['value'],
            'aplyid': soup.find('input', attrs={'name': 'aplyid'})['value'],
            'destdisp': soup.find('input', attrs={'name': 'destdisp'})['value'],
            'ipaddr': ip_address,
            'reg_kind': kind_name
        }
        req_data = request_to_sjis(req)
        post_url = soup.find('form', attrs={'name': 'DnsIPInput'})['action'].split('/')[-1]
        res = self.session.post(self.base_url + '/' + post_url, data=req_data, headers=self.header)
        res.encoding = 'Shift_JIS'
        soup = BeautifulSoup(res.text, 'html.parser')
        dns = soup.findAll('table', attrs={'cellpadding': '1'})
        return {'data': data, 'dns': dns}

    def v6_get_change_assignment(self, ip_address=''):
        self.init_get()
        ## IPv6ネットワーク情報変更申請
        self.get_contents_url('IPv6ネットワーク情報変更申請')
        print("Menu URL:", self.url)
        res = self.session.get(self.url, headers=self.header)
        res.encoding = 'Shift_JIS'
        soup = BeautifulSoup(res.text, 'html.parser')
        sel_check = None
        req = {
            'aplyid': soup.find('input', attrs={'name': 'aplyid'})['value'],
            'destdisp': soup.find('input', attrs={'name': 'destdisp'})['value'],
            'action': '確認'
        }
        for s in soup.findAll('tr', attrs={'bgcolor': '#ffffff'}):
            addr = s.find('td', string=ip_address)
            if addr:
                sel_check = s.find('input')['value']
                break
        if not sel_check:
            raise JPNICReqError('該当のIPアドレスが見つかりませんでした。', res.text)
        req['selCheck'] = sel_check
        req_data = request_to_sjis(req)
        post_url = \
            soup.find('form', attrs={'name': 'K01680Form', 'action': re.compile(r'Dispatch')})['action'].split('/')[-1]
        res = self.session.post(self.base_url + '/' + post_url, data=req_data, headers=self.header)
        res.encoding = 'Shift_JIS'
        soup = BeautifulSoup(res.text, 'html.parser')
        dns = soup.findAll('table', attrs={'cellpadding': '1'})
        data = get_request_add_change(html_bs=soup, change_req={})
        return {'data': data, 'dns': dns}

    def v4_change_assignment(self, ip_address='', kind=0, change_req={}):
        self.init_get()
        ## IPv4ネットワーク情報変更申請
        self.get_contents_url('IPv4ネットワーク情報変更申請')
        print("Menu URL:", self.url)
        res = self.session.get(self.url, headers=self.header)
        res.encoding = 'Shift_JIS'
        soup = BeautifulSoup(res.text, 'html.parser')
        req = {
            'org.apache.struts.taglib.html.TOKEN':
                soup.find('input', attrs={'name': 'org.apache.struts.taglib.html.TOKEN'})['value'],
            'aplyid': soup.find('input', attrs={'name': 'aplyid'})['value'],
            'destdisp': soup.find('input', attrs={'name': 'destdisp'})['value'],
            'ipaddr': ip_address,
            'infra_usr_kind': kind
        }
        req_data = request_to_sjis(req)
        post_url = soup.find('form', attrs={'name': 'NetInfoChangePreRegist'})['action'].split('/')[-1]
        res = self.session.post(self.base_url + '/' + post_url, data=req_data, headers=self.header)
        res.encoding = 'Shift_JIS'
        soup = BeautifulSoup(res.text, 'html.parser')
        change_req['aply_from_addr_confirm'] = change_req['aply_from_addr']
        change_req['org.apache.struts.taglib.html.TOKEN'] = \
            soup.find('input', attrs={'name': 'org.apache.struts.taglib.html.TOKEN'})['value']
        change_req['aplyid'] = soup.find('input', attrs={'name': 'aplyid'})['value']
        change_req['destdisp'] = soup.find('input', attrs={'name': 'destdisp'})['value']
        change_req['action'] = "申請"
        req_data = request_to_sjis(req)
        request_error(soup, res.text)
        post_url = soup.find('form', attrs={'name': 'NetInfoChangeRegist'})['action'].split('/')[-1]
        res = self.session.post(self.base_url + '/' + post_url, data=req_data, headers=self.header)
        res.encoding = 'Shift_JIS'
        soup = BeautifulSoup(res.text, 'html.parser')
        request_error(soup, res.text)
        req = {
            'org.apache.struts.taglib.html.TOKEN':
                soup.find('input', attrs={'name': 'org.apache.struts.taglib.html.TOKEN'})['value'],
            'prevDispId': soup.find('input', attrs={'name': 'prevDispId'})['value'],
            'aplyid': soup.find('input', attrs={'name': 'aplyid'})['value'],
            'destdisp': soup.find('input', attrs={'name': 'destdisp'})['value'],
            'inputconf': "確認"
        }
        req_data = request_to_sjis(req)
        post_url = soup.find('form', attrs={'name': 'ConfApplyForInsider'})['action'].split('/')[-1]
        res = self.session.post(self.base_url + '/' + post_url, data=req_data, headers=self.header)
        res.encoding = 'Shift_JIS'
        soup = BeautifulSoup(res.text, 'html.parser')
        data = application_complete(html_bs=soup)
        return {'data': data, 'html': res.text}

    def v6_change_assignment(self, ip_address='', change_req={}):
        self.init_get()
        ## IPv6ネットワーク情報変更申請
        self.get_contents_url('IPv6ネットワーク情報変更申請')
        print("Menu URL:", self.url)
        res = self.session.get(self.url, headers=self.header)
        res.encoding = 'Shift_JIS'
        soup = BeautifulSoup(res.text, 'html.parser')
        sel_check = None
        req = {
            'aplyid': soup.find('input', attrs={'name': 'aplyid'})['value'],
            'destdisp': soup.find('input', attrs={'name': 'destdisp'})['value'],
            'action': '確認'
        }
        for s in soup.findAll('tr', attrs={'bgcolor': '#ffffff'}):
            addr = s.find('td', string=ip_address)
            if addr:
                sel_check = s.find('input')['value']
                break
        if not sel_check:
            raise JPNICReqError('該当のIPアドレスが見つかりませんでした。', res.text)
        req['selCheck'] = sel_check
        print(req)
        req_data = request_to_sjis(req)
        post_url = \
            soup.find('form', attrs={'name': 'K01680Form', 'action': re.compile(r'Dispatch')})['action'].split('/')[-1]
        res = self.session.post(self.base_url + '/' + post_url, data=req_data, headers=self.header)
        res.encoding = 'Shift_JIS'
        soup = BeautifulSoup(res.text, 'html.parser')
        ## Request Data
        req = get_request_add_change(html_bs=soup, change_req=change_req)
        req['applymailaddrkakunin'] = req['applymailaddr']
        req['action'] = '申請'
        req_data = request_to_sjis(req)
        post_url = soup.find('form', attrs={'name': 'K01690Form'})['action'].split('/')[-1]
        res = self.session.post(self.base_url + '/' + post_url, data=req_data, headers=self.header)
        res.encoding = 'Shift_JIS'
        soup = BeautifulSoup(res.text, 'html.parser')
        request_error(soup, res.text)
        req = {'action': '確認'}
        req_data = request_to_sjis(req)
        post_url = soup.find('form', attrs={'name': 'K01690Form'})['action'].split('/')[-1]
        res = self.session.post(self.base_url + '/' + post_url, data=req_data, headers=self.header)
        res.encoding = 'Shift_JIS'
        soup = BeautifulSoup(res.text, 'html.parser')
        data = application_complete(html_bs=soup)
        return {'data': data, 'html': res.text}

    def v4_return_assignment(self, ip_address='', return_date=None, notify_address=''):
        self.init_get()
        data = self.get_ip_address(ip_address=ip_address, kind=0)
        infos = data.get('infos')
        network_name = None
        for info in infos:
            if '割当' in info['kind2']:
                network_name = info['network_name']
                break
        if not network_name:
            raise JPNICReqError('対象のIPアドレスが見つかりませんでした。', data.get('html'))

        ## 割り当て済みIPv4返却申請
        self.get_contents_url('割り当て済みIPv4返却申請')
        res = self.session.get(self.url, headers=self.header)
        res.encoding = 'Shift_JIS'
        soup = BeautifulSoup(res.text, 'html.parser')
        req = {
            'org.apache.struts.taglib.html.TOKEN':
                soup.find('input', attrs={'name': 'org.apache.struts.taglib.html.TOKEN'})['value'],
            'aplyid': soup.find('input', attrs={'name': 'aplyid'})['value'],
            'destdisp': soup.find('input', attrs={'name': 'destdisp'})['value'],
            'ipaddr': ip_address,
            'netwrk_nm': network_name,
            'rtn_date': return_date,
            'aply_from_addr': notify_address,
            'aply_from_addr_confirm': notify_address,
            'action': "申請"
        }
        req_data = request_to_sjis(req)
        post_url = \
            soup.find('form', attrs={'name': 'AssiReturnv4Regist', 'action': re.compile(r'registconf')})[
                'action'].split('/')[-1]
        ## 申請ボタン＝＞確認
        res = self.session.post(self.base_url + '/' + post_url, data=req_data, headers=self.header)
        res.encoding = 'Shift_JIS'
        soup = BeautifulSoup(res.text, 'html.parser')
        request_error(soup, res.text)
        req = {
            'org.apache.struts.taglib.html.TOKEN':
                soup.find('input', attrs={'name': 'org.apache.struts.taglib.html.TOKEN'})['value'],
            'aplyid': soup.find('input', attrs={'name': 'aplyid'})['value'],
            'prevDispId': soup.find('input', attrs={'name': 'prevDispId'})['value'],
            'destdisp': soup.find('input', attrs={'name': 'destdisp'})['value'],
            'inputconf': "確認"
        }
        req_data = request_to_sjis(req)
        post_url = soup.find('form', attrs={'name': 'ConfApplyForInsider'})['action'].split('/')[-1]
        res = self.session.post(self.base_url + '/' + post_url, data=req_data, headers=self.header)
        res.encoding = 'Shift_JIS'
        soup = BeautifulSoup(res.text, 'html.parser')
        data = application_complete(html_bs=soup)
        return {'data': data, 'html': res.text}

    def v6_return_assignment(self, ip_address='', return_date=None, notify_address=''):
        self.init_get()
        ## 割り当て済みIPv6返却申請
        self.get_contents_url('割り当て済みIPv6返却申請')
        print("Menu URL:", self.url)
        res = self.session.get(self.url, headers=self.header)
        res.encoding = 'Shift_JIS'
        soup = BeautifulSoup(res.text, 'html.parser')
        network_id = None
        req = {
            'aplyid': soup.find('input', attrs={'name': 'aplyid'})['value'],
            'destdisp': soup.find('input', attrs={'name': 'destdisp'})['value'],
            'action': '確認'
        }
        for s in soup.findAll('tr', attrs={'bgcolor': '#ffffff'}):
            addr = s.find('td', string=ip_address)
            if addr:
                network_id = s.find('input')['value']
                break
        if not network_id:
            raise JPNICReqError('該当のIPアドレスが見つかりませんでした。', res.text)
        req['netwrkId'] = network_id
        req_data = request_to_sjis(req)
        post_url = \
            soup.find('form', attrs={'name': 'K01660Form', 'action': re.compile(r'Dispatch')})['action'].split('/')[-1]
        res = self.session.post(self.base_url + '/' + post_url, data=req_data, headers=self.header)
        res.encoding = 'Shift_JIS'
        soup = BeautifulSoup(res.text, 'html.parser')
        token = soup.find('input', attrs={'name': 'org.apache.struts.taglib.html.TOKEN'})
        req = {
            'aplyid': soup.find('input', attrs={'name': 'aplyid'})['value'],
            'destdisp': soup.find('input', attrs={'name': 'destdisp'})['value'],
            'return_date': return_date,
            'aply_from_addr': notify_address,
            'aply_from_addr_confirm': notify_address,
            'action': '申請'
        }
        if token:
            req['org.apache.struts.taglib.html.TOKEN'] = token['value'],
        req_data = request_to_sjis(req)
        post_url = \
            soup.find('form', attrs={'name': 'K01661Form', 'action': re.compile(r'Dispatch')})['action'].split('/')[-1]
        res = self.session.post(self.base_url + '/' + post_url, data=req_data, headers=self.header)
        res.encoding = 'Shift_JIS'
        soup = BeautifulSoup(res.text, 'html.parser')
        request_error(html_bs=soup, html=res.text)
        req = {
            'aplyid': soup.find('input', attrs={'name': 'aplyid'})['value'],
            'inputconf': '確認'
        }
        req_data = request_to_sjis(req)
        post_url = soup.find('form', attrs={'name': 'K01662Form'})['action'].split('/')[-1]
        res = self.session.post(self.base_url + '/' + post_url, data=req_data, headers=self.header)
        res.encoding = 'Shift_JIS'
        soup = BeautifulSoup(res.text, 'html.parser')
        data = application_complete(html_bs=soup)
        return {'data': data, 'html': res.text}

    def add_person(self, change_req={}):
        self.init_get()
        ## 担当グループ(担当者)情報登録・変更
        self.get_contents_url('担当グループ（担当者）情報登録・変更')
        res = self.session.get(self.url, headers=self.header)
        res.encoding = 'Shift_JIS'
        soup = BeautifulSoup(res.text, 'html.parser')
        req = get_request_add_change(html_bs=soup, change_req=change_req)
        req['aply_from_addr_confirm'] = req['aply_from_addr']
        req['action'] = '申請'
        req_data = request_to_sjis(req)
        post_url = \
            soup.find('form', attrs={'name': 'PocRegist', 'action': re.compile(r'pocregist.do')})['action'].split('/')[
                -1]
        res = self.session.post(self.base_url + '/' + post_url, data=req_data, headers=self.header)
        res.encoding = 'Shift_JIS'
        soup = BeautifulSoup(res.text, 'html.parser')
        request_error(html_bs=soup, html=res.text)
        req = get_request_add_change(html_bs=soup, change_req=change_req)
        req['inputconf'] = '確認'
        req_data = request_to_sjis(req)
        post_url = soup.find('form', attrs={'name': 'ConfApplyForInsider'})['action'].split('/')[-1]
        res = self.session.post(self.base_url + '/' + post_url, data=req_data, headers=self.header)
        res.encoding = 'Shift_JIS'
        soup = BeautifulSoup(res.text, 'html.parser')
        data = application_complete(html_bs=soup)
        return {'data': data, 'html': res.text}

    def get_jpnic_handle(self, jpnic_handle=''):
        self.init_get()
        res = self.session.get(self.base_url + '/' + 'entryinfo_handle.do?jpnic_hdl=' + jpnic_handle,
                               headers=self.header)
        res.encoding = 'Shift_JIS'
        soup = BeautifulSoup(res.text, 'html.parser')
        jpnic_handle_info = soup.select('table > tr > td > table > tr > td > table')[0].findAll('td')
        data = {
            'jpnic_hdl': jpnic_handle
        }
        update_date = None
        for idx in range(len(jpnic_handle_info)):
            if idx != 0:
                prev_text = jpnic_handle_info[idx - 1].text.strip()
                now_text = jpnic_handle_info[idx].text.strip()
                if prev_text == 'グループハンドル':
                    data['kind'] = 'group'
                if prev_text == 'JPNICハンドル':
                    data['kind'] = 'person'
                if prev_text == 'グループ名' or prev_text == '氏名':
                    data['name_jp'] = now_text
                if prev_text == 'Group Name' or prev_text == 'Last, First':
                    data['name'] = now_text
                if prev_text == '電子メール' or prev_text == '電子メイル':
                    data['email'] = now_text
                if prev_text == '組織名':
                    data['org_nm_jp'] = now_text
                if prev_text == 'Organization':
                    data['org_nm'] = now_text
                if prev_text == '部署':
                    data['division_jp'] = now_text
                if prev_text == 'Division':
                    data['division'] = now_text
                if prev_text == '肩書':
                    data['title_jp'] = now_text
                if prev_text == 'Title':
                    data['title'] = now_text
                if prev_text == '電話番号':
                    data['phone'] = now_text
                if prev_text == 'Fax番号' or prev_text == 'FAX番号':
                    data['fax'] = now_text
                if prev_text == '最終更新':
                    update_date = now_text
        if data['org_nm_jp'] == '' and data['name_jp'] == '':
            raise JPNICReqError('該当のJPNIC Handleが見つかりませんでした。', res.text)
        return {'data': data, 'update_date': update_date}

    def contact_register(self, **kwargs):
        self.init_get()
        self.get_contents_url('担当グループ（担当者）情報登録・変更')
        print("Menu URL:", self.url)
        res = self.session.get(self.url, headers=self.header)
        res.encoding = 'Shift_JIS'
        soup = BeautifulSoup(res.text, 'html.parser')
        token = soup.find('input', attrs={'name': 'org.apache.struts.taglib.html.TOKEN'})
        destdisp = soup.find('input', attrs={'name': 'destdisp'})
        aplyid = soup.find('input', attrs={'name': 'aplyid'})
        req = self.generate_req_contact(**kwargs)
        req['org.apache.struts.taglib.html.TOKEN'] = token['value']
        req['destdisp'] = destdisp['value']
        req['aplyid'] = aplyid['value']
        req['aply_from_addr'] = kwargs.pop('apply_from_email', None)
        req['aply_from_addr_confirm'] = kwargs.pop('apply_from_email', None)
        print(req)
