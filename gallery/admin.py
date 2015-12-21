from datetime import datetime
from django.contrib import admin
from django.db.models import Max
from django.contrib.auth import models as auth_models
from localization import models as localization_models
import gallery.models as gallery_models
import image_cropping
from django.utils.translation import ugettext_lazy as _
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.admin import SimpleListFilter
import collections


# Gallery Image Position Filters
# TODO Optimize this
class GalleryImagePositionFilter(SimpleListFilter):
    title = _('Gallery')

    parameter_name = 'gallery'

    def lookups(self, request, model_admin) -> [(str, str)]:
        galleries = gallery_models.Gallery.objects.filter().all()
        lookup = []
        for gallery in galleries:
            if (gallery.id, gallery.name) not in lookup:
                lookup.append((gallery.id, gallery.name))
        return lookup

    def queryset(self, request, queryset) -> [gallery_models.GalleryImagePosition]:
        if self.value() is None:
            return queryset
        return queryset.filter(gallery=gallery_models.Gallery.objects.filter(id=self.value()).first())


class GalleryImagePositionTextDataNotRealizedLanguageFilter(SimpleListFilter):
    title = _('Realized Text Data')

    parameter_name = 'text_data_lang'

    def lookups(self, request, model_admin) -> [(int, str)]:
        languages = localization_models.Language.objects.all().values_list('id', 'name')
        lookup = [('True', 'Has no unrealized languages'), ('False', 'Has unrealized languages')]
        for lang_id, name in languages:
            lookup.append((lang_id, name))
        return lookup

    def queryset(self, request, queryset) -> [gallery_models.GalleryImagePosition]:
        if self.value() is None:
            return queryset
        result = []
        if self.value() == 'True':
            for gallery_image_position in queryset:
                if gallery_image_position.check_language_for_text_data:
                    result.append(gallery_image_position.id)
        elif self.value() == 'False':
            for gallery_image_position in queryset:
                if not gallery_image_position.check_language_for_text_data:
                    result.append(gallery_image_position.id)
        else:
            language = localization_models.Language.objects.filter(pk=self.value()).all().values_list('id',
                                                                                                          flat=True)
            if language.__len__() > 0:
                language = language[0]
                for gallery_image_position in queryset:
                    if language not in gallery_image_position.text_data_languages_ids and \
                                    gallery_image_position.text_data_languages_ids.__len__() > 0:
                        result.append(gallery_image_position.id)
        return queryset.filter(id__in=result)


# GalleryImagePosition
class GalleryImagePositionTextDataInlineFormset(forms.models.BaseInlineFormSet):
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


class GalleryImagePositionTextDataInline(admin.TabularInline):
    formset = GalleryImagePositionTextDataInlineFormset
    model = gallery_models.GalleryImagePositionTextData
    ordering = ('name', 'language',)
    extra = 1


