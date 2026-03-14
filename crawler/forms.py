from django import forms
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext as _

from .models import BrowserProfile


class BrowserProfileCreateForm(forms.ModelForm):
    profile_file = forms.FileField(
        label=_("Profile File"),
        validators=[FileExtensionValidator(["gz"])],
        widget=forms.FileInput(attrs={"accept": ".tar.gz"}),
    )

    class Meta:
        model = BrowserProfile
        fields = ["name", "description"]
