import io
import json
from html import escape

from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string

from jpnic_gui.form import SearchForm, AddAssignment, AddGroupContact, GetIPAddressForm, \
    ChangeV4Assignment, GetChangeAssignment, ChangeV6Assignment
from jpnic_gui.jpnic import JPNIC, JPNICReqError
from jpnic_gui.models import JPNIC as JPNICModel


def index(request):
    form = SearchForm(request.GET)
    result = form.get_queryset().order_by()

    count_no_data = result.filter(Q(address='', address_en='')).count()

    paginator = Paginator(result, int(request.GET.get("per_page", "30")))
    page = int(request.GET.get("page", "1"))
    try:
        events_page = paginator.page(page)
    except (EmptyPage, InvalidPage):
        events_page = paginator.page(paginator.num_pages)

    context = {
        "jpnic_page": events_page,
        "count_no_data": count_no_data,
        "search_form": form,
    }
    return render(request, 'jpnic_gui/index.html', context)


def get_jpnic_info(request):
    # a_list = Article.objects.filter(pub_date__year=year)
    # result = JPNIC.objects.filter()
    context = {'year': "year"}
    return render(request, 'jpnic_gui/index.html', context)


def add_assignment(request):
    if request.method == 'POST':
        print("POST")
        if 'test' in request.POST:
            print("test")
            context = {
                "name": "JPNIC 割り当て追加　結果",
                "error": "err",
            }
            html = render_to_string('result.html', context)
            return HttpResponse(html)
        form = AddAssignment(request.POST, request.FILES)
        if form.is_valid():
            print(form.cleaned_data)
            print(request.FILES)
            input_data = {}
            if form.cleaned_data['file']:
                print(form.cleaned_data['file'])
                input_data = json.loads(form.cleaned_data['file'].read().decode('utf-8'))
            else:
                print(request.POST)
                print(json.loads(request.POST['data']))
                input_data = json.loads(request.POST['data'])

            context = {
                "req_data": json.dumps(input_data, ensure_ascii=False, indent=4, sort_keys=True,
                                       separators=(',', ':'))
            }

            if not 'as' in input_data:
                context['error'] = "AS番号が指定されていません"
                return JsonResponse(context)

            try:
                j = JPNIC(
                    asn=input_data['as'],
                    ipv6=input_data.get('ipv6', False)
                )
                res_data = j.add_assignment(**input_data)
                print(res_data)
                context['data'] = json.dumps(res_data['data'], ensure_ascii=False, indent=4, sort_keys=True,
                                             separators=(',', ':'))
                # context['data'] = res_data['data']
                context['result_html'] = escape(res_data['html'])
            except JPNICReqError as exc:
                result_html = ''
                if len(exc.args) > 1:
                    result_html = exc.args[1]
                context['error'] = exc.args[0]
                context['result_html'] = escape(result_html)
            except TypeError as err:
                print(err)
                context['error'] = str(err)

            return JsonResponse(context)

    else:
        form = AddAssignment()

    context = {
        "form": form,
        "as": JPNICModel.objects.all(),
    }
    return render(request, 'add_assignment.html', context)


def search(request):
    if request.method == 'POST':
        if 'search' in request.POST:
            print("search")
            form = GetIPAddressForm(request.POST)
            context = {}
            if form.is_valid():
                # kind
                # 1: 割振
                # 2: インフラ割当
                # 3: ユーザ割当
                # 4: (v4)SUBA/(v6)再割振
                try:
                    j = JPNIC(
                        asn=form.cleaned_data.get('asn'),
                        ipv6=form.cleaned_data.get('ipv6')
                    )
                    res_data = j.get_ip_address(
                        ip_address=form.cleaned_data.get('ip_address'),
                        kind=form.cleaned_data.get('kind')
                    )
                    context = {
                        "name": "JPNIC 割り当て追加　結果",
                        "data": json.dumps(res_data['infos'], ensure_ascii=False, indent=4, sort_keys=True,
                                           separators=(',', ':')),
                        "result_html": res_data['html']
                    }
                    return render(request, 'result.html', context)
                except JPNICReqError as exc:
                    result_html = ''
                    if len(exc.args) > 1:
                        result_html = exc.args[1]
                    context['name'] = "データ取得　エラー"
                    context['error'] = exc.args[0]
                    context['result_html'] = result_html
                except TypeError as err:
                    print(err)
                    context['error'] = str(err)
                return render(request, 'result.html', context)
            else:
                context = {
                    "name": "データ取得　エラー",
                    "form": form,
                }
                return render(request, 'get_ip_address.html', context)
    else:
        form = GetIPAddressForm()
        context = {
            "name": "アドレス情報検索",
            "form": form,
        }
        return render(request, 'get_ip_address.html', context)


