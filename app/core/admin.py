# backend/app/core/admin.py

"""
Django admin customization.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from core import models


class UserAdmin(BaseUserAdmin):
    """Define the admin pages for users."""
    ordering = ['id']
    list_display = ['email', 'name']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal Info'), {'fields': ('name',)}),
        (
            _('Permissions'),
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                )
            }
        ),
        (_('Important dates'), {'fields': ('last_login',)}),
    )
    readonly_fields = ['last_login']
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'password1',
                'password2',
                'name',
                'is_active',
                'is_staff',
                'is_superuser',
            ),
        }),
    )


class RecipeAdmin(admin.ModelAdmin):
    """Admin view for Recipe."""
    list_display = ['title', 'user', 'average_rating', 'ratings_count']
    search_fields = ['title', 'description']
    list_filter = ['tags', 'ingredients']
    filter_horizontal = ['tags', 'ingredients']


class RatingAdmin(admin.ModelAdmin):
    """Admin view for Rating."""
    list_display = ['user', 'recipe', 'score']
    search_fields = ['user__email', 'recipe__title']
    list_filter = ['score']


class FollowAdmin(admin.ModelAdmin):
    """Admin view for Follow."""
    list_display = ['follower', 'followee']
    search_fields = ['follower__email', 'followee__email']


class CommentAdmin(admin.ModelAdmin):
    """Admin view for Comment."""
    list_display = ['user', 'recipe', 'content', 'created_at']
    search_fields = ['user__email', 'recipe__title', 'content']
    list_filter = ['created_at']


admin.site.register(models.User, UserAdmin)
admin.site.register(models.Recipe, RecipeAdmin)
admin.site.register(models.Tag)
admin.site.register(models.Ingredient)
admin.site.register(models.Rating, RatingAdmin)
admin.site.register(models.Follow, FollowAdmin)
admin.site.register(models.Comment, CommentAdmin)
