import base64
import os
import ssl
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
from jpnic_gui.models import JPNIC as JPNICModel


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


class JPNIC():
    def __init__(self, asn=None):
        self.base_url = settings.JPNIC_BASE_URL
        if asn is None:
            raise Exception("AS number is undefined.")
        as_base_object = JPNICModel.objects.get(asn=asn)
        if as_base_object is None:
            raise Exception("[database] no data")
        p12_base64 = as_base_object.p12_base64
        p12_base64 += "=" * ((4 - len(p12_base64) % 4) % 4)
        p12 = base64.b64decode(p12_base64)
        p12_pass_bytes = bytes(as_base_object.p12_pass, 'utf-8')
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
        self.url = self.base_url + "/" + target_meta_url['content'].split('url=')[1]

    def get_contents_url(self, *args):
        res = self.session.get(self.url, headers=self.header)
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
                data['emp[' + str(index) + '].' + key] = value
            index += 1

        return data

    def ipv4_assignment_user(self, **kwargs):
        self.init_get()
        self.get_contents_url('IPv4割り当て報告申請　〜ユーザ用〜')
        print("Menu URL:", self.url)
        contacts = kwargs.get('contacts', [])
        res = self.session.get(self.url, headers=self.header)
        res.encoding = 'Shift_JIS'
        soup = BeautifulSoup(res.text, 'html.parser')
        token = soup.find('input', attrs={'name': 'org.apache.struts.taglib.html.TOKEN'})
        destdisp = soup.find('input', attrs={'name': 'destdisp'})
        aplyid = soup.find('input', attrs={'name': 'aplyid'})
        post_url = soup.find('form', attrs={'name': 'AssiAplyv4Regist'})['action'].split('/')[-1]
        contact_count = 0
        for num in range(len(contacts)):
            contact_count += 1
            contact_lists = []
            for num in range(contact_count):
                contact_lists.append({})
            req = self.generate_req_assignment(**{'contacts': contact_lists})
            req['org.apache.struts.taglib.html.TOKEN'] = token['value']
            req['destdisp'] = destdisp['value']
            req['aplyid'] = aplyid['value']
            req['action'] = '[担当者情報]追加'
            req_data = ''
            for key, value in req.items():
                req_data += parse.quote_plus(key, encoding='shift-jis') + '=' + \
                            parse.quote_plus(str(value), encoding='shift-jis') + '&'
            req_data = req_data[:-1]
            res = self.session.post(self.base_url + '/' + post_url, data=req_data, headers=self.header)
            res.encoding = 'Shift_JIS'
            soup = BeautifulSoup(res.text, 'html.parser')
            token = soup.find('input', attrs={'name': 'org.apache.struts.taglib.html.TOKEN'})
            destdisp = soup.find('input', attrs={'name': 'destdisp'})
            aplyid = soup.find('input', attrs={'name': 'aplyid'})

        req = self.generate_req_assignment(**kwargs)
        req['org.apache.struts.taglib.html.TOKEN'] = token['value']
        req['destdisp'] = destdisp['value']
        req['aplyid'] = aplyid['value']
        req['action'] = '申請'
        req_data = ''
        for key, value in req.items():
            req_data += parse.quote_plus(key, encoding='shift-jis') + '=' + \
                        parse.quote_plus(str(value), encoding='shift-jis') + '&'
        req_data = req_data[:-1]
        print(req_data)
        res = self.session.post(self.base_url + '/' + post_url, data=req_data, headers=self.header)
        res.encoding = 'Shift_JIS'
        soup = BeautifulSoup(res.text, 'html.parser')
        all_error = soup.findAll('font', attrs={'color': 'red'})
        if all_error:
            error = ''
            for one_error in all_error:
                error += one_error.text + "\n"
            raise JPNICReqError(error, res.text)
        req = {
            'org.apache.struts.taglib.html.TOKEN':
                soup.find('input', attrs={'name': 'org.apache.struts.taglib.html.TOKEN'})['value'],
            'prevDispId': soup.find('input', attrs={'name': 'prevDispId'})['value'],
            'destdisp': soup.find('input', attrs={'name': 'destdisp'})['value'],
            'aplyid': soup.find('input', attrs={'name': 'aplyid'})['value'],
            'inputconf': '確認'
        }
        req_data = ''
        for key, value in req.items():
            req_data += parse.quote_plus(key, encoding='shift-jis') + '=' + \
                        parse.quote_plus(str(value), encoding='shift-jis') + '&'
        req_data = req_data[:-1]
        print(req_data)
        post_url = soup.find('form', attrs={'name': 'ConfApplyForInsider'})['action'].split('/')[-1]
        res = self.session.post(self.base_url + '/' + post_url, data=req_data, headers=self.header)
        res.encoding = 'Shift_JIS'
        soup = BeautifulSoup(res.text, 'html.parser')
        if not '申請完了' in soup.find('title').text:
            raise Exception('Error: request error')
        data = {
            '受付番号': '',
            '電子メールアドレス': '',
        }
        tmp_lists = soup.select('table > tr > td > table')[0].findAll('td')
        for idx in range(len(tmp_lists)):
            if '受付番号：' in tmp_lists[idx]:
                data['受付番号'] = tmp_lists[idx + 1].text
            if '電子メールアドレス：' in tmp_lists[idx]:
                data['電子メールアドレス'] = tmp_lists[idx + 1].text
        return {data: data, 'html': res.text}

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
        req['aplyid'] = aplyid['value']
        req['aply_from_addr'] = kwargs.pop('apply_from_email', None)
        req['aply_from_addr_confirm'] = kwargs.pop('apply_from_email', None)
        print(req)
