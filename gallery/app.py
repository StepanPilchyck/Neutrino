from django.utils.translation import ugettext_lazy as _
from django.apps import AppConfig


class GalleryAppConfig(AppConfig):
    name = 'gallery'
    verbose_name = _('Gallery')
