__author__ = 'jcranwellward'


from django import forms
#from autocomplete_light import forms

from partners.models import (
    PCA,
    GwPCALocation,
    IndicatorProgress
)


# class LocationForm(forms.ModelForm):
#
#     class Media:
#         """
#         We're currently using Media here, but that forced to move the
#         javascript from the footer to the extrahead block ...
#
#         So that example might change when this situation annoys someone a lot.
#         """
#         js = ('dependant_autocomplete.js',)
#
#     class Meta:
#         model = GwPCALocation


class IndicatorAdminModelForm(forms.ModelForm):

    class Meta:
        model = IndicatorProgress

    def __init__(self, *args, **kwargs):
        super(IndicatorAdminModelForm, self).__init__(*args, **kwargs)
        self.fields['indicator'].queryset = []


class PCAForm(forms.ModelForm):

    p_codes = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = PCA
