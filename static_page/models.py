from django.db import models
from django.contrib.auth import models as auth_models
from gallery import models as gallery_models
from django.utils.translation import ugettext_lazy as _
import localization.models as localization_models
import sortedm2m.fields as sortedm2m


class StaticPageTemplate(models.Model):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    name = models.CharField(max_length=256, verbose_name=_('Name'), help_text=_('Name'), unique=True)
    path = models.CharField(max_length=256, verbose_name=_('Path'), help_text=_('Path'), unique=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "static_page_static_page_templates"
        verbose_name = _("Static Page Template")
        verbose_name_plural = _("Static Pages Templates")


class StaticPageCategory(models.Model):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    name = models.CharField(max_length=256, verbose_name=_('Name'), help_text=_('Name'), unique=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "static_page_static_page_categories"
        verbose_name = _("Static Page Category")
        verbose_name_plural = _("Static Page Categories")


class StaticPage(models.Model):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    name = models.CharField(max_length=256, verbose_name=_('Name'), db_index=True, help_text=_('Name'))
    galleries = sortedm2m.SortedManyToManyField(gallery_models.Gallery, blank=True, verbose_name=_('Galleries'),
                                                help_text=_('Galleries'))
    default_language = models.ForeignKey(localization_models.Language, verbose_name=_('Default language'),
                                         help_text=_('Default language'))
    category = models.ForeignKey(StaticPageCategory, verbose_name=_('Category'), help_text=_('Category'))
    template = models.ForeignKey(StaticPageTemplate, verbose_name=_('Template'), help_text=_('Template'))

    def __str__(self) -> str:
        return self.name

    def texts_languages_admin_display(self) -> str:
        texts = Text.objects.filter(page=self).all()
        result = []
        for text in texts:
            if text.language.name not in result:
                result.append(text.language.name)
        result.sort()
        return "<br/>".join(result)

    texts_languages_admin_display.allow_tags = True
    texts_languages_admin_display.short_description = _('Languages of texts')

    def seo_information_languages_admin_display(self) -> str:
        seo_data = SeoInformation.objects.filter(page=self).all()
        result = []
        for seo_info in seo_data:
            if seo_info.language.name not in result:
                result.append(seo_info.language.name)
        result.sort()
        return "<br/>".join(result)

    seo_information_languages_admin_display.allow_tags = True
    seo_information_languages_admin_display.short_description = _('Languages of SEO information')

    def check_language_admin_display(self) -> str:
        """Checks if languages of texts are corresponding to seo information languages of this page"""
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
    def check_language(self) -> bool:
        """Checks if languages of texts are corresponding to seo information languages of this page"""
        if set(self.seo_information_languages_ids) == set(self.text_languages_ids):
            return True
        return False

    @property
    def check_language_for_seo_information(self) -> bool:
        """Checks if seo information languages are corresponding to languages of the website"""
        languages = localization_models.Language.objects.exclude(
            id__in=SeoInformation.objects.filter(page=self).all().values_list('language__name', flat=True)).values_list(
            'id', flat=True)
        if languages.__len__() > 0:
            return False
        return True

    @property
    def check_language_for_text(self) -> bool:
        """Checks if texts languages are corresponding to languages of the website"""
        languages = localization_models.Language.objects.exclude(
            id__in=Text.objects.filter(page=self).all().values_list('language__name', flat=True)).values_list('id',
                                                                                                              flat=True)
        if languages.__len__() > 0:
            return False
        return True

    @property
    def text_languages_names(self) -> [str]:
        texts_languages = Text.objects.filter(page=self).all().values_list('language__name', flat=True)
        return texts_languages

    @property
    def text_languages_ids(self) -> [int]:
        texts_languages = Text.objects.filter(page=self).all().values_list('language__id', flat=True)
        return texts_languages

    @property
    def seo_information_languages_names(self) -> [str]:
        seo_data_languages = SeoInformation.objects.filter(page=self).all().values_list('language__name', flat=True)
        return seo_data_languages

    @property
    def seo_information_languages_ids(self) -> [int]:
        seo_data_languages = SeoInformation.objects.filter(page=self).all().values_list('language__id', flat=True)
        return seo_data_languages

    def author(self) -> auth_models.User:
        label = StaticPageDateTimeUserLabel.objects.filter(page=self).first()
        return label.author

    author.short_description = _('Author')

    def last_editor(self) -> auth_models.User:
        label = StaticPageDateTimeUserLabel.objects.filter(page=self).first()
        return label.last_editor

    last_editor.short_description = _('Last editor')

    def creating_date(self) -> models.DateTimeField:
        label = StaticPageDateTimeUserLabel.objects.filter(page=self).first()
        return label.creating_date

    creating_date.short_description = _('Creating date')

    def last_modified_date(self) -> models.DateTimeField:
        label = StaticPageDateTimeUserLabel.objects.filter(page=self).first()
        return label.last_modified_date

    last_modified_date.short_description = _('Last modified date')

    class Meta:
        db_table = "static_page_static_pages"
        unique_together = ('name', 'category')
        verbose_name = _("Static page")
        verbose_name_plural = _("Static pages")


class Text(models.Model):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    language = models.ForeignKey(localization_models.Language, verbose_name=_('Language'), help_text=_('Language'))
    name = models.CharField(max_length=256, verbose_name=_('Name'), help_text=_('Name'))
    body = models.TextField(verbose_name=_('Body'), help_text=_('Body'))
    page = models.ForeignKey(StaticPage, verbose_name=_('Page'), help_text=_('Page'))
    weight = models.IntegerField(blank=True, verbose_name=_('Weight'), help_text=_('Weight'))

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('name', 'page', 'language')
        db_table = 'static_page_texts'
        verbose_name = _('Text')
        verbose_name_plural = _('Texts')


class StaticPageDateTimeUserLabel(models.Model):
    id = models.AutoField(primary_key=True, verbose_name=_('Id'), help_text=_('Unique identifier'))
    creating_date = models.DateTimeField(blank=True, verbose_name=_('Creating date'), help_text=_('Creating date'))
    last_modified_date = models.DateTimeField(blank=True, null=True, verbose_name=_('Last modified date'),
                                              help_text=_('Last modified date'))
    author = models.ForeignKey(auth_models.User, related_name='static_page_author', blank=True,
                               verbose_name=_('Author'), help_text=_('Author'))
    last_editor = models.ForeignKey(auth_models.User, related_name='static_page_last_editor', blank=True, null=True,
                                    verbose_name=_('Last edited by'), help_text=_('Last edited by'))
    page = models.OneToOneField(StaticPage, verbose_name=_('Page'), help_text=_('Page'))

    class Meta:
        db_table = 'static_page_datetime_user_label'
        unique_together = ('id', 'page')
        verbose_name = _('Static page datetime user label')
        verbose_name_plural = _('Static page datetime user labels')


class SeoInformation(models.Model):
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
    page = models.ForeignKey(StaticPage, verbose_name=_('Page'), help_text=_('Page'))

    class Meta:
        db_table = 'static_page_seo_information'
        unique_together = ('language', 'page')
        verbose_name = _('Seo information')
        verbose_name_plural = _('Seo information')
