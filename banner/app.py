from django.utils.translation import ugettext_lazy as _
from django.apps import AppConfig


class BannerAppConfig(AppConfig):
    name = 'banner'
    verbose_name = _('Banner')
