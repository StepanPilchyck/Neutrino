from django.contrib import admin
from datetime import datetime
from django.utils.translation import ugettext_lazy as _
from catalogue import models as catalogue_models
from django.db.models import Max
from django.contrib.auth import models as auth_models
from django.db import models
import ckeditor_uploader.widgets as ckeditor_uploader_widgets
from django import forms
from django.core.exceptions import ValidationError
import image_cropping
from django.contrib.admin import SimpleListFilter
import localization.models as localization_models
import tabbed_admin
from django.core.cache import cache
import collections


# Category
class CreatedByCategoryFilter(SimpleListFilter):
    title = _('Author')

    parameter_name = 'author'

    def lookups(self, request, model_admin) -> [(int, str)]:
        labels = catalogue_models.CategoryDateTimeUserLabel.objects.all().values_list('author__id', 'author__username')
        lookup = []
        for author_id, author in labels:
            if (author_id, author) not in lookup:
                lookup.append((author_id, author))
        return lookup

    def queryset(self, request, queryset) -> [catalogue_models.Category]:
        if self.value() is not None:
            categories = catalogue_models.CategoryDateTimeUserLabel.objects.filter(
                author=auth_models.User.objects.filter(pk=self.value()).first().id).all().values_list('category__id',
                                                                                                      flat=True)
        else:
            categories = catalogue_models.CategoryDateTimeUserLabel.objects.all().values_list('category__id', flat=True)
        return queryset.filter(id__in=categories)


class LastModifiedByCategoryFilter(SimpleListFilter):
    title = _('Last editor')

    parameter_name = 'last_editor'

    def lookups(self, request, model_admin) -> [(int, str)]:
        labels = catalogue_models.CategoryDateTimeUserLabel.objects.all().values_list('last_editor__id',
                                                                                      'last_editor__username')
        lookup = [('None', _('None')), ]
        for editor_id, editor in labels:
            if ((editor_id, editor) not in lookup) and editor is not None:
                lookup.append((editor_id, editor))
        return lookup

    def queryset(self, request, queryset) -> [catalogue_models.Category]:
        if self.value() == 'None':
            categories = catalogue_models.CategoryDateTimeUserLabel.objects.filter(last_editor=None).all().values_list(
                'category__id', flat=True)
        elif self.value() is not None:
            categories = catalogue_models.CategoryDateTimeUserLabel.objects.filter(
                author=auth_models.User.objects.filter(pk=self.value()).first().id).all().values_list('category__id',
                                                                                                      flat=True)
        else:
            categories = catalogue_models.CategoryDateTimeUserLabel.objects.all().values_list('category__id', flat=True)
        return queryset.filter(id__in=categories)


class CategoryTextLanguageFilter(SimpleListFilter):
    title = _('Language')

    parameter_name = 'language'

    def lookups(self, request, model_admin) -> [(int, str)]:
        texts = catalogue_models.CategoryText.objects.filter().all().values_list('language__id', 'language__short_name')
        lookup = []
        for lang_id, name in texts:
            if (lang_id, name) not in lookup:
                lookup.append((lang_id, name))
        return lookup

    def queryset(self, request, queryset) -> [catalogue_models.CategoryText]:
        if self.value() is None:
            return queryset
        return queryset.filter(language=localization_models.Language.objects.filter(pk=self.value()).first())


class CategoryTextFilter(SimpleListFilter):
    title = _('Category')

    parameter_name = 'category'

    def lookups(self, request, model_admin) -> [(int, str)]:
        pages = catalogue_models.Category.objects.filter().all().values_list('id', 'name')
        lookup = []
        for page_id, name in pages:
            if (page_id, name) not in lookup:
                lookup.append((page_id, name))
        return lookup

    def queryset(self, request, queryset) -> [catalogue_models.CategoryText]:
        if self.value() is None:
            return queryset
        return queryset.filter(category=catalogue_models.Category.objects.filter(pk=self.value()).first())


