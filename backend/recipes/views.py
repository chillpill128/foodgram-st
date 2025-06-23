from django.http.response import HttpResponseRedirect
from django.urls import reverse

from .utils import get_pk_from_short_code


def short_link_view(request, short_code):
    pk = get_pk_from_short_code(short_code)
    url = reverse('recipe-detail', kwargs={'pk': pk})
    return HttpResponseRedirect(url)
