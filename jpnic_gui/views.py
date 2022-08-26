import io
import json

from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.db.models import Q
from django.shortcuts import render

from jpnic_gui.form import SearchForm, AddAssignment, AddGroupContact
from jpnic_gui.jpnic import JPNIC


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
        "jpnic_page": events_page,
        "count_no_data": count_no_data,
        "search_form": form,
    }
    return render(request, 'jpnic_gui/index.html', context)


def get_jpnic_info(request):
    # a_list = Article.objects.filter(pub_date__year=year)
    # result = JPNIC.objects.filter()
    context = {'year': "year"}
    return render(request, 'jpnic_gui/index.html', context)


def add_assignment(request):
    if request.method == 'POST':
        form = AddAssignment(request.POST, request.FILES)
        print("POST!!")
        if form.is_valid():
            print("OK")
            print(form.cleaned_data)
            print(request.FILES)
            datas = []
            if form.cleaned_data['file']:
                print(form.cleaned_data['file'])
                datas = json.loads(form.cleaned_data['file'].read().decode('utf-8'))

            for data in datas:
                j = JPNIC(
                    asn=data['as'],
                )
                j.ipv4_assignment_user(**data)

    else:
        form = AddAssignment()

    context = {
        "form": form,
    }
    return render(request, 'add_assignment.html', context)


def handle_uploaded_file(f):
    print("upload")
    # with open('some/file/name.txt', 'wb+') as destination:
    #     for chunk in f.chunks():
    #         destination.write(chunk)


def add_person(request):
    form = AddGroupContact(request.GET)
    context = {
        "form": form,
    }
    return render(request, 'add_person.html', context)
