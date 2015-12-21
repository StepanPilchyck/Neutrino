from django.db import models
from django.utils.translation import ugettext_lazy as _


class Language(models.Model):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    name = models.CharField(max_length=256, unique=True, verbose_name=_('Name'), help_text=_('Name'))
    short_name = models.CharField(max_length=2, unique=True, verbose_name=_('Short name'), help_text=_('Short name'),
                                  db_index=True)
    first_image = models.ImageField(null=True, blank=True, verbose_name=_('First image'), help_text=_('First image'))
    second_image = models.ImageField(null=True, blank=True, verbose_name=_('Second image'), help_text=_('Second image'))

    def __str__(self) -> str:
        return self.short_name

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None) -> None:
        for field in self._meta.fields:
            if field.name == 'first_image':
                field.upload_to = str.format("language/{0}/first_image/", self.short_name)
            if field.name == 'second_image':
                field.upload_to = str.format("language/{0}/second_image/", self.short_name)
        super(Language, self).save()

    class Meta:
        db_table = "localization_languages"
        verbose_name = _("Language")
        verbose_name_plural = _("Languages")


class Currency(models.Model):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    name = models.CharField(max_length=256, unique=True, verbose_name=_('Name'), help_text=_('Name'))
    short_name = models.CharField(max_length=3, unique=True, verbose_name=_('Short name'), help_text=_('Short name'),
                                  db_index=True)
    first_image = models.ImageField(null=True, blank=True, verbose_name=_('First image'), help_text=_('First image'))
    second_image = models.ImageField(null=True, blank=True, verbose_name=_('Second image'), help_text=_('Second image'))
    coefficient = models.FloatField(verbose_name=_('Coefficient'), help_text=_('Coefficient'))
    default = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.short_name

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None) -> None:
        for field in self._meta.fields:
            if field.name == 'first_image':
                field.upload_to = str.format("currency/{0}/first_image/", self.short_name)
            if field.name == 'second_image':
                field.upload_to = str.format("currency/{0}/second_image/", self.short_name)
        super(Currency, self).save()

    class Meta:
        db_table = "localization_currencies"
        verbose_name = _("Currency")
        verbose_name_plural = _("Currencies")
