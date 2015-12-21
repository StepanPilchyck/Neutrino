from django.db import models
from django.contrib.auth import models as auth_models
from django.utils.translation import ugettext_lazy as _
import localization.models as localization_models
from gallery import models as gallery_models
import sortedm2m.fields as sortedm2m
from image_cropping import ImageRatioField
from easy_thumbnails.files import get_thumbnailer
import django.utils.translation as translation
import os
import neutrino.settings as settings
import shutil


# Category
class CategoryTemplate(models.Model):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    name = models.CharField(max_length=256, verbose_name=_('Name'), help_text=_('Name'), unique=True)
    path = models.CharField(max_length=256, verbose_name=_('Path'), help_text=_('Path'), unique=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "catalogue_category_templates"
        verbose_name = _("Category Template")
        verbose_name_plural = _("Categories Templates")


class Category(models.Model):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    default_language = models.ForeignKey(localization_models.Language, verbose_name=_('Default language'),
                                         help_text=_('Default language'))
    galleries = sortedm2m.SortedManyToManyField(gallery_models.Gallery, blank=True, verbose_name=_('Galleries'),
                                                help_text=_('Galleries'))
    template = models.ForeignKey(CategoryTemplate, verbose_name=_('Template'), help_text=_('Template'))
    url = models.CharField(max_length=256, db_index=True, unique=True, verbose_name=_('Url'), help_text=_('Url'))
    first_image = models.ImageField(null=True, blank=True, verbose_name=_('First image'), help_text=_('First image'))
    second_image = models.ImageField(null=True, blank=True, verbose_name=_('Second image'), help_text=_('Second image'))

    def __str__(self) -> str:
        lang = translation.get_language()
        language = localization_models.Language.objects.filter(short_name=lang).values_list('id', flat=True)
        if language.__len__() > 0:
            language = language[0]
            category_name = CategoryName.objects.filter(category=self, language=language).values_list('name', flat=True)
            if category_name.__len__() > 0:
                return category_name[0]
        category_name = CategoryName.objects.filter(category=self, default=True).values_list('name', flat=True)[0]
        return category_name

    def texts_languages_admin_display(self) -> str:
        return "<br/>".join(self.text_languages_names)

    texts_languages_admin_display.allow_tags = True
    texts_languages_admin_display.short_description = _('Languages of texts')

    def seo_information_languages_admin_display(self) -> str:
        return "<br/>".join(self.seo_information_languages_names)

    seo_information_languages_admin_display.allow_tags = True
    seo_information_languages_admin_display.short_description = _('Languages of SEO information')

    def check_language_admin_display(self) -> str:
        """Checks if languages of texts are corresponding to seo information languages of this category"""
        if self.check_language:
            return str.format(
                '<img src="/static/admin/img/icon-yes.gif" alt="True"><span style="margin-left:3px;">{0}</span>',
                _('Languages of text is correspond to languages of SEO information'))
        return str.format(
            '<img src="/static/admin/img/icon-no.gif" alt="False"><span style="margin-left:3px;">{0}</span>',
            _('Languages of text does not correspond to languages of SEO information'))

    check_language_admin_display.allow_tags = True
    check_language_admin_display.short_description = _('Language check')

    def check_language_for_seo_admin_display(self) -> str:
        """Checks if seo information languages are corresponding to languages of the website"""
        unrealized_languages = localization_models.Language.objects.exclude(
            id__in=self.seo_information_languages_ids).all().values_list('name', flat=True)
        languages__str = "<br/>".join(unrealized_languages)
        if unrealized_languages.__len__() > 0:
            return str.format(
                '<img src="/static/admin/img/icon-no.gif" alt="False"><b>{0}:</b></span><br/>{1}',
                _('Unrealized languages'), languages__str)
        return str.format(
            '<img src="/static/admin/img/icon-yes.gif" alt="True"><span style="margin-left:3px;">{0}</span>',
            _('OK'))

    check_language_for_seo_admin_display.allow_tags = True
    check_language_for_seo_admin_display.short_description = _('Seo language check')

    def check_language_for_text_admin_display(self) -> str:
        """Checks if texts languages are corresponding to languages of the website"""
        unrealized_languages = localization_models.Language.objects.exclude(
            id__in=self.text_languages_ids).all().values_list('name', flat=True)
        languages__str = "<br/>".join(unrealized_languages)
        if unrealized_languages.__len__() > 0:
            return str.format(
                '<img src="/static/admin/img/icon-no.gif" alt="False"><b>{0}:</b></span><br/>{1}',
                _('Unrealized languages'), languages__str)
        return str.format(
            '<img src="/static/admin/img/icon-yes.gif" alt="True"><span style="margin-left:3px;">{0}</span>',
            _('OK'))

    check_language_for_text_admin_display.allow_tags = True
    check_language_for_text_admin_display.short_description = _('Texts language check')

    @property
    def name(self) -> str:
        return self.__str__()

    @property
    def check_language(self) -> bool:
        """Checks if languages of texts are corresponding to seo information languages of this page"""
        if set(self.seo_information_languages_ids) == set(self.text_languages_ids):
            return True
        return False

    @property
    def check_language_for_seo_information(self) -> bool:
        """Checks if seo information languages are corresponding to languages of the website"""
        languages = localization_models.Language.objects.all().values_list('id', flat=True)
        seo_languages = self.seo_information_languages_ids
        for language in languages:
            if language not in seo_languages:
                return False
        return True

    @property
    def check_language_for_text(self) -> bool:
        """Checks if texts languages are corresponding to languages of the website"""
        languages = localization_models.Language.objects.all().values_list('id', flat=True)
        text_languages = self.text_languages_ids
        for language in languages:
            if language not in text_languages:
                return False
        return True

    @property
    def text_languages_names(self) -> [str]:
        texts_languages = CategoryText.objects.filter(category=self).all().values_list('language__name',
                                                                                       flat=True).order_by('id')
        return texts_languages

    @property
    def text_languages_ids(self) -> [int]:
        texts_languages = CategoryText.objects.filter(category=self).all().values_list('language__id',
                                                                                       flat=True).order_by('id')
        return texts_languages

    @property
    def seo_information_languages_names(self) -> [str]:
        seo_languages = CategorySeoInformation.objects.filter(category=self).all().values_list('language__name',
                                                                                               flat=True).order_by('id')
        return seo_languages

    @property
    def seo_information_languages_ids(self) -> [str]:
        seo_languages = CategorySeoInformation.objects.filter(category=self).all().values_list('language__id',
                                                                                               flat=True).order_by('id')
        return seo_languages

    def author(self) -> auth_models.User:
        label = CategoryDateTimeUserLabel.objects.filter(category=self).first()
        return label.author

    author.short_description = _('Author')

    def last_editor(self) -> auth_models.User:
        label = CategoryDateTimeUserLabel.objects.filter(category=self).first()
        return label.last_editor

    last_editor.short_description = _('Last editor')

    def creating_date(self) -> models.DateTimeField:
        label = CategoryDateTimeUserLabel.objects.filter(category=self).first()
        return label.creating_date

    creating_date.short_description = _('Creating date')

    def last_modified_date(self) -> models.DateTimeField:
        label = CategoryDateTimeUserLabel.objects.filter(category=self).first()
        return label.last_modified_date

    last_modified_date.short_description = _('Last modified date')

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None) -> None:
        for field in self._meta.fields:
            if field.name == 'first_image':
                field.upload_to = str.format("category/{0}/first_image/", self.url)
            if field.name == 'second_image':
                field.upload_to = str.format("category/{0}/second_image/", self.url)
        super(Category, self).save()

    def delete(self, using=None):
        path = os.path.join(settings.BASE_DIR, settings.MEDIA_ROOT, str.format('catalogue/{0}', self.id))
        try:
            shutil.rmtree(path)
            super(Category, self).delete()
        except Exception:
            pass

    class Meta:
        db_table = 'catalogue_categories'
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')


