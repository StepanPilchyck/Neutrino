from django.db import models
from django.contrib.auth import models as auth_models
from django.utils.translation import ugettext_lazy as _
import localization.models as localization_models
from image_cropping import ImageRatioField
from easy_thumbnails.files import get_thumbnailer
# Config variables
import django.utils.translation as translation
import os
import neutrino.settings as settings
import shutil


class GalleryImagePosition(models.Model):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    image_original = models.ImageField(verbose_name=_('Original image'), help_text=_('Original Image'))
    cropping_large = ImageRatioField('image_original', settings.GALLERY['large'], verbose_name=_('Large image'),
                                     help_text=_('Large image'))
    cropping_medium = ImageRatioField('image_original', settings.GALLERY['medium'], verbose_name=_('Medium image'),
                                      help_text=_('Medium image'))
    cropping_small = ImageRatioField('image_original', settings.GALLERY['small'], verbose_name=_('Small image'),
                                     help_text=_('Small image'))
    weight = models.IntegerField(blank=True, verbose_name=_('Weight'), help_text=_('Weight'))
    active = models.BooleanField(default=True, verbose_name=_('Is active?'), help_text=_('Is active?'))

    gallery = models.ForeignKey('Gallery', verbose_name=_('Gallery'))

    image_large = models.CharField(max_length=256, null=True, blank=True, editable=False)
    image_medium = models.CharField(max_length=256, null=True, blank=True, editable=False)
    image_small = models.CharField(max_length=256, null=True, blank=True, editable=False)

    @property
    def original_image(self) -> str:
        return str.format("/media/{0}", self.image_original)

    @property
    def large_image(self) -> str:
        url = get_thumbnailer(self.image_original).get_thumbnail({
            'size': (settings.GALLERY['large'][:settings.GALLERY['large'].index('x')],
                     settings.GALLERY['large'][settings.GALLERY['large'].index('x') + 1:]),
            'box': self.cropping_large,
            'crop': True,
            'detail': True,
        }).url
        return url

    @property
    def medium_image(self) -> str:
        url = get_thumbnailer(self.image_original).get_thumbnail({
            'size': (settings.GALLERY['medium'][:settings.GALLERY['medium'].index('x')],
                     settings.GALLERY['medium'][settings.GALLERY['medium'].index('x') + 1:]),
            'box': self.cropping_small,
            'crop': True,
            'detail': True,
        }).url
        return url

    @property
    def small_image(self) -> str:
        url = get_thumbnailer(self.image_original).get_thumbnail({
            'size': (settings.GALLERY['small'][:settings.GALLERY['small'].index('x')],
                     settings.GALLERY['small'][settings.GALLERY['small'].index('x') + 1:]),
            'box': self.cropping_medium,
            'crop': True,
            'detail': True,
        }).url
        return url

    @property
    def large_image_path(self) -> str:
        return self.image_large

    @property
    def medium_image_path(self) -> str:
        return self.image_medium

    @property
    def small_image_path(self) -> str:
        return self.image_small

    @property
    def check_language_for_text_data(self) -> bool:
        """Checks if languages of text data are corresponding to languages of the website"""
        languages = localization_models.Language.objects.all().values_list('id', flat=True)
        for language in languages:
            if language not in self.text_data_languages_ids:
                return False
        return True

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None) -> None:
        for field in self._meta.fields:
            if field.name == 'image_original':
                field.upload_to = str.format('gallery/{0}/images/{1}/', self.gallery.marker,
                                             self.image_original.__str__()[0:self.image_original.__str__().index('.')])
        super(GalleryImagePosition, self).save()
        self.image_large = self.large_image
        self.image_medium = self.medium_image
        self.image_small = self.small_image

        super(GalleryImagePosition, self).save()

    def delete(self, using=None):
        path = os.path.join(settings.BASE_DIR,
                            settings.MEDIA_ROOT,
                            self.image_original.__str__()[0:self.image_original.__str__().rfind('/')])
        try:
            shutil.rmtree(path)
            super(GalleryImagePosition, self).delete()
        except Exception as e:
            pass

    def __str__(self) -> str:
        lang = translation.get_language()
        language = localization_models.Language.objects.filter(short_name=lang).values_list('id', flat=True)
        if language.__len__() > 0:
            language = language[0]
            gallery_image_position_text_data = GalleryImagePositionTextData.objects.filter(gallery_image_position=self,
                                                                                           language=language).first()
            if gallery_image_position_text_data is not None:
                return gallery_image_position_text_data.name
        gallery_image_position_text_data = GalleryImagePositionTextData.objects.filter(gallery_image_position=self,
                                                                                       default=True).first()
        if gallery_image_position_text_data is None:
            return _('Image has no name').__str__()
        return gallery_image_position_text_data.name

    def name(self) -> str:
        return self.__str__()

    @property
    def description(self) -> str:
        lang = translation.get_language()
        language = localization_models.Language.objects.filter(short_name=lang).values_list('id', flat=True)
        if language.__len__() > 0:
            language = language[0]
            gallery_image_position_text_data = GalleryImagePositionTextData.objects.filter(gallery_image_position=self,
                                                                                           language=language).first()
            if gallery_image_position_text_data is not None:
                return gallery_image_position_text_data.description
        gallery_image_position_text_data = GalleryImagePositionTextData.objects.filter(gallery_image_position=self,
                                                                                       default=True).first()
        if gallery_image_position_text_data is None:
            return _('Image has no description').__str__()
        return gallery_image_position_text_data.description

    name.short_description = _('Name')

    def original_image_admin_display(self) -> str:
        return str.format('<img src="/media/{0}" style="width:10em" alt="Original Image: {0}"/>', self.image_original)

    original_image_admin_display.allow_tags = True
    original_image_admin_display.short_description = _('Original image')

    def large_image_admin_display(self) -> str:
        url = get_thumbnailer(self.image_original).get_thumbnail({
            'size': (settings.GALLERY['large'][:settings.GALLERY['large'].index('x')],
                     settings.GALLERY['large'][settings.GALLERY['large'].index('x') + 1:]),
            'box': self.cropping_large,
            'crop': True,
            'detail': True,
        }).url
        return str.format('<img src={0} style="width:10em" alt="Large Image: {1}"/>', url, self.image_original)

    large_image_admin_display.allow_tags = True
    large_image_admin_display.short_description = _('Large image')

    def medium_image_admin_display(self) -> str:
        url = get_thumbnailer(self.image_original).get_thumbnail({
            'size': (settings.GALLERY['medium'][:settings.GALLERY['medium'].index('x')],
                     settings.GALLERY['medium'][settings.GALLERY['medium'].index('x') + 1:]),
            'box': self.cropping_medium,
            'crop': True,
            'detail': True,
        }).url
        return str.format('<img src={0} style="width:10em" alt="Medium Image: {1}"/>', url, self.image_original)

    medium_image_admin_display.allow_tags = True
    medium_image_admin_display.short_description = _('Medium image')

    def small_image_admin_display(self) -> str:
        url = get_thumbnailer(self.image_original).get_thumbnail({
            'size': (settings.GALLERY['small'][:settings.GALLERY['small'].index('x')],
                     settings.GALLERY['small'][settings.GALLERY['small'].index('x') + 1:]),
            'box': self.cropping_small,
            'crop': True,
            'detail': True,
        }).url
        return str.format('<img src={0} style="width:10em" alt="Small Image: {1}"/>', url, self.image_original)

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

    @property
    def check_language_for_text_data(self) -> bool:
        """Checks if languages of text data are corresponding to languages of the website"""
        languages = localization_models.Language.objects.all().values_list('id', flat=True)
        for language in languages:
            if language not in self.text_data_languages_ids:
                return False
        return True

    @property
    def text_data_languages_names(self) -> [str]:
        return GalleryImagePositionTextData.objects.filter(gallery_image_position=self).all().values_list(
            'language__name', flat=True)

    @property
    def text_data_languages_ids(self) -> [int]:
        return GalleryImagePositionTextData.objects.filter(gallery_image_position=self).all().values_list(
            'language__id', flat=True)

    class Meta:
        db_table = 'gallery_gallery_image_positions'
        verbose_name = _('Gallery image position')
        verbose_name_plural = _('Gallery image positions')


