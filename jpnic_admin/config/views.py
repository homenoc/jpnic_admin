import base64
import threading

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from jpnic_admin.form import (
    ASForm,
    ChangeCertForm,
)
from jpnic_admin.jpnic import (
    verify_expire_p12_file,
    verify_expire_ca,
)
from jpnic_admin.models import JPNIC as JPNICModel
from jpnic_admin.resource.notify import NoticeResource, NoticeCertExpired
from jpnic_admin.resource.task import manual_task


@login_required
def add_as(request):
    if not request.user.is_superuser:
        return render(request, "no_auth.html", {"name": "AS・証明書の追加"})
    if request.method == "POST":
        form = ASForm(request.POST, request.FILES)
        context = {
            "form": form,
        }
        if form.is_valid():
            if not form.cleaned_data["p12"]:
                return render(request, "config/add_as.html", context=context)
            p12_binary = form.cleaned_data["p12"].read()
            p12_base64 = base64.b64encode(p12_binary)
            jpnic_model = JPNICModel.objects.create(
                name=form.cleaned_data.get("name"),
                is_active=True,
                is_ipv6=form.cleaned_data.get("ipv6"),
                collection_interval=form.cleaned_data.get("collection_interval"),
                asn=form.cleaned_data.get("asn"),
                p12_base64=p12_base64.decode("ascii"),
                p12_pass=form.cleaned_data.get("p12_pass"),
            )
            jpnic_model.save()
            context["name"] = "AS・証明書の追加"
            context["data"] = "登録しました"
            return render(request, "result.html", context)
    form = ASForm()
    context = {
        "form": form,
    }
    return render(request, "config/add_as.html", context)


@login_required
def list_as(request):
    if not request.user.is_superuser:
        return render(request, "no_auth.html", {"name": "AS・証明書の確認/変更"})
    if request.method == "POST":
        if "apply" in request.POST:
            form = ChangeCertForm(request.POST, request.FILES)
            jpnic_id = int(request.POST.get("id"))
            context = {
                "form": form,
            }
            if form.is_valid():
                if not form.cleaned_data["p12"]:
                    return render(request, "config/add_as.html", context=context)
                p12_binary = form.cleaned_data["p12"].read()
                p12_base64 = base64.b64encode(p12_binary)
                jpnic_model = JPNICModel.objects.get(id=jpnic_id)
                jpnic_model.p12_base64 = p12_base64.decode("ascii")
                jpnic_model.p12_pass = form.cleaned_data.get("p12_pass")
                jpnic_model.save()
                context["name"] = "AS・証明書の追加"
                context["data"] = "登録しました"
                return render(request, "result.html", context)
        elif "renew_cert" in request.POST:
            jpnic_id = int(request.POST.get("id"))
            form = ChangeCertForm()
            context = {
                "id": jpnic_id,
                "form": form,
            }
            return render(request, "config/change_as.html", context)
        elif "manual_ip" in request.POST:
            jpnic_id = int(request.POST.get("id"))
            threading.Thread(manual_task(type1="アドレス情報", jpnic_id=jpnic_id))

        elif "manual_resource" in request.POST:
            jpnic_id = int(request.POST.get("id"))
            threading.Thread(manual_task(type1="資源情報", jpnic_id=jpnic_id))

    jpnic_model = JPNICModel.objects.all()
    data = []
    ca_expiry_date = verify_expire_ca()
    for jpn in jpnic_model:
        try:
            p12_expiry_date = verify_expire_p12_file(
                p12_base64=jpn.p12_base64, p12_pass=jpn.p12_pass
            )
            data.append({"data": jpn, "expiry_date": p12_expiry_date})
        except:
            data.append(
                {
                    "data": jpn,
                }
            )
    context = {"jpnic": data, "ca_path": settings.CA_PATH, "ca_expiry_date": ca_expiry_date}
    return render(request, "config/list_as.html", context)


@login_required
def notice(request):
    if not request.user.is_superuser:
        return render(request, "no_auth.html", {"name": "通知機能"})
    if request.method == "POST":
        if request.POST.get("id", "") == "notice_cert_expire":
            NoticeCertExpired().to_slack()
        elif request.POST.get("id", "") == "notice_resource":
            NoticeResource().to_slack()

    return render(request, "config/notice.html", {})
