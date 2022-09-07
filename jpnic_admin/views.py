import base64
import json
from html import escape

from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string

from jpnic_admin.form import SearchForm, AddAssignment, AddGroupContact, GetIPAddressForm, \
    ChangeV4Assignment, GetChangeAssignment, ChangeV6Assignment, ReturnAssignment, UploadFile, Base1, GetJPNICHandle, \
    ASForm, ChangeCertForm
from jpnic_admin.jpnic import JPNIC, JPNICReqError, verify_expire_p12_file, verify_expire_ca, convert_date_format
from jpnic_admin.models import JPNIC as JPNICModel


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
        "jpnic_model": JPNICModel.objects.all(),
        "jpnic_page": events_page,
        "count_no_data": count_no_data,
        "search_form": form,
    }
    return render(request, 'jpnic_admin/index.html', context)


def get_jpnic_info(request):
    # a_list = Article.objects.filter(pub_date__year=year)
    # result = JPNIC.objects.filter()
    context = {'year': "year"}
    return render(request, 'jpnic_admin/index.html', context)


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
                context['error'] = str(err)
            return render(request, 'result.html', context)
    else:
        form = GetChangeAssignment()
        context = {
            "name": "アドレスの割り当て変更",
            "form": form,
        }

        return render(request, 'get_ip_address.html', context)


def return_assignment(request):
    if request.method == 'POST':
        form = ReturnAssignment(request.POST)
        context = {
            'name': 'IPアドレス割り当て返却　結果',
        }
        if form.is_valid():
            print(form.cleaned_data)
            print(form.cleaned_data.get('ipv6'))
            if form.cleaned_data.get('ipv6'):
                print('ipv6')
                try:
                    j = JPNIC(
                        asn=form.cleaned_data.get('asn'),
                        ipv6=form.cleaned_data.get('ipv6')
                    )
                    res_data = j.v6_return_assignment(
                        ip_address=form.cleaned_data.get('ip_address'),
                        return_date=convert_date_format(form.cleaned_data.get('return_date')),
                        notify_address=form.cleaned_data.get('notify_address')
                    )
                    context['result_html'] = res_data['html']
                    context['data'] = res_data['data']
                    context['req_data'] = form.cleaned_data
                except JPNICReqError as exc:
                    result_html = ''
                    if len(exc.args) > 1:
                        result_html = exc.args[1]
                    context['error'] = exc.args[0]
                    context['result_html'] = result_html
                except TypeError as err:
                    context['error'] = str(err)
                return render(request, 'result.html', context)
            else:
                try:
                    j = JPNIC(
                        asn=form.cleaned_data.get('asn'),
                        ipv6=form.cleaned_data.get('ipv6')
                    )
                    res_data = j.v4_return_assignment(
                        ip_address=form.cleaned_data.get('ip_address'),
                        return_date=convert_date_format(form.cleaned_data.get('return_date')),
                        notify_address=form.cleaned_data.get('notify_address')
                    )
                    context['result_html'] = res_data['html']
                    context['data'] = res_data['data']
                    context['req_data'] = form.cleaned_data
                except JPNICReqError as exc:
                    result_html = ''
                    if len(exc.args) > 1:
                        result_html = exc.args[1]
                    context['error'] = exc.args[0]
                    context['result_html'] = result_html
                except TypeError as err:
                    context['error'] = str(err)
                return render(request, 'result.html', context)
        else:
            context['form'] = form
            return render(request, 'return_assignment.html', context=context)
    else:
        form = ReturnAssignment()
        context = {
            'form': form
        }

        return render(request, 'return_assignment.html', context=context)


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
    if request.method == 'POST':
        if 'manual' in request.POST:
            base_form = Base1(request.POST)
            manual_form = AddGroupContact(request.POST)
            context = {
                'name': 'JPNIC 担当者追加　結果',
            }
            if base_form.is_valid() and manual_form.is_valid():
                try:
                    j = JPNIC(
                        asn=base_form.cleaned_data.get('asn'),
                        ipv6=base_form.cleaned_data.get('ipv6')
                    )
                    res_data = j.add_person(
                        change_req=manual_form.cleaned_data
                    )
                    context['result_html'] = res_data['html']
                    context['data'] = res_data['data']
                    context['req_data'] = manual_form.cleaned_data
                except JPNICReqError as exc:
                    result_html = ''
                    if len(exc.args) > 1:
                        result_html = exc.args[1]
                    context['error'] = exc.args[0]
                    context['result_html'] = result_html
                except TypeError as err:
                    context['error'] = str(err)
                return render(request, 'result.html', context)
        elif 'upload' in request.POST:
            base_form = Base1(request.POST)
            upload_form = UploadFile(request.POST, request.FILES)
            context = {
                'name': 'JPNIC 担当者追加　結果',
            }
            print(upload_form.is_valid())
            if not base_form.is_valid() and not upload_form.is_valid():
                context['base_form'] = base_form
                context['upload_form'] = upload_form
                return render(request, 'add_person.html', context=context)
            if not upload_form.cleaned_data['file']:
                return render(request, 'add_person.html', context=context)
            json_data = upload_form.cleaned_data['file'].read().decode('utf-8')
            input_data = json.loads(json_data)
            input_data['jpnic_hdl'] = '1'
            try:
                j = JPNIC(
                    asn=base_form.cleaned_data.get('asn'),
                    ipv6=base_form.cleaned_data.get('ipv6')
                )
                res_data = j.add_person(
                    change_req=input_data
                )
                context['result_html'] = res_data['html']
                context['data'] = res_data['data']
                context['req_data'] = input_data
            except JPNICReqError as exc:
                result_html = ''
                if len(exc.args) > 1:
                    result_html = exc.args[1]
                context['error'] = exc.args[0]
                context['result_html'] = result_html
            except TypeError as err:
                context['error'] = str(err)
            return render(request, 'result.html', context)
        elif 'manual_download' in request.POST:
            manual_form = AddGroupContact(request.POST)
            if manual_form.is_valid():
                data = json.dumps(manual_form.cleaned_data, ensure_ascii=False, indent=4, sort_keys=True,
                                  separators=(',', ':'))
                response = HttpResponse(data, content_type='application/json')
                response['Content-Disposition'] = 'attachment; filename="result.json"'
                return response
    else:
        base_form = Base1(request.GET)
        manual_form = AddGroupContact(request.GET)
        upload_form = UploadFile(request.GET)
        context = {
            "base_form": base_form,
            "manual_form": manual_form,
            "upload_form": upload_form
        }
        return render(request, 'add_person.html', context)


