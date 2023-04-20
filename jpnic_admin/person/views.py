import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

from jpnic_admin.form import (
    AddGroupContact,
    UploadFile,
    Base1,
    GetJPNICHandle,
)
from jpnic_admin.jpnic import (
    JPNIC,
    JPNICReqError,
)


@login_required
def result(request):
    context = request.GET.get("context")
    return render(request, "result.html", context=context)


@login_required
def add(request):
    if request.method == "POST":
        if "manual" in request.POST:
            base_form = Base1(request.POST)
            manual_form = AddGroupContact(request.POST)
            context = {
                "name": "JPNIC 担当者追加　結果",
            }
            if base_form.is_valid() and manual_form.is_valid():
                try:
                    j = JPNIC(
                        asn=base_form.cleaned_data.get("asn"),
                        ipv6=base_form.cleaned_data.get("ipv6"),
                    )
                    res_data = j.add_person(change_req=manual_form.cleaned_data)
                    context["result_html"] = res_data["html"]
                    context["data"] = res_data["data"]
                    context["req_data"] = manual_form.cleaned_data
                except JPNICReqError as exc:
                    result_html = ""
                    if len(exc.args) > 1:
                        result_html = exc.args[1]
                    context["error"] = exc.args[0]
                    context["result_html"] = result_html
                except TypeError as err:
                    context["error"] = str(err)
                return render(request, "result.html", context)
        elif "upload" in request.POST:
            base_form = Base1(request.POST)
            upload_form = UploadFile(request.POST, request.FILES)
            context = {
                "name": "JPNIC 担当者追加　結果",
            }
            print(upload_form.is_valid())
            if not base_form.is_valid() and not upload_form.is_valid():
                context["base_form"] = base_form
                context["upload_form"] = upload_form
                return render(request, "config/add.html", context=context)
            if not upload_form.cleaned_data["file"]:
                return render(request, "config/add.html", context=context)
            json_data = upload_form.cleaned_data["file"].read().decode("utf-8")
            input_data = json.loads(json_data)
            input_data["jpnic_hdl"] = "1"
            try:
                j = JPNIC(
                    asn=base_form.cleaned_data.get("asn"), ipv6=base_form.cleaned_data.get("ipv6")
                )
                res_data = j.add_person(change_req=input_data)
                context["result_html"] = res_data["html"]
                context["data"] = res_data["data"]
                context["req_data"] = input_data
            except JPNICReqError as exc:
                result_html = ""
                if len(exc.args) > 1:
                    result_html = exc.args[1]
                context["error"] = exc.args[0]
                context["result_html"] = result_html
            except TypeError as err:
                context["error"] = str(err)
            return render(request, "result.html", context)
        elif "manual_download" in request.POST:
            manual_form = AddGroupContact(request.POST)
            if manual_form.is_valid():
                data = json.dumps(
                    manual_form.cleaned_data,
                    ensure_ascii=False,
                    indent=4,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                response = HttpResponse(data, content_type="application/json")
                response["Content-Disposition"] = 'attachment; filename="result.json"'
                return response
    base_form = Base1(request.GET)
    manual_form = AddGroupContact(request.GET)
    upload_form = UploadFile(request.GET)
    context = {"base_form": base_form, "manual_form": manual_form, "upload_form": upload_form}
    return render(request, "person/add.html", context)


@login_required
def change(request):
    if request.method == "POST":
        if "search" in request.POST:
            search_form = GetJPNICHandle(request.POST)
            context = {
                "name": "JPNIC 担当者変更　結果",
            }
            if search_form.is_valid():
                try:
                    j = JPNIC(
                        asn=search_form.cleaned_data.get("asn"),
                        ipv6=search_form.cleaned_data.get("ipv6"),
                    )
                    res_data = j.get_jpnic_handle(
                        jpnic_handle=search_form.cleaned_data.get("jpnic_handle")
                    )
                    context["form"] = AddGroupContact(res_data["data"])
                    context["update_date"] = res_data["update_date"]
                    context["base_form"] = Base1(
                        data={
                            "ipv6": search_form.cleaned_data.get("ipv6"),
                            "asn": search_form.cleaned_data.get("asn"),
                        }
                    )

                    return render(request, "person/change.html", context)
                except JPNICReqError as exc:
                    result_html = ""
                    if len(exc.args) > 1:
                        result_html = exc.args[1]
                    context["error"] = exc.args[0]
                    context["result_html"] = result_html
                except TypeError as err:
                    context["error"] = str(err)
                return render(request, "result.html", context)
        elif "apply" in request.POST:
            base_form = Base1(request.POST)
            form = AddGroupContact(request.POST)
            context = {
                "name": "JPNIC 担当者追加　結果",
            }
            if base_form.is_valid() and form.is_valid():
                print(base_form.cleaned_data)
                try:
                    j = JPNIC(
                        asn=base_form.cleaned_data.get("asn"),
                        ipv6=base_form.cleaned_data.get("ipv6"),
                    )
                    res_data = j.add_person(change_req=form.cleaned_data)
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
        elif "download" in request.POST:
            form = AddGroupContact(request.POST)
            if form.is_valid():
                data = json.dumps(
                    form.cleaned_data,
                    ensure_ascii=False,
                    indent=4,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                response = HttpResponse(data, content_type="application/json")
                response["Content-Disposition"] = 'attachment; filename="result.json"'
                return response

    form = GetJPNICHandle()
    context = {
        "form": form,
    }
    return render(request, "get_jpnic_handle.html", context)
