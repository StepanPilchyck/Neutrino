from django.db import models
from django.contrib.auth import models as auth_models
from django.utils.translation import ugettext_lazy as _
import django.utils.translation as translation
import localization.models as localization_models
import os
import neutrino.settings as settings
import shutil


class BannerImagePosition(models.Model):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    image_original = models.ImageField(verbose_name=_('Original image'), help_text=_('Original image'))
    image_large = models.ImageField(blank=True, null=True, verbose_name=_('Large image'), help_text=_('Large image'))
    image_medium = models.ImageField(blank=True, null=True, verbose_name=_('Medium image'), help_text=_('Medium image'))
    image_small = models.ImageField(blank=True, null=True, verbose_name=_('Small image'), help_text=_('Small image'))
    weight = models.IntegerField(blank=True, verbose_name=_('Weight'), help_text=_('Used for sorting'))
    active = models.BooleanField(default=True, verbose_name=_('Is active?'),
                                 help_text=_('If checked image will be used in banner render'))
    banner = models.ForeignKey('Banner', verbose_name=_('Banner'), help_text=_('Banner, that contains this image'))

    def __str__(self) -> str:
        lang = translation.get_language()
        language = localization_models.Language.objects.filter(short_name=lang).values_list('id', flat=True)
        if language.__len__() > 0:
            language = language[0]
            banner_image_position_text_data = BannerImagePositionTextData.objects.filter(banner_image_position=self,
                                                                                         language=language).first()
            if banner_image_position_text_data is not None:
                return banner_image_position_text_data.name
        banner_image_position_text_data = BannerImagePositionTextData.objects.filter(banner_image_position=self,
                                                                                     default=True).first()
        if banner_image_position_text_data is None:
            return _('Image has no name').__str__()
        return banner_image_position_text_data.name

    @property
    def original_image(self) -> str:
        return str.format("/media/{0}", self.image_original)

    @property
    def large_image(self) -> str:
        return str.format("/media/{0}", self.image_large)

    @property
    def medium_image(self) -> str:
        return str.format("/media/{0}", self.image_medium)

    @property
    def small_image(self) -> str:
        return str.format("/media/{0}", self.image_small)

    @property
    def check_language_for_name(self) -> bool:
        """Checks if languages of text data are corresponding to languages of the website"""
        languages = localization_models.Language.objects.all().values_list('id', flat=True)
        for language in languages:
            if language not in self.text_data_languages_ids:
                return False
        return True

    @property
    def text_data_languages_names(self) -> [str]:
        return BannerImagePositionTextData.objects.filter(banner_image_position=self).all().values_list(
            'language__name', flat=True)

    @property
    def text_data_languages_ids(self) -> [int]:
        return BannerImagePositionTextData.objects.filter(banner_image_position=self).all().values_list(
            'language__id', flat=True)

    def name(self) -> str:
        return self.__str__()

    def description(self) -> str:
        lang = translation.get_language()
        language = localization_models.Language.objects.filter(short_name=lang).values_list('id', flat=True)
        if language.__len__() > 0:
            language = language[0]
            banner_image_position_text_data = BannerImagePositionTextData.objects.filter(banner_image_position=self,
                                                                                         language=language).first()
            if banner_image_position_text_data is not None:
                return banner_image_position_text_data.description
        banner_image_position_text_data = BannerImagePositionTextData.objects.filter(banner_image_position=self,
                                                                                     default=True).first()
        if banner_image_position_text_data is None:
            return _('Image has no name').__str__()
        return banner_image_position_text_data.description

    name.short_description = _('Name')

    def original_image_admin_display(self) -> str:
        return str.format('<img src="/media/{0}" style="width:10em" alt="Original Image: {0}"/>', self.image_original)

    original_image_admin_display.allow_tags = True
    original_image_admin_display.short_description = _('Original image')

    def large_image_admin_display(self) -> str:
        return str.format('<img src="/media/{0}" style="width:10em" alt="Large Image: {0}"/>', self.image_large)

    large_image_admin_display.allow_tags = True
    large_image_admin_display.short_description = _('Large image')

    def medium_image_admin_display(self) -> str:
        return str.format('<img src="/media/{0}" style="width:10em" alt="Medium Image: {0}"/>', self.image_medium)

    medium_image_admin_display.allow_tags = True
    medium_image_admin_display.short_description = _('Medium image')

    def small_image_admin_display(self) -> str:
        return str.format('<img src="/media/{0}" style="width:10em" alt="Small Image: {0}"/>', self.image_small)

    small_image_admin_display.allow_tags = True
    small_image_admin_display.short_description = _('Small image')

    def check_language_for_text_data_admin_display(self) -> str:
        """Checks if languages of text data are corresponding to languages of the website"""
        unrealized_languages = localization_models.Language.objects.exclude(
            id__in=self.text_data_languages_ids).all().values_list('name', flat=True)
        languages__str = "<br/>".join(unrealized_languages)
        if unrealized_languages.__len__() > 0:
            return str.format(
                '<img src="/static/admin/img/icon-no.gif" alt="False"><b>{0}:</b></span><br/>{1}',
                _('Unrealized languages'), languages__str)
        return str.format(
            '<img src="/static/admin/img/icon-yes.gif" alt="True"><span style="margin-left:3px;">{0}</span>',
            _('OK'))

    check_language_for_text_data_admin_display.allow_tags = True
    check_language_for_text_data_admin_display.short_description = _('Text data language check')

    def save(self, force_insert: bool = False, force_update: bool = False, using=None,
             update_fields=None) -> None:
        for field in self._meta.fields:
            if field.name == 'image_original':
                field.upload_to = str.format('banner/{0}/images/{1}/original/', self.banner.id,
                                             self.image_original.__str__()[0:self.image_original.__str__().index('.')])
            elif field.name == 'image_large':
                field.upload_to = str.format('banner/{0}/images/{1}/large/', self.banner.id,
                                             self.image_original.__str__()[0:self.image_original.__str__().index('.')])
            elif field.name == 'image_medium':
                field.upload_to = str.format('banner/{0}/images/{1}/medium/', self.banner.id,
                                             self.image_original.__str__()[0:self.image_original.__str__().index('.')])
            elif field.name == 'image_small':
                field.upload_to = str.format('banner/{0}/images/{1}/small/', self.banner.id,
                                             self.image_original.__str__()[0:self.image_original.__str__().index('.')])
        super(BannerImagePosition, self).save()

    def delete(self, using=None):
        path = os.path.join(settings.BASE_DIR, settings.MEDIA_ROOT,
                            self.image_original.__str__()[0:self.image_original.__str__().rfind('/original')])
        try:
            shutil.rmtree(path)
            super(BannerImagePosition, self).delete()
        except Exception:
            pass

    class Meta:
        db_table = 'banner_banner_image_positions'
        verbose_name = _('Banner image position')
        verbose_name_plural = _('Banner image positions')


