from django.utils.translation import ugettext_lazy as _
from django.apps import AppConfig


class MenuAppConfig(AppConfig):
    name = 'menu'
    verbose_name = _('Menu')
