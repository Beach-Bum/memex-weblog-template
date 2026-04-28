from django.conf import settings
from .models import ARTICLE_CATEGORIES


def site_context(request):
    return {
        'site_url': settings.SITE_URL,
        'site_name': settings.SITE_NAME,
        'site_author': settings.SITE_AUTHOR,
        'site_thesis': settings.SITE_THESIS,
        'site_description': settings.SITE_DESCRIPTION,
        'categories_nav': ARTICLE_CATEGORIES,
    }
