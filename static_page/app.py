from django.utils.translation import ugettext_lazy as _
from django.apps import AppConfig


class StaticPageAppConfig(AppConfig):
    name = 'static_page'
    verbose_name = _('Static pages')
