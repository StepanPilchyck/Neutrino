from django.contrib import admin
from django import forms
import localization.models as localization_models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


class CurrencyAdminForm(forms.ModelForm):
    class Meta:
        model = localization_models.Currency
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(CurrencyAdminForm, self).__init__(*args, **kwargs)

    def clean(self):
        if self.cleaned_data.__len__() != 0:
            count = localization_models.Currency.objects.filter(default=True).count()
            if count == 0 and self.cleaned_data['default'] == False:
                raise ValidationError(_("At least one default currency needed"))
            elif count > 0 and self.cleaned_data['default'] == True:
                raise ValidationError(_("Only one default currency needed"))


class CurrencyAdmin(admin.ModelAdmin):
    form = CurrencyAdminForm


admin.site.register(localization_models.Language)
admin.site.register(localization_models.Currency, CurrencyAdmin)
