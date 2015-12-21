from datetime import datetime
from django.contrib import admin
from django.db.models import Max
from django.contrib.auth import models as auth_models
from localization import models as localization_models
import banner.models as banner_models
import image_cropping
from django.utils.translation import ugettext_lazy as _
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.admin import SimpleListFilter
import collections


# TODO Optimize this
class BannerImagePositionFilter(SimpleListFilter):
    title = _('Banner')

    parameter_name = 'banner'

    def lookups(self, request, model_admin) -> [(str, str)]:
        banners = banner_models.Banner.objects.filter().all()
        lookup = []
        for banner in banners:
            if (banner.id, banner.name) not in lookup:
                lookup.append((banner.id, banner.name))
        return lookup

    def queryset(self, request, queryset) -> [banner_models.BannerImagePosition]:
        if self.value() is None:
            return queryset
        return queryset.filter(banner=banner_models.Banner.objects.filter(id=self.value()).first())


class BannerImagePositionTextDataNotRealizedLanguageFilter(SimpleListFilter):
    title = _('Realized Text Data')

    parameter_name = 'text_data_lang'

    def lookups(self, request, model_admin) -> [(int, str)]:
        languages = localization_models.Language.objects.all().values_list('id', 'name')
        lookup = [('True', 'Has no unrealized languages'), ('False', 'Has unrealized languages')]
        for lang_id, name in languages:
            lookup.append((lang_id, name))
        return lookup

    def queryset(self, request, queryset) -> [banner_models.BannerImagePosition]:
        if self.value() is None:
            return queryset
        result = []
        if self.value() == 'True':
            for banner_image_position in queryset:
                if banner_image_position.check_language_for_text_data:
                    result.append(banner_image_position.id)
        elif self.value() == 'False':
            for banner_image_position in queryset:
                if not banner_image_position.check_language_for_text_data:
                    result.append(banner_image_position.id)
        else:
            language = localization_models.Language.objects.filter(pk=self.value()).all().values_list('id',
                                                                                                          flat=True)
            if language.__len__() > 0:
                language = language[0]
                for banner_image_position in queryset:
                    if language not in banner_image_position.text_data_languages_ids and \
                                    banner_image_position.text_data_languages_ids.__len__() > 0:
                        result.append(banner_image_position.id)
        return queryset.filter(id__in=result)


# BannerImagePosition
class BannerImagePositionTextDataInlineFormset(forms.models.BaseInlineFormSet):
    def clean(self) -> None:
        i = 0
        j = 0
        for form in self.forms:
            if form.cleaned_data.__len__() != 0:
                if form.cleaned_data["default"]:
                    i += 1
                if form.cleaned_data["name"]:
                    j += 1
        if j != 0 and i == 0:
            raise ValidationError(_("Image item must have at least one default name"))
        if j != 0 and i != 1:
            raise ValidationError(_("Image item must have only one default name"))


class BannerImagePositionTextDataInline(admin.TabularInline):
    formset = BannerImagePositionTextDataInlineFormset
    model = banner_models.BannerImagePositionTextData
    ordering = ('name', 'language',)
    extra = 1