class Gallery(models.Model):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    first_image = models.ImageField(null=True, blank=True, verbose_name=_('First cover'), help_text=_('First cover'))
    second_image = models.ImageField(null=True, blank=True, verbose_name=_('Second cover'), help_text=_('Second cover'))
    marker = models.CharField(max_length=256, verbose_name=_('Marker'), help_text=_('Marker'))

    def __str__(self) -> str:
        lang = translation.get_language()
        language = localization_models.Language.objects.filter(short_name=lang).values_list('id', flat=True)
        if language.__len__() > 0:
            language = language[0]
            gallery_text_data = GalleryTextData.objects.filter(gallery=self, language=language).first()
            if gallery_text_data is not None:
                return gallery_text_data.name
        gallery_text_data = GalleryTextData.objects.filter(gallery=self, default=True).first()
        return gallery_text_data.name

    def save(self, force_insert: bool = False, force_update: bool = False, using=None,
             update_fields=None) -> None:
        for field in self._meta.fields:
            if field.name == 'first_image':
                field.upload_to = str.format("gallery/{0}/cover/first_image/", self.marker)
            if field.name == 'second_image':
                field.upload_to = str.format("gallery/{0}/cover/second_image/", self.marker)
        super(Gallery, self).save()

    def delete(self, using=None):
        path = os.path.join(settings.BASE_DIR, settings.MEDIA_ROOT, str.format('gallery/{0}', self.marker))
        try:
            shutil.rmtree(path)
            super(Gallery, self).delete()
        except Exception:
            pass

    def name(self) -> str:
        return self.__str__()
    name.short_description = _('Name')

    def author(self) -> auth_models.User:
        label = GalleryDateTimeUserLabel.objects.filter(gallery=self).first()
        return label.author
    author.short_description = _('Author')

    def last_editor(self) -> auth_models.User:
        label = GalleryDateTimeUserLabel.objects.filter(gallery=self).first()
        return label.last_editor
    last_editor.short_description = _('Last editor')

    def creating_date(self) -> models.DateTimeField:
        label = GalleryDateTimeUserLabel.objects.filter(gallery=self).first()
        return label.creating_date
    creating_date.short_description = _('Creating date')

    def last_modified_date(self) -> models.DateTimeField:
        label = GalleryDateTimeUserLabel.objects.filter(gallery=self).first()
        return label.last_modified_date
    last_modified_date.short_description = _('Last modified date')

    def first_image_admin_display(self):
        return str.format("<img src=/media/{0} alt='Gallery first image' style='width:10em'>", self.first_image)
    first_image_admin_display.allow_tags = True
    first_image_admin_display.short_description = _('First cover')

    def second_image_admin_display(self):
        return str.format("<img src=/media/{0} alt = 'Gallery second image' style='width:10em'>", self.second_image)
    second_image_admin_display.allow_tags = True
    second_image_admin_display.short_description = _('Second cover')

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
        return GalleryTextData.objects.filter(gallery=self).all().values_list(
            'language__name', flat=True)

    @property
    def text_data_languages_ids(self) -> [int]:
        return GalleryTextData.objects.filter(gallery=self).all().values_list(
            'language__id', flat=True)

    class Meta:
        db_table = 'gallery_galleries'
        verbose_name = _('Gallery')
        verbose_name_plural = _('Galleries')


