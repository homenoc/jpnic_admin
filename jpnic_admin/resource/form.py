import datetime

from django import forms
from django.db import connection
from django.db.models import Q

from jpnic_admin.resource.models import ResourceList, ResourceAddressList
from .sql import sqlDateSelect, sqlAddrListDateFilter, sqlDateSelectCount
from jpnic_admin.models import JPNIC as JPNICModel
from jpnic_admin.log.models import Task


class SearchForm(forms.Form):
    jpnic_id = forms.ModelChoiceField(queryset=JPNICModel.objects)

    network_name = forms.CharField(
        label="ネットワーク名(一部含む)",
        required=False,
    )

    address = forms.CharField(
        label="住所/住所(English)(一部含む)",
        required=False,
    )

    select_date = forms.DateField(
        label="取得日",
        input_formats=["%Y-%m-%d"],
        initial=datetime.date.today,
        widget=forms.DateTimeInput(format="%Y-%m-%d"),
        required=False,
    )

    def get_queryset(self, page=1):
        if not self.is_valid():
            return None

        cleaned_data = self.cleaned_data

        jpnic_id = cleaned_data.get("jpnic_id")
        network_name = cleaned_data.get("network_name")
        address = cleaned_data.get("address")
        select_date = cleaned_data.get("select_date")

        conditions = {}
        q = Q(**conditions)

        if jpnic_id is None:
            return None

        # AS番号フィルタ
        q &= Q(jpnic_id=jpnic_id)

        # ネットワーク名フィルタ
        if network_name != "":
            q &= Q(network_name__contains=network_name)

        # 住所/住所(English)一部含むフィルタ
        if address != "":
            q &= Q(address__contains=address) | Q(address_en__contains=address)

        sql = sqlDateSelect
        # 日付フィルタ
        # フィルタなし時現在の日付にする
        if select_date:
            # created_at < select_date && select_date < last_checked_
            start_time = datetime.datetime.combine(select_date, datetime.time())
            end_time = datetime.datetime.combine(select_date, datetime.time(23, 59, 59))
            input_array = [
                start_time,
                end_time,
                jpnic_id.id,
                "%%%s%%" % network_name,
                "%%%s%%" % address,
                "%%%s%%" % address,
            ]
            with connection.cursor() as cursor:
                cursor.execute(sqlDateSelectCount, input_array)
                count = len(cursor.fetchall())

            # 1つのpageあたりに入るリスト
            list_count = 50

            all_pages = count // list_count
            if count % list_count != 0:
                all_pages += 1
            # range_pages
            all_range_pages = []
            for i in range(all_pages):
                all_range_pages.append(i + 1)
            # range_pages
            next_page = None
            prev_page = None
            if page < all_pages:
                next_page = page + 1
            if page != 1:
                prev_page = page - 1

            # データ出力
            with connection.cursor() as cursor:
                input_array.append(list_count)
                input_array.append((page - 1) * list_count)
                cursor.execute(sql, input_array)
                sql_result = cursor.fetchall()
            data = []
            for result in sql_result:
                data.append(
                    {
                        "id": result[0],
                        "asn": result[1],
                        "created_at": result[2],
                        "last_checked_at": result[3],
                        "kind": result[4],
                        "division": result[5],
                        "ip_address": result[6],
                        "network_name": result[7],
                        "abuse": result[8],
                        "org": result[9],
                        "postcode": result[10],
                        "address": result[11],
                        "address_en": result[12],
                        "admin_handle": result[13],
                        "admin_name": result[14],
                        "admin_email": result[15],
                        "tech_handle": result[16],
                        "tech_name": result[17],
                        "tech_email": result[18],
                    }
                )

            return {
                "all_range_pages": all_range_pages,
                "all_pages": all_pages,
                "next_page": next_page,
                "prev_page": prev_page,
                "count": count,
                "info": data,
            }
        else:
            # TYPEフィルタ
            q &= Q(type1="アドレス情報")
            events = []
            for task in Task.objects.filter(q):
                events.append(
                    {
                        "title": "取得済み",
                        "start": task.created_at.strftime("%Y-%m-%d"),
                        "url": "?jpnic_id=" + str(jpnic_id.id) + "&select_date=" + task.created_at.strftime("%Y-%m-%d"),
                    }
                )

            return {"events": events}


