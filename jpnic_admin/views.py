import json
from html import escape

from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string

from jpnic_admin.form import (
    SearchForm,
    AddAssignment,
    GetIPAddressForm,
)
from jpnic_admin.jpnic import (
    JPNIC,
    JPNICReqError,
)
from jpnic_admin.models import JPNIC as JPNICModel


def index(request):
    jpnic_model_all = JPNICModel.objects.all()
    form = SearchForm(request.GET)

    per_page = int(request.GET.get("per_page", 1))
    data = form.get_queryset(page=per_page, jpnic_model=jpnic_model_all)

    context = {
        "jpnic_model": jpnic_model_all,
        "data": data,
        "per_page": per_page,
        "search_form": form,
    }
    return render(request, "jpnic_admin/index.html", context)


def get_jpnic_info(request):
    # a_list = Article.objects.filter(pub_date__year=year)
    # result = JPNIC.objects.filter()
    context = {"year": "year"}
    return render(request, "jpnic_admin/index.html", context)


def search(request):
    if request.method == "POST":
        if "search" in request.POST:
            form = GetIPAddressForm(request.POST)
            context = {}
            if form.is_valid():
                # kind
                # 1: 割振
                # 2: インフラ割当
                # 3: ユーザ割当
                # 4: (v4)SUBA/(v6)再割振
                try:
                    j = JPNIC(asn=form.cleaned_data.get("asn"), ipv6=form.cleaned_data.get("ipv6"))
                    res_data = j.get_ip_address(
                        ip_address=form.cleaned_data.get("ip_address"),
                        kind=form.cleaned_data.get("kind"),
                    )
                    context = {
                        "name": "JPNIC 割り当て追加　結果",
                        "data": json.dumps(
                            res_data["infos"],
                            ensure_ascii=False,
                            indent=4,
                            sort_keys=True,
                            separators=(",", ":"),
                        ),
                        "result_html": res_data["html"],
                    }
                    return render(request, "result.html", context)
                except JPNICReqError as exc:
                    result_html = ""
                    if len(exc.args) > 1:
                        result_html = exc.args[1]
                    context["name"] = "データ取得　エラー"
                    context["error"] = exc.args[0]
                    context["result_html"] = result_html
                except TypeError as err:
                    context["error"] = str(err)
                return render(request, "result.html", context)
            context = {
                "name": "データ取得　エラー",
                "form": form,
            }
            return render(request, "get_ip_address.html", context)
    form = GetIPAddressForm()
    context = {
        "name": "アドレス情報検索",
        "form": form,
    }
    return render(request, "get_ip_address.html", context)


def add_assignment1(request):
    if request.method == "POST":
        print("POST")
        if "test" in request.POST:
            print("test")
            context = {
                "name": "JPNIC 割り当て追加　結果",
                "error": "err",
            }
            html = render_to_string("result.html", context)
            return HttpResponse(html)
        form = AddAssignment(request.POST, request.FILES)
        if form.is_valid():
            print(form.cleaned_data)
            print(request.FILES)
            if form.cleaned_data["file"]:
                print(form.cleaned_data["file"])
                input_data = json.loads(form.cleaned_data["file"].read().decode("utf-8"))
            else:
                print(request.POST)
                print(json.loads(request.POST["data"]))
                input_data = json.loads(request.POST["data"])

            context = {
                "req_data": json.dumps(input_data, ensure_ascii=False, indent=4, sort_keys=True, separators=(",", ":"))
            }

            if not "as" in input_data:
                context["error"] = "AS番号が指定されていません"
                return JsonResponse(context)

            try:
                j = JPNIC(asn=input_data["as"], ipv6=input_data.get("ipv6", False))
                res_data = j.add_assignment(**input_data)
                print(res_data)
                context["data"] = json.dumps(
                    res_data["data"],
                    ensure_ascii=False,
                    indent=4,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                # context['data'] = res_data['data']
                context["result_html"] = escape(res_data["html"])
            except JPNICReqError as exc:
                result_html = ""
                if len(exc.args) > 1:
                    result_html = exc.args[1]
                context["error"] = exc.args[0]
                context["result_html"] = escape(result_html)
            except TypeError as err:
                context["error"] = str(err)

            return JsonResponse(context)

    else:
        form = AddAssignment()

    context = {
        "form": form,
        "as": JPNICModel.objects.all(),
    }
    return render(request, "add_assignment1.html", context)
