from django.contrib import admin  # type: ignore

# Register your models here.
from .models import Category, Comment, Location, Post

admin.site.empty_value_display = 'Не задано'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'text', 'post', 'author', 'created_at'
    )
    search_fields = ('text', 'post', 'author')
    list_filter = ('post', 'author')
    list_display_links = ('post',)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'text',
        'is_published',
        'author',
        'pub_date',
        'location',
        'category'
    )
    list_editable = (
        'is_published',
        'location',
        'category'
    )
    search_fields = ('title', 'text', 'location')
    list_filter = ('category', 'location', 'author')
    list_display_links = ('title',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'is_published',
        'slug',
        'created_at'
    )
    list_editable = (
        'is_published',
        'slug'
    )
    list_display_links = ('title',)
    search_fields = ('title', 'slug')


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'is_published',
        'created_at'
    )
    list_editable = (
        'is_published',
    )
    list_display_links = ('name',)
    search_fields = ('name',)
