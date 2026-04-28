import asyncio
import json
import traceback
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string

from .models import Article, Tag, Thread, ArticleLink, ARTICLE_CATEGORIES


# ── HTML views ──

def home(request):
    articles = Article.objects.filter(content_type='article', is_published=True)
    grouped = []
    for key, label in ARTICLE_CATEGORIES:
        group = articles.filter(category=key)
        if group.exists():
            grouped.append({'key': key, 'label': label, 'articles': group})
    return render(request, 'home.html', {'grouped': grouped})


def article_detail(request, slug):
    content_type_map = {
        'writing': 'article',
        'projects': 'project',
        'archive': 'archive',
        'about': 'page',
    }
    prefix = request.path.strip('/').split('/')[0]
    ct = content_type_map.get(prefix, 'article')
    article = get_object_or_404(Article, slug=slug, content_type=ct, is_published=True)

    # Lineage links
    outgoing = ArticleLink.objects.filter(source=article).select_related('target')
    incoming = ArticleLink.objects.filter(target=article).select_related('source')

    # Thread appearances
    threads = article.thread_appearances.select_related('thread').order_by('thread__title')

    return render(request, 'single_article.html', {
        'article': article,
        'outgoing_links': outgoing,
        'incoming_links': incoming,
        'thread_appearances': threads,
    })


def projects_list(request):
    projects = Article.objects.filter(content_type='project', is_published=True)
    return render(request, 'projects_list.html', {'projects': projects})


def archive_list(request):
    articles = Article.objects.filter(content_type='archive', is_published=True)
    return render(request, 'archive_list.html', {'articles': articles})


