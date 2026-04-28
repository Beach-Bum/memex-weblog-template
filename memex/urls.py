from django.contrib import admin
from django.urls import path
from blog import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('writing/<slug:slug>', views.article_detail, name='article_detail'),
    path('projects/<slug:slug>', views.article_detail, name='project_detail'),
    path('projects/', views.projects_list, name='projects_list'),
    path('archive/<slug:slug>', views.article_detail, name='archive_detail'),
    path('archive/', views.archive_list, name='archive_list'),
    path('about/<slug:slug>', views.article_detail, name='page_detail'),
    path('tag/<slug:slug>', views.tag_view, name='tag_view'),
    path('research/', views.research_view, name='research'),
    path('graph/', views.graph_view, name='graph'),
    path('graph.json', views.graph_json, name='graph_json'),
    path('feed.xml', views.rss_feed, name='rss_feed'),
    path('sitemap.xml', views.sitemap_view, name='sitemap'),
    path('llms.txt', views.llms_txt, name='llms_txt'),
    path('agents.md', views.agents_md, name='agents_md'),
    path('data/<path:path>', views.datasette_proxy, name='datasette'),
    path('data/', views.datasette_proxy, name='datasette_root'),
]
