"""
URL mappings for the recipe app.
"""
from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter

from recipe import views


router = DefaultRouter()
router.register('recipes', views.RecipeViewSet)
router.register('tags', views.TagViewSet)
router.register('ingredients', views.IngredientViewSet)
router.register('follow', views.FollowViewSet, basename='follow')
router.register('comments', views.CommentViewSet, basename='comment')

app_name = 'recipe'

urlpatterns = [
    path('', include(router.urls)),
    path('comments/<int:pk>/delete-comment/', views.CommentViewSet.as_view({'delete': 'destroy'}), name='delete-comment'),
    path('profile/<int:pk>/', views.ProfileView.as_view(), name='profile'),
]
