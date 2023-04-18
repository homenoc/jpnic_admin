import tempfile

from django.http import HttpResponse, FileResponse
from django.shortcuts import render

from .gen import GenFile
from .form import (
    SearchForm,
    SearchResourceForm,
    SearchResourcesForm,
)


def ip_address(request):
    form = SearchForm(request.GET)

    per_page = int(request.GET.get("per_page", 1))
    data = form.get_queryset(page=per_page)

    context = {
        "data": data,
        "per_page": per_page,
        "search_form": form,
    }
    return render(request, "jpnic_admin/index.html", context)


def resource(request):
    form = SearchResourceForm(request.GET)
    events_page = form.get_queryset()

    context = {
        "data": events_page,
        "search_form": form,
    }
    return render(request, "jpnic_admin/resource.html", context)


def resources(request):
    form = SearchResourcesForm(request.GET)
    events_page = form.get_queryset()

    context = {
        "data": events_page,
        "search_form": form,
    }
    for test in events_page["rs_lists"]:
        print(test.id)
    return render(request, "jpnic_admin/resource.html", context)


def export_resources(request):
    form = SearchResourcesForm(request.GET)
    events_page = form.get_queryset()

    context = {
        "data": events_page,
        "search_form": form,
    }

    if events_page is None:
        return render(request, "jpnic_admin/resources.html", context)

    with tempfile.TemporaryDirectory(prefix="tmp_") as dirPath:
        response = HttpResponse(content_type="application/zip")
        zip_path = GenFile(path=dirPath).resource(infos=events_page, response=response)
        response["Content-Disposition"] = "attachment; filename=" + zip_path
        return response
