from django.utils.translation import ugettext_lazy as _
from django.apps import AppConfig


class InfoStorageAppConfig(AppConfig):
    name = 'info_storage'
    verbose_name = _('Information Storage')