def change_person(request):
    if request.method == 'POST':
        if 'search' in request.POST:
            search_form = GetJPNICHandle(request.POST)
            context = {
                'name': 'JPNIC 担当者変更　結果',
            }
            if search_form.is_valid():
                try:
                    j = JPNIC(
                        asn=search_form.cleaned_data.get('asn'),
                        ipv6=search_form.cleaned_data.get('ipv6')
                    )
                    res_data = j.get_jpnic_handle(
                        jpnic_handle=search_form.cleaned_data.get('jpnic_handle')
                    )
                    context['form'] = AddGroupContact(res_data['data'])
                    context['update_date'] = res_data['update_date']
                    context['base_form'] = Base1(data={
                        'ipv6': search_form.cleaned_data.get('ipv6'),
                        'asn': search_form.cleaned_data.get('asn')
                    })

                    return render(request, 'change_person.html', context)
                except JPNICReqError as exc:
                    result_html = ''
                    if len(exc.args) > 1:
                        result_html = exc.args[1]
                    context['error'] = exc.args[0]
                    context['result_html'] = result_html
                except TypeError as err:
                    context['error'] = str(err)
                return render(request, 'result.html', context)
        elif 'apply' in request.POST:
            base_form = Base1(request.POST)
            form = AddGroupContact(request.POST)
            context = {
                'name': 'JPNIC 担当者追加　結果',
            }
            if base_form.is_valid() and form.is_valid():
                print(base_form.cleaned_data)
                try:
                    j = JPNIC(
                        asn=base_form.cleaned_data.get('asn'),
                        ipv6=base_form.cleaned_data.get('ipv6')
                    )
                    res_data = j.add_person(
                        change_req=form.cleaned_data
                    )
                    context['result_html'] = res_data['html']
                    context['data'] = res_data['data']
                    context['req_data'] = form.cleaned_data
                except JPNICReqError as exc:
                    result_html = ''
                    if len(exc.args) > 1:
                        result_html = exc.args[1]
                    context['error'] = exc.args[0]
                    context['result_html'] = result_html
                except TypeError as err:
                    context['error'] = str(err)
                return render(request, 'result.html', context)
        elif 'download' in request.POST:
            form = AddGroupContact(request.POST)
            if form.is_valid():
                data = json.dumps(form.cleaned_data, ensure_ascii=False, indent=4, sort_keys=True,
                                  separators=(',', ':'))
                response = HttpResponse(data, content_type='application/json')
                response['Content-Disposition'] = 'attachment; filename="result.json"'
                return response

    else:
        form = GetJPNICHandle()
        context = {
            "form": form,
        }
        return render(request, 'get_jpnic_handle.html', context)


