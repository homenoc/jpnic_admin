import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

from .form import (
    AddForm,
    BaseForm,
    UploadFile,
    GetJPNICHandleForm,
)
from jpnic_admin.jpnic import (
    JPNIC,
    JPNICReqError,
)


@login_required
def result(request):
    if not request.user.is_superuser:
        return render(request, "no_auth.html", {"name": "担当者ツール(結果)"})
    context = request.GET.get("context")
    return render(request, "result.html", context=context)


@login_required
def add(request):
    if not request.user.is_superuser:
        return render(request, "no_auth.html", {"name": "担当者ツール(追加)"})
    if "manual" in request.POST:
        base_form = BaseForm(request.POST)
        manual_form = AddForm(request.POST)
        context = {
            "name": "JPNIC 担当者追加　結果",
        }
        if not base_form.is_valid() and not manual_form.is_valid():
            return
        try:
            base = base_form.cleaned_data.get("jpnic_id")
            res_data = JPNIC(base=base).add_person(change_req=manual_form.cleaned_data)
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
        base_form = BaseForm(request.POST)
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
            base = base_form.cleaned_data.get("jpnic_id")
            res_data = JPNIC(base=base).add_person(change_req=input_data)
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
        manual_form = AddForm(request.POST)
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
    base_form = BaseForm(request.GET)
    manual_form = AddForm(request.GET)
    upload_form = UploadFile(request.GET)
    context = {"base_form": base_form, "manual_form": manual_form, "upload_form": upload_form}
    return render(request, "person/add.html", context)


@login_required
def change(request):
    if not request.user.is_superuser:
        return render(request, "no_auth.html", {"name": "担当者ツール(変更)"})
    if "search" in request.POST:
        search_form = GetJPNICHandleForm(request.POST)
        context = {
            "name": "JPNIC 担当者変更　結果",
        }
        if search_form.is_valid():
            try:
                base = search_form.cleaned_data.get("jpnic_id")
                res_data = JPNIC(base=base).get_jpnic_handle(
                    jpnic_handle=search_form.cleaned_data.get("jpnic_handle")
                )
                context["form"] = AddForm(res_data["data"])
                context["update_date"] = res_data["update_date"]
                context["base_form"] = BaseForm(
                    data={
                        "jpnic_id": base,
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
        base_form = BaseForm(request.POST)
        form = AddForm(request.POST)
        context = {
            "name": "JPNIC 担当者追加　結果",
        }
        if base_form.is_valid() and form.is_valid():
            print(base_form.cleaned_data)
            try:
                base = base_form.cleaned_data.get("jpnic_id")
                res_data = JPNIC(base=base).add_person(change_req=form.cleaned_data)
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
        form = AddForm(request.POST)
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

    form = GetJPNICHandleForm()
    context = {
        "form": form,
    }
    return render(request, "person/search.html", context)
