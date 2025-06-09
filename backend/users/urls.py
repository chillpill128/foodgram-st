from rest_framework import routers
from .views import RecipesViewSet, IngredientViewSet


router = routers.SimpleRouter()
router.register(r'recipe', RecipesViewSet)
router.register(r'ingredient', IngredientViewSet)
urlpatterns = router.urls
