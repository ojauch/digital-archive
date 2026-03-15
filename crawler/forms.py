from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext as _

from .models import BrowserProfile, Crawl


class BrowserProfileCreateForm(forms.ModelForm):
    profile_file = forms.FileField(
        label=_("Profile File"),
        validators=[FileExtensionValidator(["gz"])],
        widget=forms.FileInput(attrs={"accept": ".tar.gz"}),
    )

    class Meta:
        model = BrowserProfile
        fields = ["name", "description"]


class CrawlFilterForm(forms.Form):
    query = forms.CharField(required=False, label=_("Search Query"))
    status = forms.ChoiceField(
        choices=((None, "-"),) + Crawl.CRAWL_STATUS_CHOICES,
        required=False,
        label=_("Status"),
    )
    date_from = forms.DateField(
        required=False,
        label=_("From Date"),
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    date_to = forms.DateField(
        required=False,
        label=_("To Date"),
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "get"
        self.helper.form_class = (
            "row row-cols-lg-auto g-3 align-items-end justify-content-end"
        )
        self.helper.add_input(Submit("submit", "Filter"))
