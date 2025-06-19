from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import RecipesViewSet, IngredientViewSet
from .views import UsersViewSet, obtain_auth_token, remove_auth_token


router = DefaultRouter()

router.register('recipes', RecipesViewSet, basename='recipe')
router.register('ingredients', IngredientViewSet)
router.register('users', UsersViewSet, basename='user')

urlpatterns = router.urls


urlpatterns += [
    path('auth/token/login/', obtain_auth_token),
    path('auth/token/logout/', remove_auth_token),
]
