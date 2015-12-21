from django.core.validators import RegexValidator
from django.db import models
import django.utils.translation as translation
from django.utils.translation import ugettext_lazy as _
import localization.models as localization_models


class Storage(models.Model):
    alphanumeric = RegexValidator(r'^[a-zA-Z]*$', _('Only latin characters are allowed.'))
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    key = models.CharField(max_length=256, unique=True, verbose_name=_('Key'), help_text=_('Key'),
                           validators=[alphanumeric], db_index=True)

    def __str__(self) -> str:
        lang = translation.get_language()
        lang_data = localization_models.Language.objects.filter(short_name=lang).values_list('id', flat=True)
        if lang_data.__len__() > 0:
            value = StorageValue.objects.filter(storage=self, language=lang_data[0]).values_list('name', flat=True)
            if value.__len__() > 0:
                return value[0]
        value = StorageValue.objects.filter(storage=self, default=True).values_list('name', flat=True)
        return value[0]

    @property
    def name(self):
        return str.format("{0} : {1}", self.key, self.__str__())

    class Meta:
        db_table = "info_storage_storage"
        verbose_name = _("Key-value pair")
        verbose_name_plural = _("Storage")


class StorageValue(models.Model):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    value = models.CharField(max_length=256, verbose_name=_('Name'), help_text=_('Name'))
    language = models.ForeignKey(localization_models.Language, verbose_name=_('Language'), help_text=_('Language'))
    storage = models.ForeignKey(Storage, verbose_name=_('Storage'), help_text=_('Storage'))
    default = models.BooleanField(default=False, verbose_name=_('Is default?'), help_text=_('Is default?'))

    class Meta:
        db_table = 'info_storage_storage_values'
        unique_together = ('storage', 'language')
        verbose_name = _('Values')
        verbose_name_plural = _('Value')
