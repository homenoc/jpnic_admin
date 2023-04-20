import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from jpnic_admin.form import (
    GetIPAddressForm,
)
from jpnic_admin.jpnic import (
    JPNIC,
    JPNICReqError,
)


@login_required
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
