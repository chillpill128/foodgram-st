from rest_framework.routers import DefaultRouter

from recipes.views import RecipesViewSet, IngredientViewSet
from users.views import UsersViewSet


router = DefaultRouter()

router.register('recipes', RecipesViewSet)
router.register('ingredients', IngredientViewSet)
router.register('users', UsersViewSet)

urlpatterns = router.urls
