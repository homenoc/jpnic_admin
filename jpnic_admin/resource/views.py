import csv
import urllib

from django.http import HttpResponse
from django.shortcuts import render

from .form import (
    SearchForm,
    SearchResourceForm,
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
