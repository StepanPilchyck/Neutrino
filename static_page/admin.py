from datetime import datetime
from django.contrib import admin
from django.contrib.auth import models as auth_models
from django.db import models
from django.db.models import Max
import static_page.models as static_page_models
import localization.models as localization_models
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin import SimpleListFilter
import ckeditor_uploader.widgets as ckeditor_uploader_widgets
import tabbed_admin
from django.core.cache import cache


class CreatedByStaticPageFilter(SimpleListFilter):
    title = _('Author')

    parameter_name = 'author'

    def lookups(self, request, model_admin) -> [(int, str)]:
        labels = static_page_models.StaticPageDateTimeUserLabel.objects.all().values_list('author__id',
                                                                                          'author__username')
        lookup = []
        for author_id, author in labels:
            if (author_id, author) not in lookup:
                lookup.append((author_id, author))
        return lookup

    def queryset(self, request, queryset) -> [static_page_models.StaticPage]:
        if self.value() is not None:
            pages = static_page_models.StaticPageDateTimeUserLabel.objects.filter(
                author=auth_models.User.objects.filter(pk=self.value()).first().id).all().values_list('page__id',
                                                                                                      flat=True)
        else:
            pages = static_page_models.StaticPageDateTimeUserLabel.objects.all().values_list('page__id', flat=True)
        return queryset.filter(id__in=pages)


class StaticPageByCategoryFilter(SimpleListFilter):
    title = _('Category')

    parameter_name = 'category'

    def lookups(self, request, model_admin) -> [(int, str)]:
        categories = static_page_models.StaticPageCategory.objects.all().values_list('id', 'name')
        lookup = []
        for category_id, category_name in categories:
            if (category_id, category_name) not in lookup:
                lookup.append((category_id, category_name))
        return lookup

    def queryset(self, request, queryset) -> [static_page_models.StaticPage]:
        if self.value() is not None:
            return queryset.filter(category=static_page_models.StaticPageCategory.objects.filter(pk=self.value()))
        return queryset


class LastModifiedByStaticPageFilter(SimpleListFilter):
    title = _('Last editor')

    parameter_name = 'last_editor'

    def lookups(self, request, model_admin) -> [(int, str)]:
        labels = static_page_models.StaticPageDateTimeUserLabel.objects.all().values_list('last_editor__id',
                                                                                          'last_editor__username')
        lookup = [('None', _('None')), ]
        for editor_id, editor in labels:
            if ((editor_id, editor) not in lookup) and editor is not None:
                lookup.append((editor_id, editor))
        return lookup

    def queryset(self, request, queryset) -> [static_page_models.StaticPage]:
        if self.value() == 'None':
            pages = static_page_models.StaticPageDateTimeUserLabel.objects.filter(last_editor=None).all().values_list(
                'page__id', flat=True)
        elif self.value() is not None:
            pages = static_page_models.StaticPageDateTimeUserLabel.objects.filter(
                author=auth_models.User.objects.filter(pk=self.value()).first().id).all().values_list('page__id',
                                                                                                      flat=True)
        else:
            pages = static_page_models.StaticPageDateTimeUserLabel.objects.all().values_list('page__id', flat=True)
        return queryset.filter(id__in=pages)


class LanguageTextFilter(SimpleListFilter):
    title = _('Language')

    parameter_name = 'language'

    def lookups(self, request, model_admin) -> [(int, str)]:
        texts = static_page_models.Text.objects.filter().all().values_list('language__id', 'language__short_name')
        lookup = []
        for lang_id, name in texts:
            if (lang_id, name) not in lookup:
                lookup.append((lang_id, name))
        return lookup

    def queryset(self, request, queryset) -> [static_page_models.Text]:
        if self.value() is None:
            return queryset
        return queryset.filter(language=localization_models.Language.objects.filter(pk=self.value()).first())


class StaticPageTextFilter(SimpleListFilter):
    title = _('Static page')

    parameter_name = 'static_page'

    def lookups(self, request, model_admin) -> [(int, str)]:
        pages = static_page_models.StaticPage.objects.filter().all().values_list('id', 'name')
        lookup = []
        for page_id, name in pages:
            if (page_id, name) not in lookup:
                lookup.append((page_id, name))
        return lookup

    def queryset(self, request, queryset) -> [static_page_models.Text]:
        if self.value() is None:
            return queryset
        return queryset.filter(page=static_page_models.StaticPage.objects.filter(pk=self.value()).first())


class StaticPageSeoInformationUnrealizedLanguageFilter(SimpleListFilter):
    title = _('Unrealized SEO information')

    parameter_name = 'seo_lang'

    def lookups(self, request, model_admin) -> [(int, str)]:
        languages = localization_models.Language.objects.all().values_list('id', 'name')
        lookup = [('True', 'Has no unrealized languages'), ('False', 'Has unrealized languages')]
        for lang_id, name in languages:
            lookup.append((lang_id, name))
        return lookup

    def queryset(self, request, queryset) -> [static_page_models.StaticPage]:
        if self.value() is None:
            return queryset
        result = []
        if self.value() == 'True':
            for static_page in queryset:
                if static_page.check_language_for_seo_information:
                    result.append(static_page.id)
        elif self.value() == 'False':
            for static_page in queryset:
                if not static_page.check_language_for_seo_information:
                    result.append(static_page.id)
        else:
            language = localization_models.Language.objects.filter(pk=self.value()).all().values_list('id', flat=True)
            if language.__len__() > 0:
                language = language[0]
                for static_page in queryset:
                    if language not in static_page.seo_information_languages_ids:
                        result.append(static_page.id)
        return queryset.filter(id__in=result)


