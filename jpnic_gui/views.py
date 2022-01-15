from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.db.models import Q
from django.shortcuts import render

from jpnic_gui.form import SearchForm


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
