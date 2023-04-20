import json
from html import escape

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string

from jpnic_admin.form import (
    AddAssignment,
    AddGroupContact,
    ChangeV4Assignment,
    GetChangeAssignment,
    ChangeV6Assignment,
    ReturnAssignment,
    UploadFile,
    Base1,
    GetJPNICHandle,
)
from jpnic_admin.jpnic import (
    JPNIC,
    JPNICReqError,
    convert_date_format,
)
from jpnic_admin.models import JPNIC as JPNICModel


@login_required
def add(request):
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
                "req_data": json.dumps(
                    input_data, ensure_ascii=False, indent=4, sort_keys=True, separators=(",", ":")
                )
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
    return render(request, "assignment/add.html", context)


@login_required
def change(request):
    if request.method == "POST":
        if "search" in request.POST:
            form = GetChangeAssignment(request.POST)
            context = {}
            if form.is_valid():
                # kind
                # 1: 割振
                # 2: インフラ割当
                # 3: ユーザ割当
                # 4: (v4)SUBA/(v6)再割振
                print(form.cleaned_data)
                print(form.cleaned_data.get("ipv6"))
                if form.cleaned_data.get("ipv6"):
                    print("ipv6")
                    try:
                        j = JPNIC(
                            asn=form.cleaned_data.get("asn"), ipv6=form.cleaned_data.get("ipv6")
                        )
                        res_data = j.v6_get_change_assignment(
                            ip_address=form.cleaned_data.get("ip_address"),
                        )

                        form_change_assignment = ChangeV6Assignment(res_data["data"])
                        context = {
                            "base_form": form,
                            "form": form_change_assignment,
                            "dns": res_data["dns"],
                        }
                        return render(request, "assignment/change_v6.html", context)
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
                try:
                    j = JPNIC(asn=form.cleaned_data.get("asn"), ipv6=form.cleaned_data.get("ipv6"))
                    res_data = j.v4_get_change_assignment(
                        ip_address=form.cleaned_data.get("ip_address"),
                        kind=int(form.cleaned_data.get("kind")),
                    )

                    form_change_assignment = ChangeV4Assignment(res_data["data"])
                    context = {
                        "base_form": form,
                        "form": form_change_assignment,
                        "dns": res_data["dns"],
                    }
                    return render(request, "assignment/change_v4.html", context)
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
                "name": "アドレスの割り当て変更",
                "form": form,
            }
            return render(request, "get_ip_address.html", context)

        elif "v4_change" in request.POST:
            base_form = GetChangeAssignment(request.POST)
            form_change_assignment = ChangeV4Assignment(request.POST)
            if base_form.is_valid() and form_change_assignment.is_valid():
                print(base_form.cleaned_data)
                print(form_change_assignment.cleaned_data)
            context = {
                "name": "アドレスの割り当て変更",
            }
            try:
                j = JPNIC(
                    asn=base_form.cleaned_data.get("asn"), ipv6=base_form.cleaned_data.get("ipv6")
                )
                res_data = j.v4_change_assignment(
                    ip_address=base_form.cleaned_data.get("ip_address"),
                    kind=int(base_form.cleaned_data.get("kind")),
                    change_req=form_change_assignment.cleaned_data,
                )

                context["result_html"] = res_data["html"]
                context["data"] = res_data["data"]
                context["req_data"] = form_change_assignment.cleaned_data

                return render(request, "result.html", context)
            except JPNICReqError as exc:
                result_html = ""
                if len(exc.args) > 1:
                    result_html = exc.args[1]
                context["error"] = exc.args[0]
                context["result_html"] = result_html
            except TypeError as err:
                context["error"] = str(err)
            return render(request, "result.html", context)

        elif "v6_change" in request.POST:
            base_form = GetChangeAssignment(request.POST)
            form_change_assignment = ChangeV6Assignment(request.POST)
            if base_form.is_valid() and form_change_assignment.is_valid():
                print(base_form.cleaned_data)
                print(form_change_assignment.cleaned_data)
            context = {
                "name": "アドレスの割り当て変更",
            }
            try:
                j = JPNIC(
                    asn=base_form.cleaned_data.get("asn"), ipv6=base_form.cleaned_data.get("ipv6")
                )
                res_data = j.v6_change_assignment(
                    ip_address=base_form.cleaned_data.get("ip_address"),
                    change_req=form_change_assignment.cleaned_data,
                )

                context["result_html"] = res_data["html"]
                context["data"] = res_data["data"]
                context["req_data"] = form_change_assignment.cleaned_data

                return render(request, "result.html", context)
            except JPNICReqError as exc:
                result_html = ""
                if len(exc.args) > 1:
                    result_html = exc.args[1]
                context["error"] = exc.args[0]
                context["result_html"] = result_html
            except TypeError as err:
                context["error"] = str(err)
            return render(request, "result.html", context)

    form = GetChangeAssignment()
    context = {
        "name": "アドレスの割り当て変更",
        "form": form,
    }

    return render(request, "get_ip_address.html", context)


@login_required
def delete(request):
    if request.method == "POST":
        form = ReturnAssignment(request.POST)
        context = {
            "name": "IPアドレス割り当て返却　結果",
        }
        if form.is_valid():
            print(form.cleaned_data)
            print(form.cleaned_data.get("ipv6"))
            if form.cleaned_data.get("ipv6"):
                print("ipv6")
                try:
                    j = JPNIC(asn=form.cleaned_data.get("asn"), ipv6=form.cleaned_data.get("ipv6"))
                    res_data = j.v6_return_assignment(
                        ip_address=form.cleaned_data.get("ip_address"),
                        return_date=convert_date_format(form.cleaned_data.get("return_date")),
                        notify_address=form.cleaned_data.get("notify_address"),
                    )
                    context["result_html"] = res_data["html"]
                    context["data"] = res_data["data"]
                    context["req_data"] = form.cleaned_data
                except JPNICReqError as exc:
                    result_html = ""
                    if len(exc.args) > 1:
                        result_html = exc.args[1]
                    context["error"] = exc.args[0]
                    context["result_html"] = result_html
                except TypeError as err:
                    context["error"] = str(err)
                return render(request, "result.html", context)
            try:
                j = JPNIC(asn=form.cleaned_data.get("asn"), ipv6=form.cleaned_data.get("ipv6"))
                res_data = j.v4_return_assignment(
                    ip_address=form.cleaned_data.get("ip_address"),
                    return_date=convert_date_format(form.cleaned_data.get("return_date")),
                    notify_address=form.cleaned_data.get("notify_address"),
                )
                context["result_html"] = res_data["html"]
                context["data"] = res_data["data"]
                context["req_data"] = form.cleaned_data
            except JPNICReqError as exc:
                result_html = ""
                if len(exc.args) > 1:
                    result_html = exc.args[1]
                context["error"] = exc.args[0]
                context["result_html"] = result_html
            except TypeError as err:
                context["error"] = str(err)
            return render(request, "result.html", context)
        context["form"] = form
        return render(request, "assignment/delete.html", context=context)
    form = ReturnAssignment()
    context = {"form": form}
    return render(request, "assignment/delete.html", context=context)


@login_required
def result(request):
    context = request.GET.get("context")
    return render(request, "result.html", context=context)
