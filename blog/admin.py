from django.contrib import admin
from .models import Article, Tag, Thread, ThreadArticle, ArticleLink


class ThreadArticleInline(admin.TabularInline):
    model = ThreadArticle
    extra = 1


class ArticleLinkInline(admin.TabularInline):
    model = ArticleLink
    fk_name = 'source'
    extra = 1


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'content_type', 'category', 'shelf', 'is_published', 'published_date']
    list_filter = ['content_type', 'category', 'shelf', 'is_published']
    search_fields = ['title', 'slug']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ArticleLinkInline]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'sort_order']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ThreadArticleInline]


@admin.register(ArticleLink)
class ArticleLinkAdmin(admin.ModelAdmin):
    list_display = ['source', 'relationship', 'target']
    list_filter = ['relationship']