class SearchResourceForm(forms.Form):
    jpnic_id = forms.ModelChoiceField(queryset=JPNICModel.objects)
    select_date = forms.DateField(
        label="取得日",
        input_formats=["%Y-%m-%d"],
        initial=datetime.date.today,
        widget=forms.DateTimeInput(format="%Y-%m-%d"),
        required=False,
    )

    def get_queryset(self):
        if not self.is_valid():
            return None

        cleaned_data = self.cleaned_data

        jpnic_id = cleaned_data.get("jpnic_id")
        select_date = cleaned_data.get("select_date")

        if jpnic_id is None:
            return None

        # 条件
        conditions = {}
        q = Q(**conditions)

        # AS番号フィルタ
        q &= Q(jpnic_id=jpnic_id)
        if select_date:
            # 日付フィルタ
            # created_at < select_date && select_date < last_checked_
            start_time = datetime.datetime.combine(select_date, datetime.time())
            end_time = datetime.datetime.combine(select_date, datetime.time(23, 59, 59))
            q &= ~Q(last_checked_at__lt=start_time)
            q &= ~Q(created_at__gt=end_time)
            rs_list = ResourceList.objects.filter(q).order_by("-last_checked_at").first()
            rs_addr_list = ResourceAddressList.objects.raw(
                sqlAddrListDateFilter, params={"id": jpnic_id.id, "start_time": start_time, "end_time": end_time}
            )

            return {"rs_list": rs_list, "rs_addr_list": rs_addr_list}
        else:
            # TYPEフィルタ
            q &= Q(type1="資源情報")
            events = []
            for task in Task.objects.filter(q):
                events.append(
                    {
                        "title": "取得済み",
                        "start": task.created_at.strftime("%Y-%m-%d"),
                        "url": "?jpnic_id=" + str(jpnic_id.id) + "&select_date=" + task.created_at.strftime("%Y-%m-%d"),
                    }
                )

            return {"events": events}


class SearchResourcesForm(forms.Form):
    jpnic_ids = forms.ModelMultipleChoiceField(queryset=JPNICModel.objects)
    select_date = forms.DateField(
        label="取得日",
        input_formats=["%Y-%m-%d"],
        initial=datetime.date.today,
        widget=forms.DateTimeInput(format="%Y-%m-%d"),
        required=False,
    )

    def get_queryset(self):
        if not self.is_valid():
            return None

        cleaned_data = self.cleaned_data

        jpnic_ids = cleaned_data.get("jpnic_ids")
        select_date = cleaned_data.get("select_date")

        if jpnic_ids is None:
            return None

        # 条件
        conditions = {}

        info = []

        # AS番号フィルタ
        for jpnic_id in jpnic_ids:
            q = Q(**conditions)
            q &= Q(jpnic_id=jpnic_id.id)
            if select_date:
                # 日付フィルタ
                # created_at < select_date && select_date < last_checked_
                start_time = datetime.datetime.combine(select_date, datetime.time())
                end_time = datetime.datetime.combine(select_date, datetime.time(23, 59, 59))
                q &= ~Q(last_checked_at__lt=start_time)
                q &= ~Q(created_at__gt=end_time)
                rs_list = ResourceList.objects.filter(q).order_by("-last_checked_at").first()
                rs_addr_lists = ResourceAddressList.objects.raw(
                    sqlAddrListDateFilter,
                    params={"id": jpnic_id.id, "start_time": start_time, "end_time": end_time},
                )

            else:
                rs_list = ResourceList.objects.filter(q).order_by("-last_checked_at").first()
                rs_addr_lists = ResourceAddressList.objects.filter(q).order_by("-last_checked_at")

            info.append(
                {"name": jpnic_id.name, "asn": jpnic_id.asn, "rs_list": rs_list, "rs_addr_lists": rs_addr_lists}
            )

        return info
