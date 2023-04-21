import json
from html import escape

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from .form import (
    SearchForm,
    AddAssignment,
    ChangeV4AssignmentForm,
    ChangeV6AssignmentForm,
    ReturnForm, SearchChangeAssignmentForm
)
from jpnic_admin.jpnic import (
    JPNIC,
    JPNICReqError,
    convert_date_format,
)
from jpnic_admin.models import JPNIC as JPNICModel


@login_required
def add(request):
    form = AddAssignment(request.POST, request.FILES)
    if request.method == "POST":
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

            try:
                jpnicModel = JPNICModel.objects.get(id=int(input_data["jpnic_id"]))
                res_data = JPNIC(base=jpnicModel).add_assignment(**input_data)
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

        context = {"error": "リクエスト内容似不備があります。"}
        return JsonResponse(context)

    context = {"form": form, }
    return render(request, "assignment/add.html", context)


@login_required
def change(request):
    form = SearchChangeAssignmentForm(request.GET, request.POST)
    context = {
        "name": "アドレスの割り当て変更",
        "form": form,
    }
    if not form.is_valid():
        return render(request, "assignment/search.html", context)

    if request.method == "GET":
        try:
            base = form.cleaned_data.get("jpnic_id")
            res_data = JPNIC(base=base).get_change_assignment(
                ip_address=form.cleaned_data.get("ip_address"),
                kind=form.cleaned_data.get("kind")
            )

            if base.is_ipv6:
                form_change_assignment = ChangeV6AssignmentForm(res_data["data"])
            else:
                form_change_assignment = ChangeV4AssignmentForm(res_data["data"])

            context = {
                "base_form": form,
                "form": form_change_assignment,
                "dns": res_data["dns"],
            }
            if base.is_ipv6:
                return render(request, "assignment/change_v6.html", context)
            else:
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

    if "v4_change" in request.POST:
        base = form.cleaned_data.get("jpnic_id")
        form_change_assignment = ChangeV4AssignmentForm(request.POST)
        if not form_change_assignment.is_valid():
            return render(request, "assignment/search.html", context)
        context = {
            "name": "アドレスの割り当て変更",
        }
        try:
            res_data = JPNIC(base=base).v4_change_assignment(
                ip_address=base.cleaned_data.get("ip_address"),
                kind=int(base.cleaned_data.get("kind")),
                change_req=form_change_assignment.cleaned_data,
            )

            context["result_html"] = res_data["html"]
            context["data"] = res_data["data"]
            context["req_data"] = form_change_assignment.cleaned_data
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
        base = form.cleaned_data.get("jpnic_id")
        form_change_assignment = ChangeV6AssignmentForm(request.POST)
        if not form_change_assignment.is_valid():
            return render(request, "assignment/search.html", context)
        context = {
            "name": "アドレスの割り当て変更",
        }
        try:
            res_data = JPNIC(base=base).v6_change_assignment(
                ip_address=base.cleaned_data.get("ip_address"),
                change_req=form_change_assignment.cleaned_data,
            )

            context["result_html"] = res_data["html"]
            context["data"] = res_data["data"]
            context["req_data"] = form_change_assignment.cleaned_data
        except JPNICReqError as exc:
            result_html = ""
            if len(exc.args) > 1:
                result_html = exc.args[1]
            context["error"] = exc.args[0]
            context["result_html"] = result_html
        except TypeError as err:
            context["error"] = str(err)
        return render(request, "result.html", context)


@login_required
def delete(request):
    form = ReturnForm(request.POST or None)
    context = {"form": form}
    if not form.is_valid():
        return render(request, "assignment/delete.html", context=context)

    context = {
        "name": "IPアドレス割り当て返却　結果",
    }
    try:
        res_data = JPNIC(base=form.cleaned_data.get("jpnic_id")).return_assignment(
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


@login_required
def search(request):
    form = SearchForm(request.GET)
    context = {
        "name": "アドレス情報検索",
        "form": form,
    }
    if not form.is_valid():
        return render(request, "assignment/search.html", context)

    try:
        res_data = JPNIC(base=form.cleaned_data.get("jpnic_id")).get_ip_address(
            ip_address=form.cleaned_data.get("ip_address"),
            kind=form.cleaned_data.get("kind"))

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


@login_required
def result(request):
    context = request.GET.get("context")
    return render(request, "result.html", context=context)