class StaticPageTextNotRealizedLanguageFilter(SimpleListFilter):
    title = _('Unrealized Texts')

    parameter_name = 'text_lang'

    def lookups(self, request, model_admin) -> [(int, str)]:
        languages = localization_models.Language.objects.all().values_list('id', 'name')
        lookup = [('True', 'Has no unrealized languages'), ('False', 'Has unrealized languages')]
        for lang_id, name in languages:
            lookup.append((lang_id, name))
        return lookup

    def queryset(self, request, queryset) -> [static_page_models.StaticPage]:
        if self.value() is None:
            return queryset
        result = []
        if self.value() == 'True':
            for static_page in queryset:
                if static_page.check_language_for_text:
                    result.append(static_page.id)
        elif self.value() == 'False':
            for static_page in queryset:
                if not static_page.check_language_for_text:
                    result.append(static_page.id)
        else:
            language = localization_models.Language.objects.filter(pk=self.value()).all().values_list('id', flat=True)
            if language.__len__() > 0:
                language = language[0]
                for static_page in queryset:
                    if language not in static_page.text_languages_ids:
                        result.append(static_page.id)
        return queryset.filter(id__in=result)


class StaticPageNotRealizedLanguageFilter(SimpleListFilter):
    title = _('Realized Languages')

    parameter_name = 'static_page_lang'

    def lookups(self, request, model_admin) -> [(str, str)]:
        return [('False', 'Has unrealized languages'),
                ('True', 'Has no unrealized languages')]

    def queryset(self, request, queryset) -> [static_page_models.StaticPage]:
        if self.value() is None:
            return queryset
        result = []
        if self.value() == 'False':
            for static_page in queryset:
                if not static_page.check_language:
                    result.append(static_page.id)
        elif self.value() == 'True':
            for static_page in queryset:
                if static_page.check_language:
                    result.append(static_page.id)
        return queryset.filter(id__in=result)


class SeoInformationInline(admin.StackedInline):
    model = static_page_models.SeoInformation
    ordering = ('language',)
    extra = 1


class TextInline(admin.StackedInline):
    model = static_page_models.Text
    ordering = ('weight', 'language', )
    formfield_overrides = {
        models.TextField: {'widget': ckeditor_uploader_widgets.CKEditorUploadingWidget},
    }
    extra = 1


class TextAdmin(admin.ModelAdmin):
    list_display = ('page', 'name', 'language',)
    list_filter = (LanguageTextFilter, StaticPageTextFilter,)
    search_fields = ('name', '@body',)

    formfield_overrides = {
        models.TextField: {'widget': ckeditor_uploader_widgets.CKEditorUploadingWidget},
    }

    def save_model(self, request, obj, form, change) -> None:
        if obj.weight is None:
            max_weight = \
                static_page_models.Text.objects.filter(page=obj.page,
                                                       language=obj.language).all().aggregate(
                    Max('weight'))['weight__max']
            if max_weight:
                obj.weight = max_weight + 1
            else:
                obj.weight = 0
            obj.save()
        form.save()


class StaticPageAdmin(tabbed_admin.TabbedModelAdmin):
    # inlines = (TextInline, SeoInformationInline)
    ordering = ('name',)
    list_filter = (CreatedByStaticPageFilter,
                   LastModifiedByStaticPageFilter,
                   StaticPageSeoInformationUnrealizedLanguageFilter,
                   StaticPageTextNotRealizedLanguageFilter,
                   StaticPageNotRealizedLanguageFilter,
                   StaticPageByCategoryFilter)
    list_display = ('name',
                    'texts_languages_admin_display',
                    'seo_information_languages_admin_display',
                    'check_language_admin_display',
                    'check_language_for_seo_admin_display',
                    'check_language_for_text_admin_display',
                    'creating_date',
                    'author',
                    'last_modified_date',
                    'last_editor',)
    tab_overview = (
        (None, {
            'fields': ('name', 'galleries', 'default_language', 'category', 'template')
        }),
    )
    tab_text = (
        TextInline,
    )
    tab_seo = (
        SeoInformationInline,
    )
    tabs = [
        (_('Overview'), tab_overview),
        (_('Texts'), tab_text),
        (_('SEO'), tab_seo),
    ]
    search_fields = ['name', ]

    def save_model(self, request, obj, form, change) -> None:
        if change:
            date_time_user_label = static_page_models.StaticPageDateTimeUserLabel.objects.filter(page=obj).first()
            date_time_user_label.last_modified_date = datetime.now()
            date_time_user_label.last_editor = request.user
            date_time_user_label.save()
            obj.save()
        else:
            obj.save()
            date_time_user_label = static_page_models.StaticPageDateTimeUserLabel()
            date_time_user_label.creating_date = datetime.now()
            date_time_user_label.page = obj
            date_time_user_label.author = request.user
            date_time_user_label.save()

        cache.clear()
        form.save()

    def save_formset(self, request, form, formset, change) -> None:
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, static_page_models.Text) and instance.weight is None:
                max_weight = \
                    static_page_models.Text.objects.filter(page=instance.page,
                                                           language=instance.language).all().aggregate(
                        Max('weight'))['weight__max']
                if max_weight is not None:
                    instance.weight = max_weight + 1
                else:
                    instance.weight = 0
                instance.save()
        form.save()
        formset.save()

    class Media:
        js = (
            'admin/js/AdminStaticPages.js',
        )


admin.register(static_page_models.StaticPageDateTimeUserLabel)
admin.register(static_page_models.SeoInformation)
admin.site.register(static_page_models.StaticPageTemplate)
admin.site.register(static_page_models.Text, TextAdmin)
admin.site.register(static_page_models.StaticPage, StaticPageAdmin)
admin.site.register(static_page_models.StaticPageCategory)