class CategorySeoInformationNotRealizedLanguageFilter(SimpleListFilter):
    title = _('Unrealized SEO information')

    parameter_name = 'seo_lang'

    def lookups(self, request, model_admin) -> [(int, str)]:
        languages = localization_models.Language.objects.all().values_list('id', 'name')
        lookup = [('True', 'Has no unrealized languages'), ('False', 'Has unrealized languages')]
        for lang_id, name in languages:
            lookup.append((lang_id, name))
        return lookup

    def queryset(self, request, queryset) -> [catalogue_models.Category]:
        if self.value() is None:
            return queryset
        result = []
        if self.value() == 'True':
            for category in queryset:
                if category.check_language_for_seo_information:
                    result.append(category.id)
        elif self.value() == 'False':
            for category in queryset:
                if not category.check_language_for_seo_information:
                    result.append(category.id)
        else:
            for category in queryset:
                language = localization_models.Language.objects.filter(pk=self.value()).all().values_list('id',
                                                                                                          flat=True)
                if language.__len__() > 0:
                    language = language[0]
                    if language not in category.seo_information_languages_ids:
                        result.append(category.id)
        return queryset.filter(id__in=result)


class CategoryTextNotRealizedLanguageFilter(SimpleListFilter):
    title = _('Unrealized Texts')

    parameter_name = 'text_lang'

    def lookups(self, request, model_admin) -> [(int, str)]:
        languages = localization_models.Language.objects.all().values_list('id', 'name')
        lookup = [('True', 'Has no unrealized languages'), ('False', 'Has unrealized languages')]
        for lang_id, name in languages:
            lookup.append((lang_id, name))
        return lookup

    def queryset(self, request, queryset) -> [catalogue_models.Category]:
        if self.value() is None:
            return queryset
        result = []
        if self.value() == 'True':
            for category in queryset:
                if category.check_language_for_text:
                    result.append(category.id)
        elif self.value() == 'False':
            for category in queryset:
                if not category.check_language_for_text:
                    result.append(category.id)
        else:
            for category in queryset:
                language = localization_models.Language.objects.filter(pk=self.value()).all().values_list('id',
                                                                                                          flat=True)
                if language.__len__() > 0:
                    language = language[0]
                    if language not in category.text_languages_ids:
                        result.append(category.id)
        return queryset.filter(id__in=result)


class CategoryNotRealizedLanguageFilter(SimpleListFilter):
    title = _('Realized Languages')

    parameter_name = 'category_lang'

    def lookups(self, request, model_admin) -> [(str, str)]:
        return [('False', 'Has unrealized languages'),
                ('True', 'Has no unrealized languages')]

    def queryset(self, request, queryset) -> [catalogue_models.Category]:
        if self.value() is None:
            return queryset
        result = []
        if self.value() == 'False':
            for category in queryset:
                if not category.check_language:
                    result.append(category.id)
        elif self.value() == 'True':
            for category in queryset:
                if category.check_language:
                    result.append(category.id)
        return queryset.filter(id__in=result)


class CategorySeoInformationInline(admin.StackedInline):
    model = catalogue_models.CategorySeoInformation
    ordering = ('language',)
    extra = 1


class CategoryTextInline(admin.StackedInline):
    model = catalogue_models.CategoryText
    ordering = ('name', 'language', 'weight',)
    formfield_overrides = {
        models.TextField: {'widget': ckeditor_uploader_widgets.CKEditorUploadingWidget},
    }
    extra = 1


class CategoryNameInlineFormset(forms.models.BaseInlineFormSet):
    def clean(self) -> None:
        i = 0
        for form in self.forms:
            if form.cleaned_data.__len__() != 0:
                if form.cleaned_data["default"] and not form.cleaned_data["DELETE"]:
                    i += 1
        if i == 0:
            raise ValidationError(_("Category must have at least one default name"))
        elif i != 1:
            raise ValidationError(_("Category must have only one default name"))


class CategoryNameInline(admin.TabularInline):
    formset = CategoryNameInlineFormset
    model = catalogue_models.CategoryName
    ordering = ('id',)
    extra = 1


class CategoryTextAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'language',)
    list_filter = (CategoryTextLanguageFilter, CategoryTextFilter,)
    search_fields = ('name', '@body',)

    formfield_overrides = {
        models.TextField: {'widget': ckeditor_uploader_widgets.CKEditorUploadingWidget},
    }

    def save_model(self, request, obj, form, change) -> None:
        if obj.weight is None:
            max_weight = \
                catalogue_models.CategoryText.objects.filter(categorye=obj.category,
                                                             language=obj.language).all().aggregate(
                    Max('weight'))['weight__max']
            if max_weight:
                obj.weight = max_weight + 1
            else:
                obj.weight = 0
            obj.save()
        form.save()


