from django.http.response import Http404
from django.shortcuts import redirect
from .models import Recipe


def short_link_redirect_view(request, recipe_id):
    if not Recipe.objects.filter(pk=recipe_id).exists():
        raise Http404(f'Рецепт с id {recipe_id} не существует!')

    return redirect(f'/recipes/{recipe_id}')
