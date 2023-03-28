from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.shortcuts import render

from jpnic_admin.log.form import SearchForm


def index(request):
    form = SearchForm(request.GET)
    events = form.get_queryset().order_by(
        "-last_checked_at",
    )

    paginator = Paginator(events, int(request.GET.get("per_page", "20")))
    page = int(request.GET.get("page", "1"))
    try:
        events_page = paginator.page(page)
    except (EmptyPage, InvalidPage):
        events_page = paginator.page(paginator.num_pages)

    context = {
        "events_page": events_page,
        "search_form": form,
    }
    return render(request, "log/index.html", context)