class CategoryAdmin(tabbed_admin.TabbedModelAdmin):
    ordering = ('id',)
    list_filter = (CreatedByCategoryFilter,
                   LastModifiedByCategoryFilter,
                   CategorySeoInformationNotRealizedLanguageFilter,
                   CategoryTextNotRealizedLanguageFilter,
                   CategoryNotRealizedLanguageFilter,)
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
            'fields': ('url', 'default_language', 'galleries', 'template')
        }),
    )
    tab_name = (
        CategoryNameInline,
    )
    tab_text = (
        CategoryTextInline,
    )
    tab_cover = (
        (None, {
            'fields': ('first_image', 'second_image',)
        }),
    )
    tab_seo = (
        CategorySeoInformationInline,
    )
    tabs = [
        (_('Overview'), tab_overview),
        (_('Name'), tab_name),
        (_('Texts'), tab_text),
        (_('Cover'), tab_cover),
        (_('SEO'), tab_seo),
    ]

    # search_fields = ['name', ]

    def save_model(self, request, obj, form, change) -> None:
        if change:
            date_time_user_label = catalogue_models.CategoryDateTimeUserLabel.objects.filter(
                category=obj).first()
            date_time_user_label.last_modified_date = datetime.now()
            date_time_user_label.last_editor = request.user
            date_time_user_label.save()
            obj.save()
        else:
            obj.save()
            date_time_user_label = catalogue_models.CategoryDateTimeUserLabel()
            date_time_user_label.creating_date = datetime.now()
            date_time_user_label.category = obj
            date_time_user_label.author = request.user
            date_time_user_label.save()
        cache.clear()
        form.save()

    actions = ['delete_model']

    def get_actions(self, request):
        actions = super(CategoryAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    def delete_model(self, request, obj):
        if isinstance(obj, collections.Iterable):
            for o in obj.all():
                o.delete()
        else:
            obj.delete()

    def save_formset(self, request, form, formset, change) -> None:
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, catalogue_models.CategoryText) and instance.weight is None:
                max_weight = \
                    catalogue_models.CategoryText.objects.filter(category=instance.category,
                                                                 language=instance.language).all().aggregate(
                        Max('weight'))['weight__max']
                if max_weight is not None:
                    instance.weight = max_weight + 1
                else:
                    instance.weight = 0
                instance.save()
        form.save()
        formset.save()


# Item
class CreatedByItemFilter(SimpleListFilter):
    title = _('Author')

    parameter_name = 'author'

    def lookups(self, request, model_admin) -> [(int, str)]:
        labels = catalogue_models.ItemDateTimeUserLabel.objects.all().values_list('author__id', 'author__username')
        lookup = []
        for author_id, author in labels:
            if (author_id, author) not in lookup:
                lookup.append((author_id, author))
        return lookup

    def queryset(self, request, queryset) -> [catalogue_models.Item]:
        if self.value() is not None:
            items = catalogue_models.ItemDateTimeUserLabel.objects.filter(
                author=auth_models.User.objects.filter(pk=self.value()).first().id).all().values_list('item__id',
                                                                                                      flat=True)
        else:
            items = catalogue_models.ItemDateTimeUserLabel.objects.all().values_list('item__id', flat=True)
        return queryset.filter(id__in=items)


class LastModifiedByItemFilter(SimpleListFilter):
    title = _('Last editor')

    parameter_name = 'last_editor'

    def lookups(self, request, model_admin) -> [(int, str)]:
        labels = catalogue_models.ItemDateTimeUserLabel.objects.all().values_list('last_editor__id',
                                                                                  'last_editor__username')
        lookup = [('None', _('None')), ]
        for editor_id, editor in labels:
            if ((editor_id, editor) not in lookup) and editor is not None:
                lookup.append((editor_id, editor))
        return lookup

    def queryset(self, request, queryset) -> [catalogue_models.Item]:
        if self.value() == 'None':
            items = catalogue_models.ItemDateTimeUserLabel.objects.filter(last_editor=None).all().values_list(
                'item__id', flat=True)
        elif self.value() is not None:
            items = catalogue_models.ItemDateTimeUserLabel.objects.filter(
                author=auth_models.User.objects.filter(pk=self.value()).first().id).all().values_list('item__id',
                                                                                                      flat=True)
        else:
            items = catalogue_models.ItemDateTimeUserLabel.objects.all().values_list('item__id', flat=True)
        return queryset.filter(id__in=items)


