from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from django.utils.translation import ugettext_lazy as _
import django.utils.translation as translation
import localization.models as localization_models


class MainMenu(MPTTModel):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', verbose_name=_('Parent'),
                            help_text=_('Parent'))
    url = models.CharField(max_length=256, default=None, null=True, blank=True, verbose_name=_('Url'),
                           help_text=_('Url'))
    first_image = models.ImageField(null=True, blank=True, verbose_name=_('First image'), help_text=_('First image'))
    second_image = models.ImageField(null=True, blank=True, verbose_name=_('Second image'), help_text=_('Second image'))

    def __str__(self) -> str:
        lang = translation.get_language()
        lang_data = localization_models.Language.objects.filter(short_name=lang).values_list('id', flat=True)
        if lang_data.__len__() > 0:
            menu_item_name = \
                MainMenuItemName.objects.filter(menu_item=self, language=lang_data[0]).values_list('name', flat=True)
            if menu_item_name.__len__() > 0:
                return menu_item_name[0]
        menu_item_name = MainMenuItemName.objects.filter(menu_item=self, default=True).values_list('name',
                                                                                                           flat=True)
        return menu_item_name[0]

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None) -> None:
        for field in self._meta.fields:
            if field.name == 'first_image':
                field.upload_to = str.format("main_menu/{0}/menu_element/{0}/first_image/", self.id)
            if field.name == 'second_image':
                field.upload_to = str.format("main_menu/{0}/menu_element/{0}/second_image/", self.id)
        super(MainMenu, self).save()

    def name(self):
        return self.__str__()
    name.short_description = _('Name')

    def check_language_for_name_admin_display(self) -> str:
        """Checks if languages of text data are corresponding to languages of the website"""
        unrealized_languages = localization_models.Language.objects.exclude(
            id__in=self.name_languages_ids).all().values_list('name', flat=True)
        languages__str = "<br/>".join(unrealized_languages)
        if unrealized_languages.__len__() > 0:
            return str.format(
                '<img src="/static/admin/img/icon-no.gif" alt="False"><b>{0}:</b></span><br/>{1}',
                _('Unrealized languages'), languages__str)
        return str.format(
            '<img src="/static/admin/img/icon-yes.gif" alt="True"><span style="margin-left:3px;">{0}</span>',
            _('OK'))
    check_language_for_name_admin_display.allow_tags = True
    check_language_for_name_admin_display.short_description = _('Text data language check')

    @property
    def check_language_for_name(self) -> bool:
        """Checks if languages of text data are corresponding to languages of the website"""
        languages = localization_models.Language.objects.all().values_list('id', flat=True)
        for language in languages:
            if language not in self.name_languages_ids:
                return False
        return True

    @property
    def name_languages(self) -> [str]:
        return MainMenuItemName.objects.filter(menu_item=self).all().values_list('language__name', flat=True)

    @property
    def name_languages_ids(self) -> [int]:
        return MainMenuItemName.objects.filter(menu_item=self).all().values_list('language__id', flat=True)

    class MPTTMeta:
        order_insertion_by = ['url']

    class Meta:
        db_table = 'menu_main_menu_elements'
        verbose_name = _('Main menu item')
        verbose_name_plural = _('Main menu')


class MainMenuItemName(models.Model):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    name = models.CharField(max_length=256, verbose_name=_('Name'), help_text=_('Name'))
    language = models.ForeignKey(localization_models.Language, verbose_name=_('Language'), help_text=_('Language'))
    menu_item = models.ForeignKey(MainMenu, verbose_name=_('Menu item'), help_text=_('Menu item'))
    default = models.BooleanField(default=False, verbose_name=_('Is default?'), help_text=_('Is default?'))

    class Meta:
        db_table = 'menu_main_menu_items_names'
        unique_together = ('menu_item', 'language')
        verbose_name = _('Main menu item names')
        verbose_name_plural = _('Main menu item name')


class AdditionalMenu(MPTTModel):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', verbose_name=_('Parent'),
                            help_text=_('Parent'))
    url = models.CharField(max_length=256, default=None, null=True, blank=True, verbose_name=_('Url'),
                           help_text=_('Url'))
    first_image = models.ImageField(null=True, blank=True, verbose_name=_('First image'), help_text=_('First image'))
    second_image = models.ImageField(null=True, blank=True, verbose_name=_('Second image'), help_text=_('Second image'))

    def __str__(self) -> str:
        lang = translation.get_language()
        lang_data = localization_models.Language.objects.filter(short_name=lang).values_list('id', flat=True)
        if lang_data.__len__() > 0:
            menu_item_name = \
                AdditionalMenuItemName.objects.filter(menu_item=self, language=lang_data[0]).values_list('name',
                                                                                                         flat=True)
            if menu_item_name.__len__() > 0:
                return menu_item_name[0]
        menu_item_name = AdditionalMenuItemName.objects.filter(menu_item=self, default=True).\
            values_list('name', flat=True)
        return menu_item_name[0]

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None) -> None:
        for field in self._meta.fields:
            if field.name == 'first_image':
                field.upload_to = str.format("additional_menu/{0}/menu_element/{0}/first_image/", self.id)
            if field.name == 'second_image':
                field.upload_to = str.format("additional_menu/{0}/menu_element/{0}/second_image/", self.id)
        super(AdditionalMenu, self).save()

    def name(self):
        return self.__str__()
    name.short_description = _('Name')

    def check_language_for_name_admin_display(self) -> str:
        """Checks if languages of text data are corresponding to languages of the website"""
        unrealized_languages = localization_models.Language.objects.exclude(
            id__in=self.name_languages_ids).all().values_list('name', flat=True)
        languages__str = "<br/>".join(unrealized_languages)
        if unrealized_languages.__len__() > 0:
            return str.format(
                '<img src="/static/admin/img/icon-no.gif" alt="False"><b>{0}:</b></span><br/>{1}',
                _('Unrealized languages'), languages__str)
        return str.format(
            '<img src="/static/admin/img/icon-yes.gif" alt="True"><span style="margin-left:3px;">{0}</span>',
            _('OK'))
    check_language_for_name_admin_display.allow_tags = True
    check_language_for_name_admin_display.short_description = _('Text data language check')

    @property
    def check_language_for_name(self) -> bool:
        """Checks if languages of text data are corresponding to languages of the website"""
        languages = localization_models.Language.objects.all().values_list('id', flat=True)
        for language in languages:
            if language not in self.name_languages_ids:
                return False
        return True

    @property
    def name_languages(self) -> [str]:
        return AdditionalMenuItemName.objects.filter(menu_item=self).all().values_list('language__name', flat=True)

    @property
    def name_languages_ids(self) -> [int]:
        return AdditionalMenuItemName.objects.filter(menu_item=self).all().values_list('language__id', flat=True)

    class MPTTMeta:
        order_insertion_by = ['url']

    class Meta:
        db_table = 'menu_additional_menu_elements'
        verbose_name = _('Additional menu item')
        verbose_name_plural = _('Additional menu')