class CategoryName(models.Model):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    name = models.CharField(max_length=256, verbose_name=_('Name'), help_text=_('Name'))
    language = models.ForeignKey(localization_models.Language, verbose_name=_('Language'), help_text=_('Language'),
                                 db_index=True)
    category = models.ForeignKey(Category, verbose_name=_('Category'), help_text=_('Category'))
    default = models.BooleanField(default=False, verbose_name=_('Is default?'), help_text=_('Is default?'))

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'catalogue_categories_names'
        unique_together = ('category', 'language')
        verbose_name = _('Category name')
        verbose_name_plural = _('Categories names')


class CategoryText(models.Model):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    language = models.ForeignKey(localization_models.Language, verbose_name=_('Language'), help_text=_('Language'))
    name = models.CharField(max_length=256, verbose_name=_('Name'), help_text=_('Name'))
    body = models.TextField(verbose_name=_('Body'), help_text=_('Body'))
    category = models.ForeignKey(Category, verbose_name=_('Category'), help_text=_('Category'))
    weight = models.IntegerField(blank=True, verbose_name=_('Weight'), help_text=_('Weight'))

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('name', 'category', 'language')
        db_table = 'catalogue_category_texts'
        verbose_name = _('Category Text')
        verbose_name_plural = _('Categories Texts')