class ItemTextLanguageFilter(SimpleListFilter):
    title = _('Language')

    parameter_name = 'language'

    def lookups(self, request, model_admin) -> [(int, str)]:
        texts = catalogue_models.ItemText.objects.filter().all().values_list('language__id', 'language__short_name')
        lookup = []
        for lang_id, name in texts:
            if (lang_id, name) not in lookup:
                lookup.append((lang_id, name))
        return lookup

    def queryset(self, request, queryset) -> [catalogue_models.ItemText]:
        if self.value() is None:
            return queryset
        return queryset.filter(language=localization_models.Language.objects.filter(pk=self.value()).first())


class ItemTextFilter(SimpleListFilter):
    title = _('Item')

    parameter_name = 'item'

    def lookups(self, request, model_admin) -> [(int, str)]:
        pages = catalogue_models.Item.objects.filter().all().values_list('id', 'name')
        lookup = []
        for page_id, name in pages:
            if (page_id, name) not in lookup:
                lookup.append((page_id, name))
        return lookup

    def queryset(self, request, queryset) -> [catalogue_models.ItemText]:
        if self.value() is None:
            return queryset
        return queryset.filter(item=catalogue_models.Item.objects.filter(pk=self.value()).first())


class ItemSeoInformationNotRealizedLanguageFilter(SimpleListFilter):
    title = _('Realized SEO information')

    parameter_name = 'seo_lang'

    def lookups(self, request, model_admin) -> [(int, str)]:
        languages = localization_models.Language.objects.all().values_list('id', 'name')
        lookup = [('True', 'Has no unrealized languages'), ('False', 'Has unrealized languages')]
        for lang_id, name in languages:
            lookup.append((lang_id, name))
        return lookup

    def queryset(self, request, queryset) -> [catalogue_models.Item]:
        if self.value() is None:
            return queryset
        result = []
        if self.value() == 'True':
            for item in queryset:
                if item.check_language_for_seo_information:
                    result.append(item.id)
        elif self.value() == 'False':
            for item in queryset:
                if not item.check_language_for_seo_information:
                    result.append(item.id)
        else:
            language = localization_models.Language.objects.filter(pk=self.value()).all().values_list('id',
                                                                                                      flat=True)
            if language.__len__() > 0:
                language = language[0]
                for item in queryset:
                    if language not in item.seo_information_languages_ids:
                        result.append(item.id)
        return queryset.filter(id__in=result)


class ItemTextNotRealizedLanguageFilter(SimpleListFilter):
    title = _('Realized Texts')

    parameter_name = 'text_lang'

    def lookups(self, request, model_admin) -> [(int, str)]:
        languages = localization_models.Language.objects.all().values_list('id', 'name')
        lookup = [('True', 'Has no unrealized languages'), ('False', 'Has unrealized languages')]
        for lang_id, name in languages:
            lookup.append((lang_id, name))
        return lookup

    def queryset(self, request, queryset) -> [catalogue_models.Item]:
        if self.value() is None:
            return queryset
        result = []
        if self.value() == 'True':
            for item in queryset:
                if item.check_language_for_text:
                    result.append(item.id)
        elif self.value() == 'False':
            for item in queryset:
                if not item.check_language_for_text:
                    result.append(item.id)
        else:
            language = localization_models.Language.objects.filter(pk=self.value()).all().values_list('id', flat=True)
            if language.__len__() > 0:
                language = language[0]
                for item in queryset:
                    if language not in item.text_languages_ids:
                        result.append(item.id)
        return queryset.filter(id__in=result)