def tag_view(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    articles = Article.objects.filter(tags=tag, is_published=True)
    return render(request, 'tag_view.html', {'tag': tag, 'articles': articles})


def research_view(request):
    threads = Thread.objects.prefetch_related('entries__article').all()
    headlines = Article.objects.filter(is_headline=True, is_published=True)
    return render(request, 'research.html', {
        'threads': threads,
        'headlines': headlines,
    })


def graph_view(request):
    return render(request, 'graph.html')


# ── Machine-readable formats ──

def graph_json(request):
    articles = Article.objects.filter(is_published=True).prefetch_related('tags')
    links = ArticleLink.objects.select_related('source', 'target').all()

    nodes = []
    for a in articles:
        nodes.append({
            'id': a.id,
            'title': a.title,
            'slug': a.slug,
            'url': a.get_absolute_url(),
            'category': a.category,
            'shelf': a.shelf,
            'tags': [t.name for t in a.tags.all()],
            'published': str(a.published_date) if a.published_date else None,
        })

    edges = []
    for link in links:
        edges.append({
            'source': link.source_id,
            'target': link.target_id,
            'relationship': link.relationship,
            'note': link.note,
        })

    return JsonResponse({'nodes': nodes, 'edges': edges})


def rss_feed(request):
    articles = Article.objects.filter(
        content_type='article', is_published=True
    ).order_by('-published_date')[:20]
    xml = render_to_string('feed.xml', {
        'articles': articles,
        'site_url': settings.SITE_URL,
        'site_name': settings.SITE_NAME,
        'site_author': settings.SITE_AUTHOR,
        'site_description': settings.SITE_DESCRIPTION,
    })
    return HttpResponse(xml, content_type='application/xml')


def sitemap_view(request):
    articles = Article.objects.filter(is_published=True)
    xml = render_to_string('sitemap.xml', {
        'articles': articles,
        'site_url': settings.SITE_URL,
    })
    return HttpResponse(xml, content_type='application/xml')


def llms_txt(request):
    articles = Article.objects.filter(
        content_type='article', is_published=True
    ).order_by('-published_date')
    threads = Thread.objects.prefetch_related('entries__article').all()

    lines = [
        f'# {settings.SITE_NAME}',
        f'> {settings.SITE_DESCRIPTION}',
        '',
        f'## Author: {settings.SITE_AUTHOR}',
        f'## Thesis: {settings.SITE_THESIS}',
        '',
        '## Articles',
    ]
    for a in articles:
        lines.append(f'- [{a.title}]({settings.SITE_URL}{a.get_absolute_url()})')
        if a.description:
            lines.append(f'  {a.description}')

    lines.append('')
    lines.append('## Threads')
    for t in threads:
        lines.append(f'### {t.title}')
        lines.append(f'{t.description}')
        for entry in t.entries.all():
            lines.append(f'  {entry.position}. [{entry.article.title}]({settings.SITE_URL}{entry.article.get_absolute_url()})')
            if entry.annotation:
                lines.append(f'     {entry.annotation}')

    return HttpResponse('\n'.join(lines), content_type='text/plain; charset=utf-8')


def agents_md(request):
    articles = Article.objects.filter(is_published=True).prefetch_related('tags')
    links = ArticleLink.objects.select_related('source', 'target').all()

    lines = [
        f'# {settings.SITE_NAME} — Agent Interface',
        '',
        f'Author: {settings.SITE_AUTHOR}',
        f'Thesis: {settings.SITE_THESIS}',
        '',
        '## Capabilities',
        f'- {articles.count()} published articles across research, systems, and creative work',
        f'- {links.count()} typed lineage links (builds_on, challenges, extends, supersedes, applies, evidences)',
        f'- Knowledge graph at /graph.json',
        f'- SQL queries at /data/',
        f'- Full-text search via Datasette',
        '',
        '## Endpoints',
        f'- HTML: {settings.SITE_URL}/',
        f'- RSS: {settings.SITE_URL}/feed.xml',
        f'- Knowledge Graph: {settings.SITE_URL}/graph.json',
        f'- SQL: {settings.SITE_URL}/data/',
        f'- LLM Context: {settings.SITE_URL}/llms.txt',
        f'- Agent Interface: {settings.SITE_URL}/agents.md',
        f'- Sitemap: {settings.SITE_URL}/sitemap.xml',
    ]

    return HttpResponse('\n'.join(lines), content_type='text/plain; charset=utf-8')


# ── Datasette proxy ──

_datasette_instance = None

def _get_datasette():
    global _datasette_instance
    if _datasette_instance is not None:
        return _datasette_instance

    from datasette.app import Datasette

    db_path = Path(settings.BASE_DIR) / 'data' / 'blog.db'
    if not db_path.exists():
        return None

    template_dir = str(Path(settings.BASE_DIR) / 'datasette_templates')
    _datasette_instance = Datasette(
        [str(db_path)],
        settings={'base_url': '/data/'},
        template_dir=template_dir,
    )
    return _datasette_instance


def datasette_proxy(request, path=''):
    ds = _get_datasette()
    if ds is None:
        return HttpResponse('Datasette database not found. Run: python manage.py export_sqlite', status=503)

    scope = {
        'type': 'http',
        'method': request.method,
        'path': f'/data/{path}',
        'query_string': request.META.get('QUERY_STRING', '').encode(),
        'headers': [(k.lower().encode(), v.encode()) for k, v in request.headers.items()],
    }

    response_started = False
    status_code = 200
    response_headers = []
    body_parts = []

    async def receive():
        body = request.body
        return {'type': 'http.request', 'body': body}

    async def send(message):
        nonlocal response_started, status_code, response_headers
        if message['type'] == 'http.response.start':
            response_started = True
            status_code = message['status']
            response_headers = message.get('headers', [])
        elif message['type'] == 'http.response.body':
            body_parts.append(message.get('body', b''))

    try:
        asgi_app = ds.app()
        loop = asyncio.new_event_loop()
        loop.run_until_complete(asgi_app(scope, receive, send))
        loop.close()

        body = b''.join(body_parts)
        content_type = 'text/html'
        for key, value in response_headers:
            if key == b'content-type':
                content_type = value.decode()
                break

        return HttpResponse(body, status=status_code, content_type=content_type)
    except Exception as e:
        return HttpResponse(f'Datasette error: {e}', status=500)