class GalleryImagePositionAdmin(image_cropping.ImageCroppingMixin, admin.ModelAdmin):
    inlines = (GalleryImagePositionTextDataInline,)
    ordering = ('id',)
    list_filter = (GalleryImagePositionFilter, GalleryImagePositionTextDataNotRealizedLanguageFilter,)
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
                gallery_models.GalleryImagePosition.objects.filter(gallery=obj.gallery).all().aggregate(
                    Max('weight'))['weight__max']
            if max_weight:
                obj.weight = max_weight + 1
            else:
                obj.weight = 0
        form.save()

    actions = ['delete_model']

    def get_actions(self, request):
        actions = super(GalleryImagePositionAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    def delete_model(self, request, obj):
        if isinstance(obj, collections.Iterable):
            for o in obj.all():
                o.delete()
        else:
            obj.delete()

    delete_model.short_description = _('Delete')


class GalleryImagePositionInline(admin.TabularInline):
    model = gallery_models.GalleryImagePosition
    ordering = ('weight',)
    extra = 0
    show_change_link = True

    def formfield_for_dbfield(self, db_field, **kwargs):
        crop_fields = getattr(self.model, 'crop_fields', {})
        if db_field.name in crop_fields:
            kwargs['widget'] = image_cropping.ImageCropWidget

        return super(GalleryImagePositionInline, self).formfield_for_dbfield(db_field, **kwargs)


# Gallery Filters
class CreatedByGalleryFilter(SimpleListFilter):
    title = _('Author')

    parameter_name = 'author'

    def lookups(self, request, model_admin) -> [(int, str)]:
        labels = gallery_models.GalleryDateTimeUserLabel.objects.all().values_list('author__id', 'author__username')
        lookup = []
        for author_id, author in labels:
            if (author_id, author) not in lookup:
                lookup.append((author_id, author))
        return lookup

    def queryset(self, request, queryset) -> [gallery_models.Gallery]:
        if self.value() is not None:
            galleries = gallery_models.GalleryDateTimeUserLabel.objects.filter(
                author=auth_models.User.objects.filter(pk=self.value()).first().id).all().values_list('gallery__id',
                                                                                                      flat=True)
        else:
            galleries = gallery_models.GalleryDateTimeUserLabel.objects.all().values_list('gallery__id', flat=True)
        return queryset.filter(id__in=galleries)


class LastModifiedByGalleryFilter(SimpleListFilter):
    title = _('Last editor')

    parameter_name = 'last_editor'

    def lookups(self, request, model_admin) -> [(int, str)]:
        labels = gallery_models.GalleryDateTimeUserLabel.objects.all().values_list('last_editor__id',
                                                                                          'last_editor__username')
        lookup = [('None', _('None')), ]
        for editor_id, editor in labels:
            if ((editor_id, editor) not in lookup) and editor is not None:
                lookup.append((editor_id, editor))
        return lookup

    def queryset(self, request, queryset) -> [gallery_models.Gallery]:
        if self.value() == 'None':
            galleries = gallery_models.GalleryDateTimeUserLabel.objects.filter(last_editor=None).all().values_list(
                'gallery__id', flat=True)
        elif self.value() is not None:
            galleries = gallery_models.GalleryDateTimeUserLabel.objects.filter(
                author=auth_models.User.objects.filter(pk=self.value()).first().id).all().values_list('gallery__id',
                                                                                                      flat=True)
        else:
            galleries = gallery_models.GalleryDateTimeUserLabel.objects.all().values_list('gallery__id', flat=True)
        return queryset.filter(id__in=galleries)


class GalleryTextDataNotRealizedLanguageFilter(SimpleListFilter):
    title = _('Realized Text Data')

    parameter_name = 'text_data_lang'

    def lookups(self, request, model_admin) -> [(int, str)]:
        languages = localization_models.Language.objects.all().values_list('id', 'name')
        lookup = [('True', 'Has no unrealized languages'), ('False', 'Has unrealized languages')]
        for language_id, language_name in languages:
            lookup.append((language_id, language_name))
        return lookup

    def queryset(self, request, queryset) -> [gallery_models.Gallery]:
        if self.value() is None:
            return queryset
        result = []
        if self.value() == 'True':
            for gallery in queryset:
                if gallery.check_language_for_text_data:
                    result.append(gallery.id)
        elif self.value() == 'False':
            for gallery in queryset:
                if not gallery.check_language_for_text_data:
                    result.append(gallery.id)
        else:
            language = localization_models.Language.objects.filter(pk=self.value()).all().values_list('id', flat=True)
            if language.__len__() > 0:
                language = language[0]
                for gallery in queryset:
                    if language not in gallery.text_data_languages_ids:
                        result.append(gallery.id)
        return queryset.filter(id__in=result)


# Gallery
class GalleryTextDataInlineFormset(forms.models.BaseInlineFormSet):
    def clean(self) -> None:
        i = 0
        for form in self.forms:
            if form.cleaned_data.__len__() != 0:
                if form.cleaned_data["default"] and not form.cleaned_data["DELETE"]:
                    i += 1
        if i == 0:
            raise ValidationError(_("Gallery must have at least one default name"))
        elif i != 1:
            raise ValidationError(_("Gallery must have only one default name"))


class GalleryTextDataInline(admin.TabularInline):
    formset = GalleryTextDataInlineFormset
    model = gallery_models.GalleryTextData
    ordering = ('name', 'language',)
    extra = 1


class GalleryAdmin(admin.ModelAdmin):
    inlines = (GalleryImagePositionInline, GalleryTextDataInline)
    ordering = ('id',)
    list_filter = (CreatedByGalleryFilter,
                   LastModifiedByGalleryFilter,
                   GalleryTextDataNotRealizedLanguageFilter,)
    list_display = ('id',
                    'name',
                    'check_language_for_text_data_admin_display',
                    'first_image_admin_display',
                    'second_image_admin_display',
                    'creating_date',
                    'author',
                    'last_modified_date',
                    'last_editor',)

    def save_model(self, request, obj, form, change: bool) -> None:
        if change:
            date_time_user_label = gallery_models.GalleryDateTimeUserLabel.objects.filter(gallery=obj).first()
            date_time_user_label.last_modified_date = datetime.now()
            date_time_user_label.last_editor = request.user
            date_time_user_label.save()
            obj.save()
        else:
            obj.save()
            date_time_user_label = gallery_models.GalleryDateTimeUserLabel()
            date_time_user_label.creating_date = datetime.now()
            date_time_user_label.gallery = obj
            date_time_user_label.author = request.user
            date_time_user_label.save()
        form.save()

    actions = ['delete_model']

    def get_actions(self, request):
        actions = super(GalleryAdmin, self).get_actions(request)
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
            if isinstance(instance, gallery_models.GalleryImagePosition) and instance.weight is None:
                max_weight = \
                    gallery_models.GalleryImagePosition.objects.filter(gallery=instance.gallery).all().aggregate(
                        Max('weight'))['weight__max']
                if max_weight is not None:
                    instance.weight = max_weight + 1
                else:
                    instance.weight = 0
                instance.save()
        form.save()
        formset.save()


admin.site.register(gallery_models.Gallery, GalleryAdmin)
admin.site.register(gallery_models.GalleryImagePosition, GalleryImagePositionAdmin)
