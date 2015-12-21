from django.contrib import admin
import info_storage.models as info_storage_models
from localization import models as localization_models
import django_mptt_admin.admin as mptt_admin
from django.utils.translation import ugettext_lazy as _
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.admin import SimpleListFilter
from django.core.cache import cache


class StorageValuesInlineFormset(forms.models.BaseInlineFormSet):
    def clean(self) -> None:
        i = 0
        for form in self.forms:
            if form.cleaned_data.__len__() != 0:
                if form.cleaned_data["default"] and not form.cleaned_data["DELETE"]:
                    i += 1
        if i == 0:
            raise ValidationError(_("Storage must have at least one default name"))
        elif i != 1:
            raise ValidationError(_("Storage must have only one default name"))


class StorageValuesInline(admin.TabularInline):
    formset = StorageValuesInlineFormset
    model = info_storage_models.StorageValue
    extra = 1


class StorageAdmin(mptt_admin.DjangoMpttAdmin):
    list_display = ('name',)
    inlines = (StorageValuesInline, )

    def save_model(self, request, obj, form, change):
        cache.clear()
        form.save()

admin.register(info_storage_models.StorageValue)
admin.site.register(info_storage_models.Storage, StorageAdmin)