class Banner(models.Model):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    marker = models.CharField(max_length=256, verbose_name=_('Marker'), help_text=_('Marker'))

    def __str__(self) -> str:
        lang = translation.get_language()
        language = localization_models.Language.objects.filter(short_name=lang).values_list('id', flat=True)
        if language.__len__() > 0:
            language = language[0]
            banner_text_data = BannerTextData.objects.filter(banner=self, language=language).first()
            if banner_text_data is not None:
                return banner_text_data.name
        banner_text_data = BannerTextData.objects.filter(banner=self, default=True).first()
        return banner_text_data.name

    def delete(self, using=None):
        path = os.path.join(settings.BASE_DIR, settings.MEDIA_ROOT, str.format('banner/{0}', self.id))
        try:
            shutil.rmtree(path)
            super(Banner, self).delete()
        except Exception:
            pass

    def name(self) -> str:
        return self.__str__()

    name.short_description = _('Name')

    def author(self) -> auth_models.User:
        label = BannerDateTimeUserLabel.objects.filter(banner=self).first()
        return label.author

    author.short_description = _('Author')

    def last_editor(self) -> auth_models.User:
        label = BannerDateTimeUserLabel.objects.filter(banner=self).first()
        return label.last_editor

    last_editor.short_description = _('Last edited by')

    def creating_date(self) -> models.DateTimeField:
        label = BannerDateTimeUserLabel.objects.filter(banner=self).first()
        return label.creating_date

    creating_date.short_description = _('Creating date')

    def last_modified_date(self) -> models.DateTimeField:
        label = BannerDateTimeUserLabel.objects.filter(banner=self).first()
        return label.last_modified_date

    last_modified_date.short_description = _('Last modified date')

    def check_language_for_text_data_admin_display(self) -> str:
        """Checks if languages of text data are corresponding to languages of the website"""
        unrealized_languages = localization_models.Language.objects.exclude(
            id__in=self.text_data_languages_ids).all().values_list('name', flat=True)
        languages__str = "<br/>".join(unrealized_languages)
        if unrealized_languages.__len__() > 0:
            return str.format(
                '<img src="/static/admin/img/icon-no.gif" alt="False"><b>{0}:</b></span><br/>{1}',
                _('Unrealized languages'), languages__str)
        return str.format(
            '<img src="/static/admin/img/icon-yes.gif" alt="True"><span style="margin-left:3px;">{0}</span>',
            _('OK'))

    check_language_for_text_data_admin_display.allow_tags = True
    check_language_for_text_data_admin_display.short_description = _('Text data language check')

    @property
    def check_language_for_text_data(self) -> bool:
        """Checks if languages of text data are corresponding to languages of the website"""
        languages = localization_models.Language.objects.all().values_list('id', flat=True)
        text_languages = self.text_data_languages_ids
        for language in languages:
            if language not in text_languages:
                return False
        return True

    @property
    def text_data_languages_names(self) -> [str]:
        return BannerTextData.objects.filter(banner=self).all().values_list(
            'language__name', flat=True)

    @property
    def text_data_languages_ids(self) -> [int]:
        return BannerTextData.objects.filter(banner=self).all().values_list(
            'language__id', flat=True)

    class Meta:
        db_table = 'banner_banners'
        verbose_name = _('Banner')
        verbose_name_plural = _('Banners')


