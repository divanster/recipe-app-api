from rest_framework import serializers
from core.models import Recipe, Tag, Ingredient, Rating, Follow, Comment, User
from user.serializers import UserSerializer  # Importing the correct UserSerializer


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for ingredients."""

    class Meta:
        model = Ingredient
        fields = ['id', 'name']
        read_only_fields = ['id']


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags."""

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ['id', 'user', 'recipe', 'score']
        read_only_fields = ['id', 'user', 'recipe']


class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ['id', 'follower', 'followee']
        read_only_fields = ['id', 'follower', 'followee']


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'user', 'recipe', 'content', 'created_at']
        read_only_fields = ['id', 'user', 'recipe', 'created_at']


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipes."""
    tags = TagSerializer(many=True, required=False)
    ingredients = IngredientSerializer(many=True, required=False)
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2, read_only=True)
    ratings_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.SerializerMethodField()
    user = UserSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = [
            'id', 'title', 'time_minutes', 'price', 'link', 'tags',
            'ingredients', 'likes', 'average_rating', 'ratings_count', 'is_liked',
            'description', 'image', 'user'
        ]
        read_only_fields = ['id', 'likes', 'average_rating', 'ratings_count', 'is_liked']

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(id=request.user.id).exists()
        return False

    def _get_or_create_tags(self, tags, recipe):
        """Handle getting or creating tags as needed."""
        user = self.context['request'].user
        tag_objects = []
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(
                name=tag['name'],
                defaults={'user': user}
            )
            tag_objects.append(tag_obj)
        recipe.tags.set(tag_objects)

    def _get_or_create_ingredients(self, ingredients, recipe):
        """Handle getting or creating ingredients as needed."""
        user = self.context['request'].user
        ingredient_objects = []
        for ingredient in ingredients:
            ingredient_obj, created = Ingredient.objects.get_or_create(
                name=ingredient['name'],
                defaults={'user': user}
            )
            ingredient_objects.append(ingredient_obj)
        recipe.ingredients.set(ingredient_objects)

    def create(self, validated_data):
        """Create a recipe."""
        tags = validated_data.pop('tags', [])
        ingredients = validated_data.pop('ingredients', [])
        recipe = Recipe.objects.create(**validated_data)
        recipe.user = self.context['request'].user
        recipe.save()
        self._get_or_create_tags(tags, recipe)
        self._get_or_create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        """Update recipe."""
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)
        user = self.context['request'].user

        if tags is not None:
            self._get_or_create_tags(tags, instance)
        if ingredients is not None:
            self._get_or_create_ingredients(ingredients, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for recipe detail view."""
    ratings = RatingSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['ratings', 'comments']


class RecipeImageSerializer(serializers.ModelSerializer):
    """Serializer for uploading images to recipes."""

    class Meta:
        model = Recipe
        fields = ['id', 'image']
        read_only_fields = ['id']
        extra_kwargs = {'image': {'required': 'True'}}
