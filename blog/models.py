from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
import markdown


SHELF_CHOICES = [
    ('research', 'Research'),
    ('systems', 'Systems'),
    ('creative', 'Creative Systems'),
    ('archive', 'Archive'),
]

RELATIONSHIP_TYPES = [
    ('builds_on', 'builds on'),
    ('challenges', 'challenges'),
    ('extends', 'extends'),
    ('supersedes', 'supersedes'),
    ('applies', 'applies'),
    ('evidences', 'is evidence for'),
]

# Customize these categories for your research program
ARTICLE_CATEGORIES = [
    ('research', 'Research'),
    ('systems', 'Systems'),
    ('opinion', 'Opinion'),
    ('notes', 'Notes'),
]

CONTENT_TYPES = [
    ('article', 'Article'),
    ('project', 'Project'),
    ('archive', 'Archive'),
    ('page', 'Page'),
]

ARCHIVE_SECTIONS = [
    ('design', 'Design'),
    ('code', 'Code'),
    ('writing', 'Writing'),
]


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Article(models.Model):
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES, default='article')
    category = models.CharField(max_length=30, choices=ARTICLE_CATEGORIES, blank=True)
    archive_section = models.CharField(max_length=20, choices=ARCHIVE_SECTIONS, blank=True)

    tags = models.ManyToManyField(Tag, blank=True)

    body_markdown = models.TextField(blank=True, help_text='Write in Markdown. Rendered to HTML on save.')
    body_html = models.TextField(blank=True, editable=False)
    body_raw_html = models.TextField(blank=True, help_text='Raw HTML override. If set, used instead of Markdown.')

    subtitle = models.CharField(max_length=300, blank=True)
    description = models.TextField(blank=True, max_length=500, help_text='For meta tags and RSS. Auto-generated from body if blank.')

    hero_painting = models.CharField(max_length=200, blank=True, help_text='Filename in writing/images/paintings/, e.g. "my-article.jpg"')

    published_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_published = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0, help_text='Lower = higher in nav. 0 = use date.')

    shelf = models.CharField(max_length=20, choices=SHELF_CHOICES, default='archive', help_text='Research program shelf')
    is_headline = models.BooleanField(default=False, help_text='Flagship article for the research program')

    class Meta:
        ordering = ['-published_date', '-created_at']
        unique_together = [('slug', 'content_type')]

    def __str__(self):
        return f'[{self.content_type}] {self.title}'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if self.body_markdown and not self.body_raw_html:
            import re as _re
            # Extract mermaid blocks before codehilite mangles them
            _mermaid_blocks = []
            def _stash_mermaid(m):
                _mermaid_blocks.append(m.group(1))
                return f'\n\n<MERMAID_PLACEHOLDER_{len(_mermaid_blocks) - 1}>\n\n'
            _md_text = _re.sub(r'```mermaid\n(.*?)```', _stash_mermaid, self.body_markdown, flags=_re.DOTALL)
            self.body_html = markdown.markdown(
                _md_text,
                extensions=['tables', 'fenced_code', 'codehilite', 'smarty'],
            )
            for i, block in enumerate(_mermaid_blocks):
                self.body_html = self.body_html.replace(
                    f'<MERMAID_PLACEHOLDER_{i}>',
                    f'<pre class="mermaid">{block.strip()}</pre>'
                )
        elif self.body_raw_html:
            self.body_html = self.body_raw_html
        if not self.description and self.body_html:
            import re
            text = re.sub(r'<[^>]+>', '', self.body_html)
            self.description = text[:160].strip()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        type_prefix = {
            'article': 'writing',
            'project': 'projects',
            'archive': 'archive',
            'page': 'about',
        }
        prefix = type_prefix.get(self.content_type, 'writing')
        return f'/{prefix}/{self.slug}'

    def get_rendered_body(self):
        return self.body_html


class Thread(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(help_text='What argument does this thread make?')
    research_question = models.TextField(blank=True, help_text='Which research question does this address?')
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'title']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class ThreadArticle(models.Model):
    thread = models.ForeignKey(Thread, related_name='entries', on_delete=models.CASCADE)
    article = models.ForeignKey(Article, related_name='thread_appearances', on_delete=models.CASCADE)
    position = models.PositiveIntegerField()
    annotation = models.TextField(blank=True, help_text='Why this article matters in this thread')

    class Meta:
        ordering = ['position']
        unique_together = [['thread', 'position'], ['thread', 'article']]

    def __str__(self):
        return f'{self.thread.title} #{self.position}: {self.article.title}'


class ArticleLink(models.Model):
    source = models.ForeignKey(Article, related_name='outgoing_links', on_delete=models.CASCADE)
    target = models.ForeignKey(Article, related_name='incoming_links', on_delete=models.CASCADE)
    relationship = models.CharField(max_length=20, choices=RELATIONSHIP_TYPES)
    note = models.TextField(blank=True, help_text='Optional annotation on this relationship')

    class Meta:
        unique_together = [['source', 'target', 'relationship']]

    def __str__(self):
        return f'{self.source.title} {self.get_relationship_display()} {self.target.title}'

    def clean(self):
        if self.source_id and self.target_id and self.source_id == self.target_id:
            raise ValidationError("An article cannot link to itself.")