class CategoryDateTimeUserLabel(models.Model):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    creating_date = models.DateTimeField(blank=True, verbose_name=_('Creating date'), help_text=_('Creating date'))
    last_modified_date = models.DateTimeField(blank=True, null=True, verbose_name=_('Last modified date'),
                                              help_text=_('Last modified date'))
    author = models.ForeignKey(auth_models.User, related_name='catalogue_category_author', blank=True,
                               verbose_name=_('Author'), help_text=_('Author'))
    last_editor = models.ForeignKey(auth_models.User, related_name='catalogue_category_last_editor', blank=True,
                                    null=True, verbose_name=_('Last edited by'), help_text=_('Last edited by'))
    category = models.OneToOneField(Category, verbose_name=_('Category'), help_text=_('Category'))

    class Meta:
        db_table = 'catalogue_datetime_user_label'
        unique_together = ('id', 'category')
        verbose_name = _('Category datetime user label')
        verbose_name_plural = _('Category datetime user labels')


class CategorySeoInformation(models.Model):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    language = models.ForeignKey(localization_models.Language, verbose_name=_('Language'), help_text=_('Language'))
    title = models.CharField(max_length=256, blank=True, null=True, verbose_name=_('Title'), help_text=_('Title'))
    meta_keywords = models.CharField(max_length=256, blank=True, null=True, verbose_name=_('Meta keywords'),
                                     help_text=_('Meta keywords'))
    meta_description = models.CharField(max_length=256, blank=True, null=True, verbose_name=_('Meta description'),
                                        help_text=_('Meta description'))
    meta_robots = models.CharField(max_length=256, blank=True, null=True, verbose_name=_('Meta robots'),
                                   help_text=_('Meta robots'))
    meta_canonical = models.CharField(max_length=256, blank=True, null=True, verbose_name=_('Meta canonical'),
                                      help_text=_('Meta canonical'))
    h1 = models.CharField(max_length=256, blank=True, null=True, verbose_name=_('H1'), help_text=_('H1'))
    category = models.ForeignKey(Category, verbose_name=_('Category'), help_text=_('Category'))

    class Meta:
        db_table = 'catalogue_category_seo_information'
        unique_together = ('language', 'category')
        verbose_name = _('Seo information')
        verbose_name_plural = _('Seo information')