class ItemShortTextNotRealizedLanguageFilter(SimpleListFilter):
    title = _('Realized Short Texts')

    parameter_name = 'short_text_lang'

    def lookups(self, request, model_admin) -> [(int, str)]:
        languages = localization_models.Language.objects.all().values_list('id', 'name')
        lookup = [('True', 'Has no unrealized languages'), ('False', 'Has unrealized languages')]
        for lang_id, name in languages:
            lookup.append((lang_id, name))
        return lookup

    def queryset(self, request, queryset) -> [catalogue_models.Item]:
        if self.value() is None:
            return queryset
        result = []
        if self.value() == 'True':
            for item in queryset:
                if item.check_language_for_text:
                    result.append(item.id)
        elif self.value() == 'False':
            for item in queryset:
                if not item.check_language_for_text:
                    result.append(item.id)
        else:
            language = localization_models.Language.objects.filter(pk=self.value()).all().values_list('id', flat=True)
            if language.__len__() > 0:
                language = language[0]
                for item in queryset:
                    if language not in item.text_languages_ids:
                        result.append(item.id)
        return queryset.filter(id__in=result)


class ItemNotRealizedLanguageFilter(SimpleListFilter):
    title = _('Realized Languages')

    parameter_name = 'category_lang'

    def lookups(self, request, model_admin) -> [(str, str)]:
        return [('False', 'Has unrealized languages'),
                ('True', 'Has no unrealized languages')]

    def queryset(self, request, queryset) -> [catalogue_models.Item]:
        if self.value() is None:
            return queryset
        result = []
        if self.value() == 'False':
            for item in queryset:
                if not item.check_language:
                    result.append(item.id)
        elif self.value() == 'True':
            for item in queryset:
                if item.check_language:
                    result.append(item.id)
        return queryset.filter(id__in=result)


# TODO Optimize this
class ItemByCategoryFilter(SimpleListFilter):
    title = _('Category')

    parameter_name = 'category'

    def lookups(self, request, model_admin) -> [(int, str)]:
        categories = catalogue_models.Category.objects.all()
        lookup = []
        for category in categories:
            if (category.id, category.name) not in lookup:
                lookup.append((category.id, category.name))
        return lookup

    def queryset(self, request, queryset) -> [catalogue_models.Item]:
        if self.value() is not None:
            return queryset.filter(category=catalogue_models.Category.objects.filter(id=self.value()))
        return queryset


class ItemSeoInformationInline(admin.StackedInline):
    model = catalogue_models.ItemSeoInformation
    ordering = ('language',)
    extra = 1


class ItemImagePositionInlineFormset(forms.models.BaseInlineFormSet):
    def clean(self) -> None:
        i = 0
        for form in self.forms:
            if form.cleaned_data.__len__() != 0:
                if form.cleaned_data["default"] and not form.cleaned_data["DELETE"]:
                    i += 1
        if i == 0:
            raise ValidationError(_("Item must have at least one default name"))
        elif i != 1:
            raise ValidationError(_("Item must have only one default name"))


class ItemImagePositionInline(admin.TabularInline):
    formset = ItemImagePositionInlineFormset
    model = catalogue_models.ItemImagePosition
    ordering = ('weight',)
    extra = 0
    show_change_link = True

    def formfield_for_dbfield(self, db_field, **kwargs):
        crop_fields = getattr(self.model, 'crop_fields', {})
        if db_field.name in crop_fields:
            kwargs['widget'] = image_cropping.ImageCropWidget

        return super(ItemImagePositionInline, self).formfield_for_dbfield(db_field, **kwargs)


class ItemTextInline(admin.StackedInline):
    model = catalogue_models.ItemText
    ordering = ('name', 'language', 'weight',)
    formfield_overrides = {
        models.TextField: {'widget': ckeditor_uploader_widgets.CKEditorUploadingWidget},
    }
    extra = 1


class ItemShortTextInline(admin.StackedInline):
    model = catalogue_models.ItemShortText
    ordering = ('language',)
    formfield_overrides = {
        models.TextField: {'widget': ckeditor_uploader_widgets.CKEditorUploadingWidget},
    }
    extra = 1


class ItemNameInlineFormset(forms.models.BaseInlineFormSet):
    def clean(self) -> None:
        i = 0
        for form in self.forms:
            if form.cleaned_data.__len__() != 0:
                if form.cleaned_data["default"] and not form.cleaned_data["DELETE"]:
                    i += 1
        if i == 0:
            raise ValidationError(_("Item must have at least one default name"))
        elif i != 1:
            raise ValidationError(_("Item must have only one default name"))


class ItemNameInline(admin.TabularInline):
    formset = ItemNameInlineFormset
    model = catalogue_models.ItemName
    ordering = ('id',)
    extra = 1


class ItemTextAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'language',)
    list_filter = (ItemTextLanguageFilter, ItemTextFilter,)
    search_fields = ('name', '@body',)

    formfield_overrides = {
        models.TextField: {'widget': ckeditor_uploader_widgets.CKEditorUploadingWidget},
    }

    def save_model(self, request, obj, form, change) -> None:
        if obj.weight is None:
            max_weight = \
                catalogue_models.ItemText.objects.filter(item=obj.item,
                                                         language=obj.language).all().aggregate(
                    Max('weight'))['weight__max']
            if max_weight:
                obj.weight = max_weight + 1
            else:
                obj.weight = 0
            obj.save()
        form.save()


# TODO Optimize this
class ItemParameterByItemFilter(SimpleListFilter):
    title = _('Item')

    parameter_name = 'item'

    def lookups(self, request, model_admin) -> [(str, str)]:
        items = catalogue_models.Item.objects.all()
        lookup = []
        for item in items:
            if (item.id, item.name) not in lookup:
                lookup.append((item.id, item.name))
        return lookup

    def queryset(self, request, queryset) -> [catalogue_models.ItemParameter]:
        if self.value() is not None:
            return queryset.filter(item=catalogue_models.Item.objects.filter(id=self.value()))
        return queryset


class ItemParameterNameInlineFormset(forms.models.BaseInlineFormSet):
    def clean(self) -> None:
        for form in self.forms:
            if form.cleaned_data.__len__() != 0:
                if form.cleaned_data['item_parameter'].item.default_language == form.cleaned_data['language']:
                    raise ValidationError(_("Item parameter already have name with this language"))


class ItemParameterNameInline(admin.TabularInline):
    formset = ItemParameterNameInlineFormset
    model = catalogue_models.ItemParameterName
    ordering = ('id',)
    extra = 1


