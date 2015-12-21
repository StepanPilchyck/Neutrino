from django.contrib import admin
from menu import models as menu_models
from localization import models as localization_models
import django_mptt_admin.admin as mptt_admin
from django.utils.translation import ugettext_lazy as _
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.admin import SimpleListFilter
from django.core.cache import cache


class MainMenuItemNamesInlineFormset(forms.models.BaseInlineFormSet):
    def clean(self) -> None:
        i = 0
        for form in self.forms:
            if form.cleaned_data.__len__() != 0:
                if form.cleaned_data["default"] and not form.cleaned_data["DELETE"]:
                    i += 1
        if i == 0:
            raise ValidationError(_("Menu item must have at least one default  name"))
        elif i != 1:
            raise ValidationError(_("Menu item must have only one default name"))


class MainMenuItemNamesInline(admin.TabularInline):
    formset = MainMenuItemNamesInlineFormset
    model = menu_models.MainMenuItemName
    extra = 1


class MainMenuTextDataNotRealizedLanguageFilter(SimpleListFilter):
    title = _('Realized Text Data')

    parameter_name = 'text_data_lang'

    def lookups(self, request, model_admin) -> [(int, str)]:
        languages = localization_models.Language.objects.all().values_list('id', 'name')
        lookup = [('True', 'Has no unrealized languages'), ('False', 'Has unrealized languages')]
        for lang_id, name in languages:
            lookup.append((lang_id, name))
        return lookup

    def queryset(self, request, queryset) -> [menu_models.MainMenu]:
        if self.value() is None:
            return queryset
        result = []
        if self.value() == 'True':
            for menu_item in queryset:
                if menu_item.check_language_for_name:
                    result.append(menu_item.id)
        elif self.value() == 'False':
            for menu_item in queryset:
                if not menu_item.check_language_for_name:
                    result.append(menu_item.id)
        else:
            language = localization_models.Language.objects.filter(pk=self.value()).values_list('id', flat=True)
            if language.__len__() > 0:
                language = language[0]
                for menu_item in queryset:
                    if language not in menu_item.name_languages_ids:
                        result.append(menu_item.id)
        return queryset.filter(id__in=result)


class MainMenuAdmin(mptt_admin.DjangoMpttAdmin):
    list_display = ('name', 'check_language_for_name_admin_display',)
    list_filter = (MainMenuTextDataNotRealizedLanguageFilter, )
    inlines = (MainMenuItemNamesInline, )

    def save_model(self, request, obj, form, change):
        cache.clear()
        form.save()



class AdditionalMenuItemNamesInlineFormset(forms.models.BaseInlineFormSet):
    def clean(self) -> None:
        i = 0
        for form in self.forms:
            if form.cleaned_data.__len__() != 0:
                if form.cleaned_data["default"] and not form.cleaned_data["DELETE"]:
                    i += 1
        if i == 0:
            raise ValidationError(_("Menu item must have at least one default name"))
        elif i != 1:
            raise ValidationError(_("Menu item must have only one default name"))


class AdditionalMenuItemNamesInline(admin.TabularInline):
    formset = AdditionalMenuItemNamesInlineFormset
    model = menu_models.AdditionalMenuItemName
    extra = 1


class AdditionalMenuTextDataNotRealizedLanguageFilter(SimpleListFilter):
    title = _('Realized Text Data')

    parameter_name = 'text_data_lang'

    def lookups(self, request, model_admin) -> [(int, str)]:
        languages = localization_models.Language.objects.all().values_list('id', 'name')
        lookup = [('True', 'Has no unrealized languages'), ('False', 'Has unrealized languages')]
        for lang_id, name in languages:
            lookup.append((lang_id, name))
        return lookup

    def queryset(self, request, queryset) -> [menu_models.AdditionalMenu]:
        if self.value() is None:
            return queryset
        result = []
        if self.value() == 'True':
            for menu_item in queryset:
                if menu_item.check_language_for_name:
                    result.append(menu_item.id)
        elif self.value() == 'False':
            for menu_item in queryset:
                if not menu_item.check_language_for_name:
                    result.append(menu_item.id)
        else:
            language = localization_models.Language.objects.filter(pk=self.value()).values_list('id', flat=True)
            if language.__len__() > 0:
                language = language[0]
                for menu_item in queryset:
                    if language not in menu_item.name_languages_ids:
                        result.append(menu_item.id)
        return queryset.filter(id__in=result)


class AdditionalMenuAdmin(mptt_admin.DjangoMpttAdmin):
    list_display = ('name', 'check_language_for_name_admin_display',)
    list_filter = (AdditionalMenuTextDataNotRealizedLanguageFilter, )
    inlines = (AdditionalMenuItemNamesInline, )

    def save_model(self, request, obj, form, change):
        cache.clear()
        form.save()


class ExtraMenuItemNamesInlineFormset(forms.models.BaseInlineFormSet):
    def clean(self) -> None:
        i = 0
        for form in self.forms:
            if form.cleaned_data.__len__() != 0:
                if form.cleaned_data["default"] and not form.cleaned_data["DELETE"]:
                    i += 1
        if i == 0:
            raise ValidationError(_("Menu item must have at least one default name"))
        elif i != 1:
            raise ValidationError(_("Menu item must have only one default name"))


class ExtraMenuItemNamesInline(admin.TabularInline):
    formset = ExtraMenuItemNamesInlineFormset
    model = menu_models.ExtraMenuItemName
    extra = 1


class ExtraMenuTextDataNotRealizedLanguageFilter(SimpleListFilter):
    title = _('Realized Text Data')

    parameter_name = 'text_data_lang'

    def lookups(self, request, model_admin) -> [(int, str)]:
        languages = localization_models.Language.objects.all().values_list('id', 'name')
        lookup = [('True', 'Has no unrealized languages'), ('False', 'Has unrealized languages')]
        for lang_id, name in languages:
            lookup.append((lang_id, name))
        return lookup

    def queryset(self, request, queryset) -> [menu_models.ExtraMenu]:
        if self.value() is None:
            return queryset
        result = []
        if self.value() == 'True':
            for menu_item in queryset:
                if menu_item.check_language_for_name:
                    result.append(menu_item.id)
        elif self.value() == 'False':
            for menu_item in queryset:
                if not menu_item.check_language_for_name:
                    result.append(menu_item.id)
        else:
            language = localization_models.Language.objects.filter(pk=self.value()).values_list('id', flat=True)
            if language.__len__() > 0:
                language = language[0]
                for menu_item in queryset:
                    if language not in menu_item.name_languages_ids:
                        result.append(menu_item.id)
        return queryset.filter(id__in=result)


class ExtraMenuAdmin(mptt_admin.DjangoMpttAdmin):
    list_display = ('name', 'check_language_for_name_admin_display',)
    list_filter = (ExtraMenuTextDataNotRealizedLanguageFilter, )
    inlines = (ExtraMenuItemNamesInline, )

    def save_model(self, request, obj, form, change):
        cache.clear()
        form.save()


admin.site.register(menu_models.MainMenu, MainMenuAdmin)
admin.site.register(menu_models.ExtraMenu, ExtraMenuAdmin)
admin.site.register(menu_models.AdditionalMenu, AdditionalMenuAdmin)

admin.register(menu_models.MainMenuItemName)