class BannerImagePositionAdmin(image_cropping.ImageCroppingMixin, admin.ModelAdmin):
    inlines = (BannerImagePositionTextDataInline,)
    ordering = ('id',)
    list_filter = (BannerImagePositionFilter,
                   BannerImagePositionTextDataNotRealizedLanguageFilter)
    list_display = ('id',
                    'name',
                    'check_language_for_text_data_admin_display',
                    'original_image_admin_display',
                    'large_image_admin_display',
                    'medium_image_admin_display',
                    'small_image_admin_display',)

    def save_model(self, request, obj, form, change: bool) -> None:
        if obj.weight is None:
            max_weight = \
                banner_models.BannerImagePosition.objects.filter(banner=obj.banner).all().aggregate(
                    Max('weight'))['weight__max']
            if max_weight:
                obj.weight = max_weight + 1
            else:
                obj.weight = 0
        form.save()

    actions = ['delete_model']

    def get_actions(self, request):
        actions = super(BannerImagePositionAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    def delete_model(self, request, obj):
        if isinstance(obj, collections.Iterable):
            for o in obj.all():
                o.delete()
        else:
            obj.delete()

    delete_model.short_description = _('Delete')


class BannerImagePositionInline(admin.TabularInline):
    model = banner_models.BannerImagePosition
    ordering = ('weight',)
    extra = 0
    show_change_link = True

    def formfield_for_dbfield(self, db_field, **kwargs):
        crop_fields = getattr(self.model, 'crop_fields', {})
        if db_field.name in crop_fields:
            kwargs['widget'] = image_cropping.ImageCropWidget

        return super(BannerImagePositionInline, self).formfield_for_dbfield(db_field, **kwargs)


# Banner Filters
class CreatedByBannerFilter(SimpleListFilter):
    title = _('Author')

    parameter_name = 'author'

    def lookups(self, request, model_admin) -> [(int, str)]:
        labels = banner_models.BannerDateTimeUserLabel.objects.all().values_list('author__id', 'author__username')
        lookup = []
        for author_id, author in labels:
            if (author_id, author) not in lookup:
                lookup.append((author_id, author))
        return lookup

    def queryset(self, request, queryset) -> [banner_models.Banner]:
        if self.value() is not None:
            banners = banner_models.BannerDateTimeUserLabel.objects.filter(
                author=auth_models.User.objects.filter(pk=self.value()).first().id).all().values_list('banner__id',
                                                                                                      flat=True)
        else:
            banners = banner_models.BannerDateTimeUserLabel.objects.all().values_list('banner__id', flat=True)
        return queryset.filter(id__in=banners)


class LastModifiedByBannerFilter(SimpleListFilter):
    title = _('Last editor')

    parameter_name = 'last_editor'

    def lookups(self, request, model_admin) -> [(int, str)]:
        labels = banner_models.BannerDateTimeUserLabel.objects.all().values_list('last_editor__id',
                                                                                          'last_editor__username')
        lookup = [('None', _('None')), ]
        for editor_id, editor in labels:
            if ((editor_id, editor) not in lookup) and editor is not None:
                lookup.append((editor_id, editor))
        return lookup

    def queryset(self, request, queryset) -> [banner_models.Banner]:
        if self.value() == 'None':
            banners = banner_models.BannerDateTimeUserLabel.objects.filter(last_editor=None).all().values_list(
                'banner__id', flat=True)
        elif self.value() is not None:
            banners = banner_models.BannerDateTimeUserLabel.objects.filter(
                author=auth_models.User.objects.filter(pk=self.value()).first().id).all().values_list('banner__id',
                                                                                                      flat=True)
        else:
            banners = banner_models.BannerDateTimeUserLabel.objects.all().values_list('banner__id', flat=True)
        return queryset.filter(id__in=banners)


class BannerTextDataNotRealizedLanguageFilter(SimpleListFilter):
    title = _('Not realized Text Data')

    parameter_name = 'text_data_lang'


    def lookups(self, request, model_admin) -> [(int, str)]:
        languages = localization_models.Language.objects.all().values_list('id', 'name')
        lookup = [('True', 'Has no unrealized languages'), ('False', 'Has unrealized languages')]
        for language_id, language_name in languages:
            lookup.append((language_id, language_name))
        return lookup

    def queryset(self, request, queryset) -> [banner_models.Banner]:
        if self.value() is None:
            return queryset
        result = []
        if self.value() == 'True':
            for banner in queryset:
                if banner.check_language_for_text_data:
                    result.append(banner.id)
        elif self.value() == 'False':
            for banner in queryset:
                if not banner.check_language_for_text_data:
                    result.append(banner.id)
        else:
            language = localization_models.Language.objects.filter(pk=self.value()).all().values_list('id', flat=True)
            if language.__len__() > 0:
                language = language[0]
                for banner in queryset:
                    if language not in banner.text_data_languages_ids:
                        result.append(banner.id)
        return queryset.filter(id__in=result)


# Banner
class BannerTextDataInlineFormset(forms.models.BaseInlineFormSet):
    def clean(self) -> None:
        i = 0
        print(self.forms)
        for form in self.forms:
            if form.cleaned_data.__len__() != 0:
                if form.cleaned_data["default"] and not form.cleaned_data["DELETE"]:
                    i += 1
        if i == 0:
            raise ValidationError(_("Banner must have at least one default name"))
        elif i != 1:
            raise ValidationError(_("Banner must have only one default name"))


class BannerTextDataInline(admin.TabularInline):
    formset = BannerTextDataInlineFormset
    model = banner_models.BannerTextData
    ordering = ('name', 'language',)
    extra = 1


class BannerAdmin(admin.ModelAdmin):
    inlines = (BannerImagePositionInline, BannerTextDataInline)
    ordering = ('id',)
    list_filter = (CreatedByBannerFilter,
                   LastModifiedByBannerFilter,
                   BannerTextDataNotRealizedLanguageFilter,)
    list_display = ('id',
                    'name',
                    'check_language_for_text_data_admin_display',
                    'creating_date',
                    'author',
                    'last_modified_date',
                    'last_editor',)

    def save_model(self, request, obj, form, change: bool) -> None:
        if change:
            date_time_user_label = banner_models.BannerDateTimeUserLabel.objects.filter(banner=obj).first()
            date_time_user_label.last_modified_date = datetime.now()
            date_time_user_label.last_editor = request.user
            date_time_user_label.save()
            obj.save()
        else:
            obj.save()
            date_time_user_label = banner_models.BannerDateTimeUserLabel()
            date_time_user_label.creating_date = datetime.now()
            date_time_user_label.banner = obj
            date_time_user_label.author = request.user
            date_time_user_label.save()
        form.save()

    def get_actions(self, request):
        actions = super(BannerAdmin, self).get_actions(request)
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
            if isinstance(instance, banner_models.BannerImagePosition) and instance.weight is None:
                max_weight = \
                    banner_models.BannerImagePosition.objects.filter(banner=instance.banner).all().aggregate(
                        Max('weight'))['weight__max']
                if max_weight is not None:
                    instance.weight = max_weight + 1
                else:
                    instance.weight = 0
                instance.save()
        form.save()
        formset.save()


admin.site.register(banner_models.Banner, BannerAdmin)
admin.site.register(banner_models.BannerImagePosition, BannerImagePositionAdmin)