class GalleryDateTimeUserLabel(models.Model):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'))
    creating_date = models.DateTimeField(blank=True, verbose_name=_('Creating date'))
    last_modified_date = models.DateTimeField(blank=True, null=True, verbose_name=_('Last modified date'))
    author = models.ForeignKey(auth_models.User, related_name='gallery_author', blank=True, verbose_name=_('Author'))
    last_editor = models.ForeignKey(auth_models.User, related_name='gallery_last_editor', blank=True, null=True,
                                    verbose_name=_('Last edited by'))
    gallery = models.OneToOneField(Gallery, verbose_name=_('Gallery'))

    class Meta:
        db_table = 'gallery_datetime_user_label'
        unique_together = ('id', 'gallery')
        verbose_name = _('Gallery datetime user label')
        verbose_name_plural = _('Galleries datetime user labels')


class GalleryImagePositionTextData(models.Model):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    language = models.ForeignKey(localization_models.Language, verbose_name=_('Language'), help_text=_('Language'))
    name = models.CharField(max_length=256, blank=True, verbose_name=_('Name'), help_text=_('Name'))
    description = models.CharField(max_length=256, null=True, blank=True, verbose_name=_('Description'),
                                   help_text=_('Description'))
    gallery_image_position = models.ForeignKey(GalleryImagePosition, verbose_name=_('Gallery image'),
                                               help_text=_('Gallery image'))
    default = models.BooleanField(default=False, verbose_name=_('Is default?'), help_text=_('Is default?'))

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'gallery_image_position_text_data'
        unique_together = ('language', 'gallery_image_position')
        verbose_name = _('Gallery image position metadata')
        verbose_name_plural = _('Galleries image positions metadata')


class GalleryTextData(models.Model):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    language = models.ForeignKey(localization_models.Language, verbose_name=_('Language'), help_text=_('Language'))
    name = models.CharField(max_length=256, blank=True, verbose_name=_('Name'), help_text=_('Name'))
    description = models.CharField(max_length=256, null=True, blank=True, verbose_name=_('Description'),
                                   help_text=_('Description'))
    gallery = models.ForeignKey(Gallery, verbose_name=_('Gallery'), help_text=_('Gallery'))
    default = models.BooleanField(default=False, verbose_name=_('Is default?'), help_text=_('Is default?'))

    class Meta:
        db_table = 'gallery_text_data'
        unique_together = ('language', 'gallery')
        verbose_name = _('Gallery metadata')
        verbose_name_plural = _('Galleries metadata')
