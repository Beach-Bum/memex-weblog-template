"""Export all published content to a SQLite database for Datasette."""
import sqlite3
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand
from blog.models import Article, Tag, Thread, ThreadArticle, ArticleLink


class Command(BaseCommand):
    help = 'Export published articles, links, and threads to data/blog.db for Datasette'

    def handle(self, *args, **options):
        db_path = Path(settings.BASE_DIR) / 'data' / 'blog.db'
        db_path.parent.mkdir(exist_ok=True)
        if db_path.exists():
            db_path.unlink()

        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()

        # Articles
        c.execute('''CREATE TABLE articles (
            id INTEGER PRIMARY KEY, title TEXT, slug TEXT, url TEXT,
            content_type TEXT, category TEXT, shelf TEXT,
            description TEXT, published_date TEXT, body_text TEXT
        )''')

        articles = Article.objects.filter(is_published=True)
        import re
        for a in articles:
            text = re.sub(r'<[^>]+>', '', a.body_html or '')
            c.execute('INSERT INTO articles VALUES (?,?,?,?,?,?,?,?,?,?)', (
                a.id, a.title, a.slug, a.get_absolute_url(),
                a.content_type, a.category, a.shelf,
                a.description, str(a.published_date) if a.published_date else None, text,
            ))

        # FTS
        c.execute('CREATE VIRTUAL TABLE articles_fts USING fts5(title, body_text, content=articles, content_rowid=id)')
        c.execute("INSERT INTO articles_fts(articles_fts) VALUES('rebuild')")

        # Tags
        c.execute('CREATE TABLE tags (id INTEGER PRIMARY KEY, name TEXT, slug TEXT)')
        for t in Tag.objects.all():
            c.execute('INSERT INTO tags VALUES (?,?,?)', (t.id, t.name, t.slug))

        c.execute('CREATE TABLE article_tags (id INTEGER PRIMARY KEY AUTOINCREMENT, article_id INTEGER, tag_id INTEGER)')
        for a in articles:
            for t in a.tags.all():
                c.execute('INSERT INTO article_tags (article_id, tag_id) VALUES (?,?)', (a.id, t.id))

        # Threads
        c.execute('CREATE TABLE threads (id INTEGER PRIMARY KEY, title TEXT, slug TEXT, description TEXT)')
        threads = Thread.objects.all()
        for t in threads:
            c.execute('INSERT INTO threads VALUES (?,?,?,?)', (t.id, t.title, t.slug, t.description))

        c.execute('CREATE TABLE thread_entries (id INTEGER PRIMARY KEY, thread_id INTEGER, article_id INTEGER, position INTEGER, annotation TEXT)')
        for te in ThreadArticle.objects.all():
            c.execute('INSERT INTO thread_entries VALUES (?,?,?,?,?)', (
                te.id, te.thread_id, te.article_id, te.position, te.annotation,
            ))

        # Lineage
        c.execute('CREATE TABLE lineage (id INTEGER PRIMARY KEY, source_id INTEGER, target_id INTEGER, relationship TEXT, note TEXT)')
        links = ArticleLink.objects.all()
        for l in links:
            c.execute('INSERT INTO lineage VALUES (?,?,?,?,?)', (
                l.id, l.source_id, l.target_id, l.relationship, l.note,
            ))

        conn.commit()
        conn.close()
        self.stdout.write(f'Exported {articles.count()} articles, {links.count()} links, {threads.count()} threads → {db_path}')