class ItemParameterAdmin(admin.ModelAdmin):
    inlines = (ItemParameterNameInline,)
    list_display = ('default_name', 'default_value', 'weight', 'first_image', 'second_image')
    list_editable = ('default_name', 'default_value', 'weight', 'first_image', 'second_image')
    list_filter = (ItemParameterByItemFilter,)

    def save_model(self, request, obj, form, change: bool) -> None:
        if obj.weight is None:
            max_weight = \
                catalogue_models.ItemParameter.objects.filter(item=obj.item).all().aggregate(
                    Max('weight'))['weight__max']
            if max_weight:
                obj.weight = max_weight + 1
            else:
                obj.weight = 0
        form.save()

    def get_actions(self, request):
        actions = super(ItemParameterAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    def delete_model(self, request, obj):
        if isinstance(obj, collections.Iterable):
            for o in obj.all():
                o.delete()
        else:
            obj.delete()

    delete_model.short_description = _('Delete')


class ItemParameterInline(admin.TabularInline):
    model = catalogue_models.ItemParameter
    exclude = ('first_image', 'second_image')
    extra = 1
    ordering = ('default_name',)
    show_change_link = True


class ItemAdminForm(forms.ModelForm):
    class Meta:
        model = localization_models.Currency
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(ItemAdminForm, self).__init__(*args, **kwargs)

    def clean(self):
        if self.cleaned_data.__len__() != 0:
            if (self.cleaned_data['default_price'] is None or self.cleaned_data['default_price'] == 0) and \
                            self.cleaned_data['currency'] is not None:
                raise ValidationError(_("Please check price"))
            elif (self.cleaned_data['default_price'] is not None and self.cleaned_data['default_price'] != 0) and \
                            self.cleaned_data['currency'] is None:
                raise ValidationError(_("Please select currency"))
            super(ItemAdminForm, self).clean()


class ItemAdmin(tabbed_admin.TabbedModelAdmin):
    model = catalogue_models.Item
    form = ItemAdminForm
    ordering = ('id',)
    list_filter = (CreatedByItemFilter,
                   LastModifiedByItemFilter,
                   ItemSeoInformationNotRealizedLanguageFilter,
                   ItemTextNotRealizedLanguageFilter,
                   ItemNotRealizedLanguageFilter,
                   ItemByCategoryFilter,
                   ItemShortTextNotRealizedLanguageFilter)
    list_display = ('name',
                    'texts_languages_admin_display',
                    'short_texts_languages_admin_display',
                    'seo_information_languages_admin_display',
                    'check_language_admin_display',
                    'check_language_for_seo_admin_display',
                    'check_language_for_text_admin_display',
                    'check_language_for_short_text_admin_display',
                    'creating_date',
                    'author',
                    'last_modified_date',
                    'last_editor',)
    tab_overview = (
        (None, {
            'fields': ('default_language', 'url', 'code', 'default_price', 'currency', 'category', 'template')
        }),
    )
    tab_name = (
        ItemNameInline,
    )
    tab_images = (
        ItemImagePositionInline,
    )
    tab_short_text = (
        ItemShortTextInline,
    )
    tab_text = (
        ItemTextInline,
    )
    tab_parameter = (
        ItemParameterInline,
    )
    tab_seo = (
        ItemSeoInformationInline,
    )
    tab_markers = (
        (None, {
            'fields': ('new', 'top', 'stock', 'pending')
        }),
    )
    tabs = [
        (_('Overview *'), tab_overview),
        (_('Name *'), tab_name),
        (_('Images *'), tab_images),
        (_('Parameters'), tab_parameter),
        (_('Short texts'), tab_short_text),
        (_('Product texts'), tab_text),
        (_('Markers'), tab_markers),
        (_('SEO'), tab_seo),
    ]

    # search_fields = ['name', ]

    def save_model(self, request, obj, form, change) -> None:
        if change:
            date_time_user_label = catalogue_models.ItemDateTimeUserLabel.objects.filter(
                item=obj).first()
            date_time_user_label.last_modified_date = datetime.now()
            date_time_user_label.last_editor = request.user
            date_time_user_label.save()
            obj.save()
        else:
            obj.save()
            date_time_user_label = catalogue_models.ItemDateTimeUserLabel()
            date_time_user_label.creating_date = datetime.now()
            date_time_user_label.item = obj
            date_time_user_label.author = request.user
            date_time_user_label.save()
        cache.clear()
        form.save()

    actions = ['delete_model']

    def get_actions(self, request):
        actions = super(ItemAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    def delete_model(self, request, obj):
        if isinstance(obj, collections.Iterable):
            for o in obj.all():
                o.delete()
        else:
            obj.delete()

    delete_model.short_description = _('Delete')

    def save_formset(self, request, form, formset, change) -> None:
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, catalogue_models.ItemText) and instance.weight is None:
                max_weight = \
                    catalogue_models.ItemText.objects.filter(item=instance.item,
                                                             language=instance.language).all().aggregate(
                        Max('weight'))['weight__max']
                if max_weight is not None:
                    instance.weight = max_weight + 1
                else:
                    instance.weight = 0
                instance.save()
            if isinstance(instance, catalogue_models.ItemImagePosition) and instance.weight is None:
                max_weight = \
                    catalogue_models.ItemImagePosition.objects.filter(item=instance.item).all().aggregate(
                        Max('weight'))['weight__max']
                if max_weight is not None:
                    instance.weight = max_weight + 1
                else:
                    instance.weight = 0
                instance.save()
            if isinstance(instance, catalogue_models.ItemParameter) and instance.weight is None:
                max_weight = \
                    catalogue_models.ItemParameter.objects.filter(item=instance.item).all().aggregate(
                        Max('weight'))['weight__max']
                if max_weight is not None:
                    instance.weight = max_weight + 1
                else:
                    instance.weight = 0
                instance.save()
        form.save()
        formset.save()


admin.site.register(catalogue_models.CategoryTemplate)
admin.site.register(catalogue_models.Category, CategoryAdmin)
admin.site.register(catalogue_models.CategoryText, CategoryTextAdmin)
admin.register(catalogue_models.CategoryName)
admin.register(catalogue_models.CategoryDateTimeUserLabel)
admin.register(catalogue_models.CategorySeoInformation)

admin.site.register(catalogue_models.ItemTemplate)
admin.site.register(catalogue_models.Item, ItemAdmin)
admin.site.register(catalogue_models.ItemText, ItemTextAdmin)
admin.register(catalogue_models.ItemName)
admin.register(catalogue_models.ItemDateTimeUserLabel)
admin.register(catalogue_models.ItemSeoInformation)
admin.register(catalogue_models.ItemImagePosition)
admin.site.register(catalogue_models.ItemParameter, ItemParameterAdmin)
admin.register(catalogue_models.ItemParameterName)
admin.register(catalogue_models.ItemShortText)