def ca(request):
    f = open(settings.CA_PATH, 'r', encoding='UTF-8')
    ca_data = f.read()
    return HttpResponse(content=ca_data, content_type='text/plain')


def add_as(request):
    if request.method == 'POST':
        form = ASForm(request.POST, request.FILES)
        context = {
            "form": form,
        }
        if form.is_valid():
            if not form.cleaned_data['p12']:
                return render(request, 'add_as.html', context=context)
            p12_binary = form.cleaned_data['p12'].read()
            p12_base64 = base64.b64encode(p12_binary)
            jpnic_model = JPNICModel.objects.create(
                name=form.cleaned_data.get('name'),
                is_active=True,
                is_ipv6=form.cleaned_data.get('ipv6'),
                ada=form.cleaned_data.get('ada'),
                collection_interval=form.cleaned_data.get('collection_interval'),
                asn=form.cleaned_data.get('asn'),
                p12_base64=p12_base64.decode("ascii"),
                p12_pass=form.cleaned_data.get('p12_pass'),
            )
            jpnic_model.save()
            context['name'] = 'AS・証明書の追加'
            context['data'] = '登録しました'
            return render(request, 'result.html', context)
    else:
        form = ASForm()
        context = {
            "form": form,
        }
        return render(request, 'add_as.html', context)


def list_as(request):
    if request.method == 'POST':
        if 'apply' in request.POST:
            form = ChangeCertForm(request.POST, request.FILES)
            jpnic_id = int(request.POST.get('id'))
            context = {
                "form": form,
            }
            if form.is_valid():
                if not form.cleaned_data['p12']:
                    return render(request, 'add_as.html', context=context)
                p12_binary = form.cleaned_data['p12'].read()
                p12_base64 = base64.b64encode(p12_binary)
                jpnic_model = JPNICModel.objects.get(id=jpnic_id)
                jpnic_model.p12_base64 = p12_base64.decode("ascii")
                jpnic_model.p12_pass = form.cleaned_data.get('p12_pass')
                jpnic_model.save()
                context['name'] = 'AS・証明書の追加'
                context['data'] = '登録しました'
                return render(request, 'result.html', context)
        elif 'renew_cert' in request.POST:
            jpnic_id = int(request.POST.get('id'))
            form = ChangeCertForm()
            context = {
                "id": jpnic_id,
                "form": form,
            }
            return render(request, 'change_as.html', context)

    else:
        jpnic_model = JPNICModel.objects.all()
        print(jpnic_model)
        data = []
        ca_expiry_date = verify_expire_ca()
        for jpn in jpnic_model:
            print(jpn)
            p12_expiry_date = verify_expire_p12_file(p12_base64=jpn.p12_base64, p12_pass=jpn.p12_pass)
            data.append({
                'data': jpn,
                'expiry_date': p12_expiry_date
            })
        context = {
            "jpnic": data,
            "ca_path": settings.CA_PATH,
            "ca_expiry_date": ca_expiry_date
        }
        return render(request, 'list_as.html', context)