def change_assignment(request):
    if request.method == 'POST':
        if 'search' in request.POST:
            print("search")
            form = GetChangeAssignment(request.POST)
            context = {}
            if form.is_valid():
                # kind
                # 1: 割振
                # 2: インフラ割当
                # 3: ユーザ割当
                # 4: (v4)SUBA/(v6)再割振
                print(form.cleaned_data)
                print(form.cleaned_data.get('ipv6'))
                if form.cleaned_data.get('ipv6'):
                    print('ipv6')
                    try:
                        j = JPNIC(
                            asn=form.cleaned_data.get('asn'),
                            ipv6=form.cleaned_data.get('ipv6')
                        )
                        res_data = j.v6_get_change_assignment(
                            ip_address=form.cleaned_data.get('ip_address'),
                        )

                        form_change_assignment = ChangeV6Assignment(res_data['data'])
                        context = {
                            "base_form": form,
                            "form": form_change_assignment,
                            "dns": res_data['dns'],
                        }
                        return render(request, 'change_v6_assignment.html', context)
                    except JPNICReqError as exc:
                        result_html = ''
                        if len(exc.args) > 1:
                            result_html = exc.args[1]
                        context['name'] = "データ取得　エラー"
                        context['error'] = exc.args[0]
                        context['result_html'] = result_html
                    except TypeError as err:
                        print(err)
                        context['error'] = str(err)
                    return render(request, 'result.html', context)
                else:
                    try:
                        j = JPNIC(
                            asn=form.cleaned_data.get('asn'),
                            ipv6=form.cleaned_data.get('ipv6')
                        )
                        res_data = j.v4_get_change_assignment(
                            ip_address=form.cleaned_data.get('ip_address'),
                            kind=int(form.cleaned_data.get('kind'))
                        )

                        form_change_assignment = ChangeV4Assignment(res_data['data'])
                        context = {
                            "base_form": form,
                            "form": form_change_assignment,
                            "dns": res_data['dns'],
                        }
                        return render(request, 'change_v4_assignment.html', context)
                    except JPNICReqError as exc:
                        result_html = ''
                        if len(exc.args) > 1:
                            result_html = exc.args[1]
                        context['name'] = "データ取得　エラー"
                        context['error'] = exc.args[0]
                        context['result_html'] = result_html
                    except TypeError as err:
                        print(err)
                        context['error'] = str(err)
                    return render(request, 'result.html', context)
            else:
                context = {
                    "name": "アドレスの割り当て変更",
                    "form": form,
                }
                return render(request, 'get_ip_address.html', context)
        elif 'v4_change' in request.POST:
            base_form = GetChangeAssignment(request.POST)
            form_change_assignment = ChangeV4Assignment(request.POST)
            if base_form.is_valid() and form_change_assignment.is_valid():
                print(base_form.cleaned_data)
                print(form_change_assignment.cleaned_data)
            context = {
                'name': "アドレスの割り当て変更",
            }
            try:
                j = JPNIC(
                    asn=base_form.cleaned_data.get('asn'),
                    ipv6=base_form.cleaned_data.get('ipv6')
                )
                res_data = j.v4_change_assignment(
                    ip_address=base_form.cleaned_data.get('ip_address'),
                    kind=int(base_form.cleaned_data.get('kind')),
                    change_req=form_change_assignment.cleaned_data
                )

                context['result_html'] = res_data['html']
                context['data'] = res_data['data']
                context['req_data'] = form_change_assignment.cleaned_data

                return render(request, 'result.html', context)
            except JPNICReqError as exc:
                result_html = ''
                if len(exc.args) > 1:
                    result_html = exc.args[1]
                context['error'] = exc.args[0]
                context['result_html'] = result_html
            except TypeError as err:
                print(err)
                context['error'] = str(err)
            return render(request, 'result.html', context)

        elif 'v6_change' in request.POST:
            base_form = GetChangeAssignment(request.POST)
            form_change_assignment = ChangeV6Assignment(request.POST)
            if base_form.is_valid() and form_change_assignment.is_valid():
                print(base_form.cleaned_data)
                print(form_change_assignment.cleaned_data)
            context = {
                'name': "アドレスの割り当て変更",
            }
            try:
                j = JPNIC(
                    asn=base_form.cleaned_data.get('asn'),
                    ipv6=base_form.cleaned_data.get('ipv6')
                )
                res_data = j.v6_change_assignment(
                    ip_address=base_form.cleaned_data.get('ip_address'),
                    change_req=form_change_assignment.cleaned_data
                )

                context['result_html'] = res_data['html']
                context['data'] = res_data['data']
                context['req_data'] = form_change_assignment.cleaned_data

                return render(request, 'result.html', context)
            except JPNICReqError as exc:
                result_html = ''
                if len(exc.args) > 1:
                    result_html = exc.args[1]
                context['error'] = exc.args[0]
                context['result_html'] = result_html
            except TypeError as err:
                print(err)
                context['error'] = str(err)
            return render(request, 'result.html', context)
    else:
        form = GetChangeAssignment()
        context = {
            "name": "アドレスの割り当て変更",
            "form": form,
        }

        return render(request, 'get_ip_address.html', context)


def result(request):
    context = {

    }
    context = request.GET.get('context')
    return render(request, 'result.html', context=context)


def handle_uploaded_file(f):
    print("upload")
    # with open('some/file/name.txt', 'wb+') as destination:
    #     for chunk in f.chunks():
    #         destination.write(chunk)


def add_person(request):
    form = AddGroupContact(request.GET)
    context = {
        "form": form,
    }
    return render(request, 'add_person.html', context)
