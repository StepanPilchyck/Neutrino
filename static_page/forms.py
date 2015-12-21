from django import forms
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.utils.translation import ugettext_lazy as _
from django.template.loader import get_template
from django.template import Context


class ContactUs(forms.Form):
    your_name = forms.CharField(max_length=64, widget=forms.TextInput(attrs={'placeholder': _('Name')}))
    subject = forms.CharField(max_length=128, widget=forms.TextInput(attrs={'placeholder': _('Subject')}))
    email = forms.EmailField(max_length=128, widget=forms.TextInput(attrs={'placeholder': _('E-mail')}))
    message = forms.CharField(widget=forms.Textarea(attrs={'placeholder': _('Message')}))

    def process(self) -> object:
        if self.is_valid():
            your_name = self.cleaned_data['your_name']
            subject = self.cleaned_data['subject']
            email = self.cleaned_data['email']
            message = self.cleaned_data['message']

            recipients = ['deniszorinets@gmail.com']
            if email:
                recipients.append(email)

            body = get_template('localization/contact_us.html').render(Context({
                    'name': your_name,
                    'message': message,
            }))

            send_mail(subject, body, email, recipients)

            return self, True
        else:
            return self, False
