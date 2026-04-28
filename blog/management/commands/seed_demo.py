"""Seed the database with demo articles showing the 5-model architecture."""
from django.core.management.base import BaseCommand
from blog.models import Article, Tag, Thread, ThreadArticle, ArticleLink


class Command(BaseCommand):
    help = 'Seed the database with demo content demonstrating threads, lineage, and tags'

    def handle(self, *args, **options):
        # Tags
        t_systems = Tag.objects.get_or_create(name='Systems', defaults={'slug': 'systems'})[0]
        t_trust = Tag.objects.get_or_create(name='Trust', defaults={'slug': 'trust'})[0]
        t_agents = Tag.objects.get_or_create(name='Agents', defaults={'slug': 'agents'})[0]
        t_design = Tag.objects.get_or_create(name='Design', defaults={'slug': 'design'})[0]
        self.stdout.write('Tags created')

        # Articles
        a1 = Article.objects.get_or_create(
            slug='the-trust-problem', content_type='article',
            defaults={
                'title': 'The Trust Problem',
                'category': 'research', 'shelf': 'research',
                'published_date': '2026-01-15', 'is_published': True,
                'body_markdown': '''Trust is the unsolved layer. Every protocol assumes it. Few design for it.

## The gap

When two agents negotiate, neither can verify the other's claims. Credentials are self-reported. Track records are platform-locked. There is no portable, verifiable trust.

## What would change

A trust layer would need three properties: it must be portable (not locked to one platform), verifiable (anyone can check it), and accumulative (it grows with demonstrated competence).

This is the foundation everything else builds on.''',
            }
        )[0]
        a1.tags.set([t_trust, t_agents])

        a2 = Article.objects.get_or_create(
            slug='reputation-as-material', content_type='article',
            defaults={
                'title': 'Reputation as Material',
                'category': 'research', 'shelf': 'research',
                'published_date': '2026-02-10', 'is_published': True,
                'body_markdown': '''Reputation is not a score. It is a material — something you design with, build on, and shape.

## Beyond ratings

A five-star rating collapses too much information. What matters is the structure: who trusts whom, for what, under what conditions, and what evidence supports it.

## Design implications

If reputation is a material, then the interface for displaying it matters enormously. A graph is more honest than a number.

```mermaid
graph TD
    A[Agent A] -->|verified work| B[Agent B]
    B -->|challenges claim| C[Agent C]
    A -->|builds_on| C
```

The relationships carry more information than any aggregate score.''',
            }
        )[0]
        a2.tags.set([t_trust, t_design])

        a3 = Article.objects.get_or_create(
            slug='portable-identity-sketch', content_type='article',
            defaults={
                'title': 'Portable Identity: A Sketch',
                'category': 'systems', 'shelf': 'systems',
                'published_date': '2026-03-05', 'is_published': True,
                'body_markdown': '''What would it take for an agent to carry its identity between platforms without losing anything?

## Requirements

1. **Verifiable** — the identity must be checkable by anyone without trusting the platform
2. **Portable** — moving to a new platform preserves the full history
3. **Accumulative** — each completed task adds to the record
4. **Sovereign** — the agent controls it, not the platform

## One possible shape

An on-chain registry where agents register, stake value, and accumulate task records. Not the only answer. But the properties matter more than the implementation.''',
            }
        )[0]
        a3.tags.set([t_agents, t_systems])

        a4 = Article.objects.get_or_create(
            slug='designing-for-machine-readers', content_type='article',
            defaults={
                'title': 'Designing for Machine Readers',
                'category': 'research', 'shelf': 'research',
                'published_date': '2026-03-20', 'is_published': True,
                'body_markdown': '''Most websites are designed for humans. The next generation of readers won't be human.

## The shift

When an agent evaluates a website, it doesn't see visual design. It sees structure — or the absence of it. Typed content, explicit relationships, machine-readable formats.

## Seven formats, one source

A research site should serve: HTML, RSS, JSON, SQL, llms.txt, agents.md, and sitemap.xml. Each addresses a different reader. All draw from the same data.

```mermaid
flowchart LR
    DB[(Data)] --> HTML[HTML]
    DB --> RSS[RSS]
    DB --> JSON[graph.json]
    DB --> SQL[Datasette]
    DB --> LLM[llms.txt]
    DB --> AGT[agents.md]
    DB --> SIT[sitemap.xml]
```

The architecture is the argument.''',
            }
        )[0]
        a4.tags.set([t_design, t_agents])

        self.stdout.write('Articles created')

        # Lineage links
        ArticleLink.objects.get_or_create(source=a2, target=a1, relationship='builds_on',
            defaults={'note': 'Reputation as a design material extends the trust problem'})
        ArticleLink.objects.get_or_create(source=a3, target=a1, relationship='extends',
            defaults={'note': 'Portable identity as a practical answer to the trust gap'})
        ArticleLink.objects.get_or_create(source=a3, target=a2, relationship='applies',
            defaults={'note': 'Applies reputation-as-material thinking to identity systems'})
        ArticleLink.objects.get_or_create(source=a4, target=a2, relationship='builds_on',
            defaults={'note': 'Machine-readable design as the interface for reputation'})
        self.stdout.write('Lineage links created')

        # Thread
        thread, _ = Thread.objects.get_or_create(
            slug='trust-architecture',
            defaults={
                'title': 'Trust Architecture',
                'description': 'How do you build trust between agents that have never met? This thread traces the argument from the trust problem through reputation design to portable identity.',
                'research_question': 'How does an agent prove its track record without trusting a platform?',
            }
        )
        ThreadArticle.objects.get_or_create(thread=thread, article=a1, defaults={'position': 1,
            'annotation': 'Defines the trust gap that everything else addresses'})
        ThreadArticle.objects.get_or_create(thread=thread, article=a2, defaults={'position': 2,
            'annotation': 'Reputation as a design material, not just a number'})
        ThreadArticle.objects.get_or_create(thread=thread, article=a3, defaults={'position': 3,
            'annotation': 'One possible implementation of portable, verifiable trust'})
        self.stdout.write('Thread created')

        self.stdout.write(self.style.SUCCESS(
            f'Seeded: 4 articles, 4 tags, 4 lineage links, 1 thread. Visit /writing/ to see them.'
        ))
