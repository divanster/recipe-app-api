# recipe/serializers.py

from rest_framework import serializers
from core.models import Recipe, Tag, Ingredient, Rating, Follow, Comment, User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user profiles."""
    password = serializers.CharField(write_only=True)
    recipes = serializers.PrimaryKeyRelatedField(many=True, queryset=Recipe.objects.all(), source='recipe_set')
    following = serializers.SerializerMethodField()
    followers = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'password', 'recipes', 'following', 'followers']

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            name=validated_data['name'],
            password=validated_data['password']
        )
        return user

    def get_following(self, obj):
        """Return a list of users the current user is following."""
        follows = Follow.objects.filter(follower=obj)
        return [follow.followee.id for follow in follows]

    def get_followers(self, obj):
        """Return a list of users following the current user."""
        followers = Follow.objects.filter(followee=obj)
        return [follow.follower.id for follow in followers]


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
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(
                **tag,
            )
            recipe.tags.add(tag_obj)

    def _get_or_create_ingredients(self, ingredients, recipe):
        """Handle getting or creating ingredients as needed."""
        for ingredient in ingredients:
            ingredient_obj, created = Ingredient.objects.get_or_create(
                **ingredient,
            )
            recipe.ingredients.add(ingredient_obj)

    def create(self, validated_data):
        """Create a recipe."""
        tags = validated_data.pop('tags', [])
        ingredients = validated_data.pop('ingredients', [])
        recipe = Recipe.objects.create(**validated_data)
        self._get_or_create_tags(tags, recipe)
        self._get_or_create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        """Update recipe."""
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)
        if ingredients is not None:
            instance.ingredients.clear()
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
