# Memex Weblog Template

A structured research weblog with five interlocking data models and seven machine-readable output formats. Not a blog — a knowledge architecture.

Named after Vannevar Bush's 1945 [Memex](https://en.wikipedia.org/wiki/Memex) — a theoretical device for storing, linking, and retrieving all of a person's knowledge.

## What this is

Most personal websites are flat: posts in a feed, maybe categories. That works for a diary. It doesn't work for a research program where the relationship between ideas is the primary artifact.

This template gives you:

### Five data models

1. **Articles** — typed content with categories, shelves, and publication dates
2. **Tags** — lightweight thematic crosscuts across the corpus
3. **Threads** — curated reading paths organized around thesis questions
4. **Lineage** — typed relationships between articles (builds_on, challenges, extends, supersedes, applies, evidences)
5. **Shelves** — maturity levels: Research, Systems, Creative Systems, Archive

### Seven output formats

All drawing from the same data:

| Format | Reader | URL |
|--------|--------|-----|
| HTML | Browsers | `/` |
| RSS | Subscribers | `/feed.xml` |
| JSON graph | Knowledge tools | `/graph.json` |
| SQL | Researchers | `/data/` |
| llms.txt | Language models | `/llms.txt` |
| agents.md | Autonomous agents | `/agents.md` |
| Sitemap | Search engines | `/sitemap.xml` |

### Bonus features

- **Knowledge graph** — interactive D3 visualization at `/graph/`
- **Research observatory** — thesis, questions, threads, and headlines at `/research/`
- **Datasette** — full SQL query interface at `/data/`
- **Floyd-Steinberg dithering** — image processing script for hero images
- **Mermaid diagrams** — renders in article bodies automatically
- **Dark mode** — localStorage-persisted toggle
- **Cross-referencing** — auto-link concept mentions across articles

## Quick start

```bash
# Clone
git clone https://github.com/YOUR-USERNAME/memex-weblog-template.git
cd memex-weblog-template

# Set up
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Initialize
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo  # creates 4 demo articles with lineage + threads

# Export for Datasette
python manage.py export_sqlite

# Run
python manage.py runserver
```

Visit `http://localhost:8000` to see the demo content. Visit `/admin/` to manage articles.

## Customization

### Site identity

Set environment variables or edit `memex/settings.py`:

```bash
SITE_NAME="Your Name's Research"
SITE_AUTHOR="Your Name"
SITE_THESIS="Your research thesis goes here."
SITE_DESCRIPTION="A structured research program."
SITE_URL="https://yourdomain.com"
```

### Categories

Edit `ARTICLE_CATEGORIES` in `blog/models.py` to match your research areas.

### Cross-references

Add entries to `CONCEPT_MAP` in `blog/management/commands/crossref_articles.py`:

```python
CONCEPT_MAP = {
    'portable memory': ('portable-memory', 'article'),
    'exit rights': ('exit-rights', 'article'),
}
```

Then run `python manage.py crossref_articles`.

### Hero images

1. Place original in `writing/images/paintings/your-slug.jpg`
2. Dither it: `python -c "from scripts.dither import dither_image; dither_image('writing/images/paintings/your-slug.jpg').save('writing/images/dithered/your-slug.png')"`
3. Set `hero_painting = "your-slug.jpg"` on the article

## Deployment

Works on any platform that runs Python (Railway, Render, Fly.io, Vercel, etc.):

```bash
# Railway
railway up

# Or any platform with Procfile support
gunicorn memex.wsgi --bind 0.0.0.0:$PORT
```

For Postgres, set `DATABASE_URL` or individual `DB_*` environment variables. Falls back to SQLite for local development.

## The architecture

```
Article ──── Tags (many-to-many, thematic crosscuts)
  │
  ├── Thread Entries (ordered position in curated reading paths)
  │     └── Thread (thesis question + description)
  │
  ├── Lineage (typed: builds_on, challenges, extends, supersedes, applies, evidences)
  │     └── Target Article
  │
  ├── Category (research area)
  └── Shelf (maturity level)
```

Every article exists in at least five simultaneous contexts. No article is isolated. Every article is a node in a graph.

## Philosophy

> "The structure of a knowledge system determines what kinds of thinking it can support."

This template is designed to be read by things that don't exist yet. Whether that turns out to be prescient or paranoid probably depends on the next few years.

## License

MIT
