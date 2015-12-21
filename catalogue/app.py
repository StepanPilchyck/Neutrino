from django.utils.translation import ugettext_lazy as _
from django.apps import AppConfig


class CatalogueAppConfig(AppConfig):
    name = 'catalogue'
    verbose_name = _('Catalogue')