# Item
class ItemTemplate(models.Model):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    name = models.CharField(max_length=256, verbose_name=_('Name'), help_text=_('Name'), unique=True)
    path = models.CharField(max_length=256, verbose_name=_('Path'), help_text=_('Path'), unique=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "catalogue_item_templates"
        verbose_name = _("Item Template")
        verbose_name_plural = _("Items Templates")


class Item(models.Model):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    default_price = models.FloatField(null=True, blank=True, verbose_name=_('Price'), help_text=_('Price'))
    currency = models.ForeignKey(localization_models.Currency, null=True, blank=True, verbose_name=_('Currency'),
                                 help_text=_('Currency'))
    default_language = models.ForeignKey(localization_models.Language, verbose_name=_('Default language'),
                                         help_text=_('Default language'))
    category = models.ForeignKey(Category, verbose_name=_('Category'), help_text=_('Category'))
    template = models.ForeignKey(ItemTemplate, verbose_name=_('Template'), help_text=_('Template'))
    active = models.BooleanField(default=True, verbose_name=_('Is active?'), help_text=_('Is active?'))
    new = models.BooleanField(default=False, verbose_name=_('Is new?'), help_text=_('This product is new?'))
    top = models.BooleanField(default=False, verbose_name=_('Is top?'), help_text=_('This product is popular?'))
    stock = models.BooleanField(default=False, verbose_name=_('Is stock?'), help_text=_('The product is in the sale?'))
    pending = models.BooleanField(default=False, verbose_name=_('Is pending?'), help_text=_('The product is pending?'))
    code = models.CharField(max_length=256, blank=True, null=True, verbose_name=_('Code'), help_text=_('Code'))
    url = models.CharField(max_length=256, db_index=True, unique=True, verbose_name=_('Url'), help_text=_('Url'))

    def delete(self, using=None):
        path = os.path.join(settings.BASE_DIR, settings.MEDIA_ROOT, str.format('catalogue/{0}/item/{1}',
                                                                               self.category.id,
                                                                               self.id))
        try:
            shutil.rmtree(path)
            super(Item, self).delete()
        except Exception:
            pass

    def __str__(self) -> str:
        lang = translation.get_language()
        language = localization_models.Language.objects.filter(short_name=lang).values_list('id', flat=True)
        if language.__len__() > 0:
            language = language[0]
            item_name = ItemName.objects.filter(item=self, language=language).values_list('name', flat=True)
            if item_name.__len__() > 0:
                return item_name[0]
        item_name = ItemName.objects.filter(item=self, default=True).values_list('name', flat=True)[0]
        return item_name

    def texts_languages_admin_display(self) -> str:
        return "<br/>".join(self.text_languages_names)

    texts_languages_admin_display.allow_tags = True
    texts_languages_admin_display.short_description = _('Languages of texts')

    def short_texts_languages_admin_display(self) -> str:
        return "<br/>".join(self.short_text_languages_names)

    short_texts_languages_admin_display.allow_tags = True
    short_texts_languages_admin_display.short_description = _('Languages of short texts')

    def seo_information_languages_admin_display(self) -> str:
        return "<br/>".join(self.seo_information_languages_names)

    seo_information_languages_admin_display.allow_tags = True
    seo_information_languages_admin_display.short_description = _('Languages of SEO information')

    def check_language_admin_display(self) -> str:
        """Checks if languages of texts are corresponding to seo information languages of this category"""
        if self.check_language:
            return str.format(
                '<img src="/static/admin/img/icon-yes.gif" alt="True"><span style="margin-left:3px;">{0}</span>',
                _('Languages of text is correspond to languages of SEO information'))
        return str.format(
            '<img src="/static/admin/img/icon-no.gif" alt="False"><span style="margin-left:3px;">{0}</span>',
            _('Languages of text does not correspond to languages of SEO information'))

    check_language_admin_display.allow_tags = True
    check_language_admin_display.short_description = _('Language check')

    def check_language_for_seo_admin_display(self) -> str:
        """Checks if seo information languages are corresponding to languages of the website"""
        unrealized_languages = localization_models.Language.objects.exclude(
            id__in=self.seo_information_languages_ids).all().values_list('name', flat=True)
        languages__str = "<br/>".join(unrealized_languages)
        if unrealized_languages.__len__() > 0:
            return str.format(
                '<img src="/static/admin/img/icon-no.gif" alt="False"><b>{0}:</b></span><br/>{1}',
                _('Unrealized languages'), languages__str)
        return str.format(
            '<img src="/static/admin/img/icon-yes.gif" alt="True"><span style="margin-left:3px;">{0}</span>',
            _('OK'))

    check_language_for_seo_admin_display.allow_tags = True
    check_language_for_seo_admin_display.short_description = _('Seo language check')

    def check_language_for_text_admin_display(self) -> str:
        """Checks if texts languages are corresponding to languages of the website"""
        unrealized_languages = localization_models.Language.objects.exclude(
            id__in=self.text_languages_ids).all().values_list('name', flat=True)
        languages__str = "<br/>".join(unrealized_languages)
        if unrealized_languages.__len__() > 0:
            return str.format(
                '<img src="/static/admin/img/icon-no.gif" alt="False"><b>{0}:</b></span><br/>{1}',
                _('Unrealized languages'), languages__str)
        return str.format(
            '<img src="/static/admin/img/icon-yes.gif" alt="True"><span style="margin-left:3px;">{0}</span>',
            _('OK'))

    check_language_for_text_admin_display.allow_tags = True
    check_language_for_text_admin_display.short_description = _('Texts language check')

    def check_language_for_short_text_admin_display(self) -> str:
        """Checks if texts languages are corresponding to languages of the website"""
        unrealized_languages = localization_models.Language.objects.exclude(
            id__in=self.short_text_languages_ids).all().values_list('name', flat=True)
        languages__str = "<br/>".join(unrealized_languages)
        if unrealized_languages.__len__() > 0:
            return str.format(
                '<img src="/static/admin/img/icon-no.gif" alt="False"><b>{0}:</b></span><br/>{1}',
                _('Unrealized languages'), languages__str)
        return str.format(
            '<img src="/static/admin/img/icon-yes.gif" alt="True"><span style="margin-left:3px;">{0}</span>',
            _('OK'))

    check_language_for_short_text_admin_display.allow_tags = True
    check_language_for_short_text_admin_display.short_description = _('Shrot texts language check')

    @property
    def name(self):
        return self.__str__()

    @property
    def short_text(self) -> str:
        lang = translation.get_language()
        language = localization_models.Language.objects.filter(short_name=lang).values_list('id', flat=True)
        if language.__len__() > 0:
            language = language[0]
            item_short_text = ItemShortText.objects.filter(item=self, language=language).values_list('body', flat=True)
            if item_short_text.__len__() > 0:
                return item_short_text[0]
        return None

    def price(self, currency: localization_models.Currency) -> float:
        if currency is None:
            return None
        if self.price is not None:
            return self.default_price * self.currency.coefficient / currency.coefficient
        return None

    @property
    def image(self):
        return ItemImagePosition.objects.filter(item=self, default=True).first()

    @property
    def check_language(self) -> bool:
        """Checks if languages of texts are corresponding to seo information languages of this page"""
        if set(self.seo_information_languages_ids) == set(self.text_languages_ids):
            return True
        return False

    @property
    def check_language_for_seo_information(self) -> bool:
        """Checks if seo information languages are corresponding to languages of the website"""
        languages = localization_models.Language.objects.all().values_list('id', flat=True)
        seo_languages = self.seo_information_languages_ids
        for language in languages:
            if language not in seo_languages:
                return False
        return True

    @property
    def check_language_for_text(self) -> bool:
        """Checks if texts languages are corresponding to languages of the website"""
        languages = localization_models.Language.objects.all().values_list('id', flat=True)
        text_languages = self.text_languages_ids
        for language in languages:
            if language not in text_languages:
                return False
        return True

    @property
    def text_languages_names(self) -> [str]:
        texts_languages = ItemText.objects.filter(item=self).all().values_list('language__name',
                                                                               flat=True).order_by('id')
        return texts_languages

    @property
    def text_languages_ids(self) -> [int]:
        texts_languages = ItemText.objects.filter(item=self).all().values_list('language__id',
                                                                               flat=True).order_by('id')
        return texts_languages

    @property
    def short_text_languages_names(self) -> [int]:
        texts_languages = ItemShortText.objects.filter(item=self).all().values_list('language__name',
                                                                                    flat=True).order_by('id')
        return texts_languages

    @property
    def short_text_languages_ids(self) -> [int]:
        texts_languages = ItemShortText.objects.filter(item=self).all().values_list('language__id',
                                                                                    flat=True).order_by('id')
        return texts_languages

    @property
    def seo_information_languages_names(self) -> [str]:
        seo_languages = ItemSeoInformation.objects.filter(item=self).all().values_list('language__name',
                                                                                       flat=True).order_by('id')
        return seo_languages

    @property
    def seo_information_languages_ids(self) -> [str]:
        seo_languages = ItemSeoInformation.objects.filter(item=self).all().values_list('language__id',
                                                                                       flat=True).order_by('id')
        return seo_languages

    def author(self) -> auth_models.User:
        label = ItemDateTimeUserLabel.objects.filter(item=self).first()
        return label.author

    author.short_description = _('Author')

    def last_editor(self) -> auth_models.User:
        label = ItemDateTimeUserLabel.objects.filter(item=self).first()
        return label.last_editor

    last_editor.short_description = _('Last editor')

    def creating_date(self) -> models.DateTimeField:
        label = ItemDateTimeUserLabel.objects.filter(item=self).first()
        return label.creating_date

    creating_date.short_description = _('Creating date')

    def last_modified_date(self) -> models.DateTimeField:
        label = ItemDateTimeUserLabel.objects.filter(item=self).first()
        return label.last_modified_date

    last_modified_date.short_description = _('Last modified date')

    class Meta:
        db_table = "catalogue_items"
        verbose_name = _("Item")
        verbose_name_plural = _("Items")


class ItemName(models.Model):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    name = models.CharField(max_length=256, unique=True, verbose_name=_('Name'), help_text=_('Name'))
    language = models.ForeignKey(localization_models.Language, verbose_name=_('Language'), help_text=_('Language'),
                                 db_index=True)
    item = models.ForeignKey(Item, verbose_name=_('Item'), help_text=_('Item'))
    default = models.BooleanField(default=False, verbose_name=_('Is default?'), help_text=_('Is default?'))

    class Meta:
        db_table = 'catalogue_item_names'
        unique_together = ('item', 'language')
        verbose_name = _('Item name')
        verbose_name_plural = _('Items names')


class ItemText(models.Model):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    language = models.ForeignKey(localization_models.Language, verbose_name=_('Language'), help_text=_('Language'))
    name = models.CharField(max_length=256, verbose_name=_('Name'), help_text=_('Name'))
    body = models.TextField(verbose_name=_('Body'), help_text=_('Body'))
    item = models.ForeignKey(Item, verbose_name=_('Item'), help_text=_('Item'))
    weight = models.IntegerField(blank=True, verbose_name=_('Weight'), help_text=_('Weight'))

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('name', 'item', 'language')
        db_table = 'catalogue_item_texts'
        verbose_name = _('Item Text')
        verbose_name_plural = _('Items Texts')


class ItemShortText(models.Model):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    language = models.ForeignKey(localization_models.Language, verbose_name=_('Language'), help_text=_('Language'))
    body = models.TextField(verbose_name=_('Body'), help_text=_('Body'))
    item = models.ForeignKey(Item, verbose_name=_('Item'), help_text=_('Item'))

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('item', 'language')
        db_table = 'catalogue_item_short_texts'
        verbose_name = _('Item Short Text')
        verbose_name_plural = _('Items  Short Texts')


class ItemDateTimeUserLabel(models.Model):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    creating_date = models.DateTimeField(blank=True, verbose_name=_('Creating date'), help_text=_('Creating date'))
    last_modified_date = models.DateTimeField(blank=True, null=True, verbose_name=_('Last modified date'),
                                              help_text=_('Last modified date'))
    author = models.ForeignKey(auth_models.User, related_name='catalogue_item_author', blank=True,
                               verbose_name=_('Author'), help_text=_('Author'))
    last_editor = models.ForeignKey(auth_models.User, related_name='catalogue_item_last_editor', blank=True, null=True,
                                    verbose_name=_('Last edited by'), help_text=_('Last edited by'))
    item = models.OneToOneField(Item, verbose_name=_('Item'), help_text=_('Item'))

    class Meta:
        db_table = 'catalogue_item_datetime_user_label'
        unique_together = ('id', 'item')
        verbose_name = _('Item datetime user label')
        verbose_name_plural = _('Item datetime user labels')


class ItemSeoInformation(models.Model):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    language = models.ForeignKey(localization_models.Language, verbose_name=_('Language'), help_text=_('Language'))
    title = models.CharField(max_length=256, blank=True, null=True, verbose_name=_('Title'), help_text=_('Title'))
    meta_keywords = models.CharField(max_length=256, blank=True, null=True, verbose_name=_('Meta keywords'),
                                     help_text=_('Meta keywords'))
    meta_description = models.CharField(max_length=256, blank=True, null=True, verbose_name=_('Meta description'),
                                        help_text=_('Meta description'))
    meta_robots = models.CharField(max_length=256, blank=True, null=True, verbose_name=_('Meta robots'),
                                   help_text=_('Meta robots'))
    meta_canonical = models.CharField(max_length=256, blank=True, null=True, verbose_name=_('Meta canonical'),
                                      help_text=_('Meta canonical'))
    h1 = models.CharField(max_length=256, blank=True, null=True, verbose_name=_('H1'), help_text=_('H1'))
    item = models.ForeignKey(Item, verbose_name=_('Item'), help_text=_('Item'))

    class Meta:
        db_table = 'catalogue_item_seo_information'
        unique_together = ('language', 'item')
        verbose_name = _('Seo information')
        verbose_name_plural = _('Seo information')


class ItemImagePosition(models.Model):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    image_original = models.ImageField(verbose_name=_('Original image'), help_text=_('Original Image'))
    cropping_large = ImageRatioField('image_original', settings.CATALOGUE_ITEM_GALLERY['large'],
                                     verbose_name=_('Large image'),
                                     help_text=_('Large image'))
    cropping_medium = ImageRatioField('image_original', settings.CATALOGUE_ITEM_GALLERY['medium'],
                                      verbose_name=_('Medium image'),
                                      help_text=_('Medium image'))
    cropping_small = ImageRatioField('image_original', settings.CATALOGUE_ITEM_GALLERY['small'],
                                     verbose_name=_('Small image'),
                                     help_text=_('Small image'))
    weight = models.IntegerField(blank=True, verbose_name=_('Weight'), help_text=_('Weight'))
    active = models.BooleanField(default=True, verbose_name=_('Is active?'), help_text=_('Is active?'))

    default = models.BooleanField(default=False, verbose_name=_('Is default?'), help_text=_('Is active?'))

    item = models.ForeignKey(Item, verbose_name=_('Item'))

    image_large = models.CharField(max_length=256, null=True, blank=True, editable=False)
    image_medium = models.CharField(max_length=256, null=True, blank=True, editable=False)
    image_small = models.CharField(max_length=256, null=True, blank=True, editable=False)

    @property
    def original_image(self) -> str:
        return str.format("/media/{0}", self.image_original)

    @property
    def large_image(self) -> str:
        url = get_thumbnailer(self.image_original).get_thumbnail({
            'size': (settings.CATALOGUE_ITEM_GALLERY['large'][:settings.CATALOGUE_ITEM_GALLERY['large'].index('x')],
                     settings.CATALOGUE_ITEM_GALLERY['large'][
                     settings.CATALOGUE_ITEM_GALLERY['large'].index('x') + 1:]),
            'box': self.cropping_large,
            'crop': True,
            'detail': True,
        }).url
        return url

    @property
    def medium_image(self) -> str:
        url = get_thumbnailer(self.image_original).get_thumbnail({
            'size': (settings.CATALOGUE_ITEM_GALLERY['medium'][:settings.CATALOGUE_ITEM_GALLERY['medium'].index('x')],
                     settings.CATALOGUE_ITEM_GALLERY['medium'][
                     settings.CATALOGUE_ITEM_GALLERY['medium'].index('x') + 1:]),
            'box': self.cropping_small,
            'crop': True,
            'detail': True,
        }).url
        return url

    @property
    def small_image(self) -> str:
        url = get_thumbnailer(self.image_original).get_thumbnail({
            'size': (settings.CATALOGUE_ITEM_GALLERY['small'][:settings.CATALOGUE_ITEM_GALLERY['small'].index('x')],
                     settings.CATALOGUE_ITEM_GALLERY['small'][
                     settings.CATALOGUE_ITEM_GALLERY['small'].index('x') + 1:]),
            'box': self.cropping_medium,
            'crop': True,
            'detail': True,
        }).url
        return url

    @property
    def original_image(self) -> str:
        return str.format("/media/{0}", self.image_original)

    @property
    def large_image_path(self) -> str:
        return self.image_large

    @property
    def medium_image_path(self) -> str:
        return self.image_medium

    @property
    def small_image_path(self) -> str:
        return self.image_small

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        for field in self._meta.fields:
            if field.name == 'image_original':
                field.upload_to = str.format('catalogue/{0}/item/{1}/images/{2}/', self.item.category.id, self.item.id,
                                             self.image_original.__str__()[0:self.image_original.__str__().index('.')])
        super(ItemImagePosition, self).save()
        self.image_large = self.large_image
        self.image_medium = self.medium_image
        self.image_small = self.small_image

        super(ItemImagePosition, self).save()

    def delete(self, using=None):
        path = os.path.join(settings.BASE_DIR,
                            settings.MEDIA_ROOT,
                            self.image_original.__str__()[0:self.image_original.__str__().rfind('/')])
        try:
            super(ItemImagePosition, self).delete()
            shutil.rmtree(path)
        except Exception as e:
            pass

    def name(self) -> str:
        return self.__str__()

    name.short_description = _('Name')

    def original_image_admin_display(self) -> str:
        return str.format('<img src="/media/{0}" style="width:10em" alt="Original Image: {0}"/>', self.image_original)

    original_image_admin_display.allow_tags = True
    original_image_admin_display.short_description = _('Original image')

    def large_image_admin_display(self) -> str:
        url = get_thumbnailer(self.image_original).get_thumbnail({
            'size': (settings.CATALOGUE_ITEM_GALLERY['large'][:settings.CATALOGUE_ITEM_GALLERY['large'].index('x')],
                     settings.CATALOGUE_ITEM_GALLERY['large'][
                     settings.CATALOGUE_ITEM_GALLERY['large'].index('x') + 1:]),
            'box': self.cropping_large,
            'crop': True,
            'detail': True,
        }).url
        return str.format('<img src={0} style="width:10em" alt="Large Image: {1}"/>', url, self.image_original)

    large_image_admin_display.allow_tags = True
    large_image_admin_display.short_description = _('Large image')

    def medium_image_admin_display(self) -> str:
        url = get_thumbnailer(self.image_original).get_thumbnail({
            'size': (settings.CATALOGUE_ITEM_GALLERY['medium'][:settings.CATALOGUE_ITEM_GALLERY['medium'].index('x')],
                     settings.CATALOGUE_ITEM_GALLERY['medium'][
                     settings.CATALOGUE_ITEM_GALLERY['medium'].index('x') + 1:]),
            'box': self.cropping_medium,
            'crop': True,
            'detail': True,
        }).url
        return str.format('<img src={0} style="width:10em" alt="Medium Image: {1}"/>', url, self.image_original)

    medium_image_admin_display.allow_tags = True
    medium_image_admin_display.short_description = _('Medium image')

    def small_image_admin_display(self) -> str:
        url = get_thumbnailer(self.image_original).get_thumbnail({
            'size': (settings.CATALOGUE_ITEM_GALLERY['small'][:settings.CATALOGUE_ITEM_GALLERY['small'].index('x')],
                     settings.CATALOGUE_ITEM_GALLERY['small'][
                     settings.CATALOGUE_ITEM_GALLERY['small'].index('x') + 1:]),
            'box': self.cropping_small,
            'crop': True,
            'detail': True,
        }).url
        return str.format('<img src={0} style="width:10em" alt="Small Image: {1}"/>', url, self.image_original)

    small_image_admin_display.allow_tags = True
    small_image_admin_display.short_description = _('Small image')

    def __str__(self) -> str:
        return self.id.__str__()

    class Meta:
        db_table = 'catalogue_item_image_positions'
        verbose_name = _('Catalogue item position')
        verbose_name_plural = _('Catalogue image positions')


class ItemParameter(models.Model):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    first_image = models.ImageField(null=True, blank=True, verbose_name=_('First image'), help_text=_('First image'))
    second_image = models.ImageField(null=True, blank=True, verbose_name=_('Second image'), help_text=_('Second image'))
    item = models.ForeignKey(Item)
    default_name = models.CharField(max_length=256)
    default_value = models.CharField(max_length=256)
    weight = models.IntegerField(blank=True)

    def __str__(self) -> str:
        lang = translation.get_language()
        language = localization_models.Language.objects.filter(short_name=lang).values_list('id', flat=True)
        if language.__len__() > 0:
            language = language[0]
            item_name = ItemParameterName.objects.filter(item_parameter=self,
                                                         language=language).values_list('name', flat=True)
            if item_name.__len__() > 0:
                return item_name[0]
        return self.default_name

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None) -> None:
        for field in self._meta.fields:
            if field.name == 'first_image':

                field.upload_to = str.format("catalogue/{0}/item/{1}/parameter/{2}/first_image",
                                             self.item.category.id, self.item.id, self.default_name)
            if field.name == 'second_image':
                field.upload_to = str.format("catalogue/{0}/item/{1}/parameter/{2}/first_image",
                                             self.item.category.id, self.item.id, self.default_name)
        super(ItemParameter, self).save()

    def delete(self, using=None):
        path = os.path.join(settings.BASE_DIR,
                            settings.MEDIA_ROOT,
                            str.format('catalogue/{0}/item/{1}/parameter/{2}',
                                       self.item.category.id, self.item.id, self.default_name))
        try:
            super(ItemParameter, self).delete()
            shutil.rmtree(path)
        except Exception as e:
            pass

    @property
    def name(self):
        return self.__str__()

    class Meta:
        db_table = 'catalogue_item_parameters'
        unique_together = ('default_name', 'item')
        verbose_name = _('Item Parameter')
        verbose_name_plural = _('Items Parameters')


class ItemParameterName(models.Model):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    name = models.CharField(max_length=256)
    value = models.CharField(max_length=256)
    language = models.ForeignKey(localization_models.Language)
    item_parameter = models.ForeignKey(ItemParameter)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'catalogue_item_parameters_names'
        unique_together = ('language', 'item_parameter')
        verbose_name = _('Item Parameter Name')
        verbose_name_plural = _('Items Parameters Names')
