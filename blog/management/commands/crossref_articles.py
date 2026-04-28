"""
Smart cross-referencing: scan articles for concept mentions and insert links.

Usage: python manage.py crossref_articles
       python manage.py crossref_articles --dry-run
       python manage.py crossref_articles --slug my-article
"""
import re
from django.core.management.base import BaseCommand
from blog.models import Article


# Map concept phrases to (slug, content_type).
# Add your own entries here as your corpus grows.
CONCEPT_MAP = {
    # Example entries — customize for your research program:
    # 'portable memory': ('portable-memory-article', 'article'),
    # 'exit rights': ('exit-rights', 'article'),
    # 'attestation': ('attestations-design', 'article'),
}


class Command(BaseCommand):
    help = 'Cross-reference articles by inserting links for concept mentions'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--slug', type=str, help='Only process this slug')

    def handle(self, *args, **options):
        if not CONCEPT_MAP:
            self.stdout.write('CONCEPT_MAP is empty. Add entries to crossref_articles.py first.')
            return

        articles = Article.objects.filter(is_published=True, body_markdown__gt='')
        if options['slug']:
            articles = articles.filter(slug=options['slug'])

        self.stdout.write(f'Cross-referencing {articles.count()} articles...')

        modified = 0
        for article in articles:
            html = article.body_html
            changes = 0

            for phrase, (target_slug, target_ct) in CONCEPT_MAP.items():
                if article.slug == target_slug:
                    continue
                target = Article.objects.filter(slug=target_slug, content_type=target_ct).first()
                if not target:
                    continue

                url = target.get_absolute_url()
                if url in html:
                    continue

                pattern = re.compile(re.escape(phrase), re.IGNORECASE)
                match = pattern.search(html)
                if match:
                    linked = f'<a href="{url}">{match.group()}</a>'
                    html = html[:match.start()] + linked + html[match.end():]
                    changes += 1
                    if not options['dry_run']:
                        self.stdout.write(f'      {phrase} → {url}')

            if changes > 0:
                modified += 1
                if not options['dry_run']:
                    article.body_html = html
                    Article.objects.filter(pk=article.pk).update(body_html=html)

        total = sum(1 for _ in CONCEPT_MAP)
        self.stdout.write(f'\nModified {modified}/{articles.count()} articles')
        self.stdout.write(f'Total cross-references: {total}')
