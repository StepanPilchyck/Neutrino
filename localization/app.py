from django.utils.translation import ugettext_lazy as _
from django.apps import AppConfig


class LocalizationAppConfig(AppConfig):
    name = 'localization'
    verbose_name = _('Localization')
