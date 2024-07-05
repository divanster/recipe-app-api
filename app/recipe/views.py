"""
Views for the recipe APIs
"""
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)

from rest_framework import (
    viewsets,
    mixins,
    status,
)

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import (
    Recipe,
    Tag,
    Ingredient,
    Rating,
    Follow,
    Comment,
)
from recipe import serializers


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'tags',
                OpenApiTypes.STR,
                description='Comma separated list of tag IDs to filter',
            ),
            OpenApiParameter(
                'ingredients',
                OpenApiTypes.STR,
                description='Comma separated list of ingredient IDs to filter',
            ),
        ]
    )
)
class RecipeViewSet(viewsets.ModelViewSet):
    """View for managing recipe APIs."""
    serializer_class = serializers.RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _params_to_ints(self, qs):
        """Convert a list of strings to integers."""
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        """Retrieve recipes for authenticated user."""
        tags = self.request.query_params.get('tags')
        ingredients = self.request.query_params.get('ingredients')
        queryset = self.queryset
        if tags:
            tag_ids = self._params_to_ints(tags)
            queryset = queryset.filter(tags__id__in=tag_ids)
        if ingredients:
            ingredient_ids = self._params_to_ints(ingredients)
            queryset = queryset.filter(ingredients__id__in=ingredient_ids)

        return queryset.filter(
            user=self.request.user
        ).order_by('-id').distinct()

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action == 'list':
            return serializers.RecipeSerializer
        elif self.action == 'upload_image':
            return serializers.RecipeImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new recipe."""
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Upload an image to recipe."""
        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['POST'], detail=True)
    def like(self, request, pk=None):
        """Like a recipe."""
        recipe = self.get_object()
        recipe.likes.add(request.user)
        return Response(status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=True)
    def unlike(self, request, pk=None):
        """Unlike a recipe."""
        recipe = self.get_object()
        recipe.likes.remove(request.user)
        return Response(status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=True)
    def rate(self, request, pk=None):
        """Rate a recipe."""
        recipe = self.get_object()
        rating_value = request.data.get('score')
        rating, created = Rating.objects.update_or_create(
            user=request.user, recipe=recipe,
            defaults={'score': rating_value}
        )
        recipe.update_rating()
        serializer = serializers.RatingSerializer(rating)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=True, url_path='add-comment')
    def add_comment(self, request, pk=None):
        """Add a comment to a recipe."""
        recipe = self.get_object()
        comment_content = request.data.get('content')
        comment = Comment.objects.create(
            user=request.user,
            recipe=recipe,
            content=comment_content
        )
        serializer = serializers.CommentSerializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'assigned_only',
                OpenApiTypes.INT, enum=[0, 1],
                description='Filter by items assigned to recipes.',
            ),
        ]
    )
)
class BaseRecipeAttrViewSet(mixins.DestroyModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.ListModelMixin,
                            viewsets.GenericViewSet):
    """Base viewset for recipe attributes."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter queryset to authenticated user."""
        assigned_only = bool(
            int(self.request.query_params.get('assigned_only', 0))
        )
        queryset = self.queryset
        if assigned_only:
            queryset = queryset.filter(recipe__isnull=False)

        return queryset.filter(
            user=self.request.user
        ).order_by('-name').distinct()


class TagViewSet(BaseRecipeAttrViewSet):
    """Manage tags in the database."""
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(BaseRecipeAttrViewSet):
    """Manage ingredients in the database."""
    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()


class FollowViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    """Manage following and unfollowing users."""
    serializer_class = serializers.FollowSerializer
    queryset = Follow.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve the follows for the authenticated user."""
        return self.queryset.filter(follower=self.request.user)

    @action(methods=['POST'], detail=True, url_path='follow')
    def follow(self, request, pk=None):
        """Follow a user."""
        user_to_follow = self.get_object()
        Follow.objects.get_or_create(follower=request.user, followee=user_to_follow)
        return Response(status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=True, url_path='unfollow')
    def unfollow(self, request, pk=None):
        """Unfollow a user."""
        user_to_unfollow = self.get_object()
        Follow.objects.filter(follower=request.user, followee=user_to_unfollow).delete()
        return Response(status=status.HTTP_200_OK)


class CommentViewSet(viewsets.GenericViewSet, mixins.DestroyModelMixin):
    """Manage comments in the database."""
    serializer_class = serializers.CommentSerializer
    queryset = Comment.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve the comments for the authenticated user."""
        return self.queryset.filter(user=self.request.user)

    @action(methods=['DELETE'], detail=True, url_path='delete-comment')
    def delete_comment(self, request, pk=None):
        """Delete a comment."""
        comment = self.get_object()
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