class AdditionalMenuItemName(models.Model):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    name = models.CharField(max_length=256, verbose_name=_('Name'), help_text=_('Name'))
    language = models.ForeignKey(localization_models.Language, verbose_name=_('Language'), help_text=_('Language'))
    menu_item = models.ForeignKey(AdditionalMenu, verbose_name=_('Menu item'), help_text=_('Menu item'))
    default = models.BooleanField(default=False, verbose_name=_('Is default?'), help_text=_('Is default?'))

    class Meta:
        db_table = 'menu_additional_menu_items_names'
        unique_together = ('menu_item', 'language')
        verbose_name = _('Additional menu item names')
        verbose_name_plural = _('Additional menu item name')


class ExtraMenu(MPTTModel):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', verbose_name=_('Parent'),
                            help_text=_('Parent'))
    url = models.CharField(max_length=256, default=None, null=True, blank=True, verbose_name=_('Url'),
                           help_text=_('Url'))
    first_image = models.ImageField(null=True, blank=True, verbose_name=_('First image'), help_text=_('First image'))
    second_image = models.ImageField(null=True, blank=True, verbose_name=_('Second image'), help_text=_('Second image'))

    def __str__(self) -> str:
        lang = translation.get_language()
        lang_data = localization_models.Language.objects.filter(short_name=lang).values_list('id', flat=True)
        if lang_data.__len__() > 0:
            menu_item_name = \
                ExtraMenuItemName.objects.filter(menu_item=self, language=lang_data[0]).values_list('name', flat=True)
            if menu_item_name.__len__() > 0:
                return menu_item_name[0]
        menu_item_name = ExtraMenu.objects.filter(menu_item=self, default=True).values_list('name', flat=True)
        return menu_item_name[0]

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None) -> None:
        for field in self._meta.fields:
            if field.name == 'first_image':
                field.upload_to = str.format("extra_menu/{0}/menu_element/{0}/first_image/", self.id)
            if field.name == 'second_image':
                field.upload_to = str.format("extra_menu/{0}/menu_element/{0}/second_image/", self.id)
        super(ExtraMenu, self).save()

    def name(self):
        return self.__str__()
    name.short_description = _('Name')

    def check_language_for_name_admin_display(self) -> str:
        """Checks if languages of text data are corresponding to languages of the website"""
        unrealized_languages = localization_models.Language.objects.exclude(
            id__in=self.name_languages_ids).all().values_list('name', flat=True)
        languages__str = "<br/>".join(unrealized_languages)
        if unrealized_languages.__len__() > 0:
            return str.format(
                '<img src="/static/admin/img/icon-no.gif" alt="False"><b>{0}:</b></span><br/>{1}',
                _('Unrealized languages'), languages__str)
        return str.format(
            '<img src="/static/admin/img/icon-yes.gif" alt="True"><span style="margin-left:3px;">{0}</span>',
            _('OK'))
    check_language_for_name_admin_display.allow_tags = True
    check_language_for_name_admin_display.short_description = _('Text data language check')

    @property
    def check_language_for_name(self) -> bool:
        """Checks if languages of text data are corresponding to languages of the website"""
        languages = localization_models.Language.objects.all().values_list('id', flat=True)
        for language in languages:
            if language not in self.name_languages_ids:
                return False
        return True

    @property
    def name_languages(self) -> [str]:
        return ExtraMenuItemName.objects.filter(menu_item=self).all().values_list('language__name', flat=True)

    @property
    def name_languages_ids(self) -> [int]:
        return ExtraMenuItemName.objects.filter(menu_item=self).all().values_list('language__id', flat=True)

    class MPTTMeta:
        order_insertion_by = ['url']

    class Meta:
        db_table = 'menu_extra_menu_elements'
        verbose_name = _('Extra menu item')
        verbose_name_plural = _('Extra menu')


class ExtraMenuItemName(models.Model):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    name = models.CharField(max_length=256, verbose_name=_('Name'), help_text=_('Name'))
    language = models.ForeignKey(localization_models.Language, verbose_name=_('Language'), help_text=_('Language'))
    menu_item = models.ForeignKey(ExtraMenu, verbose_name=_('Menu item'), help_text=_('Menu item'))
    default = models.BooleanField(default=False, verbose_name=_('Is default?'), help_text=_('Is default?'))

    class Meta:
        db_table = 'menu_extra_menu_items_names'
        unique_together = ('menu_item', 'language')
        verbose_name = _('Extra menu item names')
        verbose_name_plural = _('Extra menu item name')