class BannerDateTimeUserLabel(models.Model):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    creating_date = models.DateTimeField(blank=True, verbose_name=_('Creating date'), help_text=_('Date of creating'))
    last_modified_date = models.DateTimeField(blank=True, null=True, verbose_name=_('Last modified date'),
                                              help_text=_('date of last modification'))
    author = models.ForeignKey(auth_models.User, related_name='banner_author', blank=True, verbose_name=_('Author'),
                               help_text=_('Author'))
    last_editor = models.ForeignKey(auth_models.User, related_name='banner_last_editor', blank=True, null=True,
                                    verbose_name=_('Last edited by'), help_text=_('Last editor'))
    banner = models.OneToOneField(Banner, verbose_name=_('Banner'), help_text=_('Banner'))

    class Meta:
        db_table = 'banner_datetime_user_label'
        unique_together = ('id', 'banner')
        verbose_name = _('Banner datetime user label')
        verbose_name_plural = _('Banners datetime user labels')


class BannerImagePositionTextData(models.Model):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    language = models.ForeignKey(localization_models.Language, verbose_name=_('Language'), help_text=_('Language'))
    name = models.CharField(max_length=256, blank=True, verbose_name=_('Name'), help_text=_('Name'))
    description = models.CharField(max_length=256, null=True, blank=True, verbose_name=_('Description'),
                                   help_text=_('Description'))
    banner_image_position = models.ForeignKey(BannerImagePosition, verbose_name=_('Banner image position'),
                                              help_text=_('Banner image position'))
    default = models.BooleanField(default=False, verbose_name=_('Is default?'),
                                  help_text=_('Is this metadata used by default?'))

    class Meta:
        db_table = 'banner_banner_image_position_text_data'
        unique_together = ('language', 'banner_image_position')
        verbose_name = _('Banner image position metadata')
        verbose_name_plural = _('Banners image positions metadata')


class BannerTextData(models.Model):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    language = models.ForeignKey(localization_models.Language, verbose_name=_('Language'), help_text=_('Language'))
    name = models.CharField(max_length=256, blank=True, verbose_name=_('Name'), help_text=_('Name'))
    description = models.CharField(max_length=256, null=True, blank=True, verbose_name=_('Description'),
                                   help_text=_('Description'))
    banner = models.ForeignKey(Banner, verbose_name=_('Banner'), help_text=_('Banner'))
    default = models.BooleanField(default=False, verbose_name=_('Is default?'),
                                  help_text=_('Is this metadata used by default?'))

    class Meta:
        db_table = 'banner_banner_text_data'
        unique_together = ('language', 'banner')
        verbose_name = _('Banner metadata')
        verbose_name_plural = _('Banners metadata')
