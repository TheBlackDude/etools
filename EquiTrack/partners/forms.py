from __future__ import absolute_import

__author__ = 'jcranwellward'

import pandas

from django import forms
from django.forms.models import BaseInlineFormSet
from django.contrib import messages
#from autocomplete_light import forms
from django.core.exceptions import (
    ValidationError,
    ObjectDoesNotExist,
    MultipleObjectsReturned,
)

from suit.widgets import AutosizedTextarea

from locations.models import Location
from reports.models import Sector, Result, Indicator
from .models import (
    PCA,
    GwPCALocation,
    ResultChain,
    IndicatorProgress,
    AmendmentLog
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


class ParentInlineAdminFormSet(BaseInlineFormSet):
    """
    Passes the parent instance to the form constructor for easy
    access by child inline forms to use for conditional filtering
    """
    def _construct_form(self, i, **kwargs):
        kwargs['parent_object'] = self.instance
        return super(ParentInlineAdminFormSet, self)._construct_form(i, **kwargs)


class ResultChainAdminForm(forms.ModelForm):

    class Meta:
        model = ResultChain

    def __init__(self, *args, **kwargs):
        """
        Filter linked results by sector and result structure
        """
        if 'parent_object' in kwargs:
            self.parent_partnership = kwargs.pop('parent_object')

        super(ResultChainAdminForm, self).__init__(*args, **kwargs)

        if hasattr(self, 'parent_partnership'):

            results = Result.objects.filter(
                result_structure=self.parent_partnership.result_structure
            )
            indicators = Indicator.objects.filter(
                result_structure=self.parent_partnership.result_structure
            )
            for sector in self.parent_partnership.sector_children:
                results = results.filter(sector=sector)
                indicators = indicators.filter(sector=sector)

            if self.instance.result_id:
                self.fields['result'].queryset = results.filter(id=self.instance.result_id)
                self.fields['indicator'].queryset = indicators.filter(result_id=self.instance.result_id)


class AmendmentForm(forms.ModelForm):

    class Meta:
        model = AmendmentLog

    def __init__(self, *args, **kwargs):
        """
        Only display the amendments related to this partnership
        """
        if 'parent_object' in kwargs:
            self.parent_partnership = kwargs.pop('parent_object')

        super(AmendmentForm, self).__init__(*args, **kwargs)

        self.fields['amendment'].queryset = self.parent_partnership.amendments_list \
            if hasattr(self, 'parent_partnership') else AmendmentLog.objects.none()


class PCAForm(forms.ModelForm):

    # fields needed to assign locations from p_codes
    p_codes = forms.CharField(widget=forms.Textarea, required=False)
    location_sector = forms.ModelChoiceField(
        required=False,
        queryset=Sector.objects.all()
    )

    # fields needed to import log frames/work plans from excel
    work_plan = forms.FileField(required=False)
    work_plan_sector = forms.ModelChoiceField(
        required=False,
        queryset=Sector.objects.all()
    )

    class Meta:
        model = PCA
        widgets = {
            'title':
                AutosizedTextarea(attrs={'class': 'input-xlarge'}),
        }

    def add_locations(self, p_codes, sector):
        """
        Adds locations to the partnership based
        on the passed in list and the relevant sector
        """
        p_codes_list = p_codes.split()
        created, notfound = 0, 0
        for p_code in p_codes_list:
            try:
                location = Location.objects.get(
                    p_code=p_code
                )
                loc, new = GwPCALocation.objects.get_or_create(
                    sector=sector,
                    governorate=location.locality.region.governorate,
                    region=location.locality.region,
                    locality=location.locality,
                    location=location,
                    pca=self.obj
                )
                if new:
                    created += 1
            except Location.DoesNotExist:
                notfound += 1

        messages.info(
            self.request,
            u'Assigned {} locations, {} were not found'.format(
                created, notfound
            ))

    def import_results_from_work_plan(self, work_plan, sector):
        """
        Matches results from the work plan to country result structure.
        Will try to match indicators one to one or by name, this can be ran
        multiple times to continually update the work plan
        """
        try:  # first try to grab the excel as a table...
            data = pandas.read_excel(work_plan, index_col=0)
        except Exception as exp:
            raise ValidationError(exp.message)

        imported = found = not_found = 0
        for code, row in data.iterrows():
            create_args = dict(
                partnership=self.obj
            )
            try:
                result = Result.objects.get(
                    sector=sector,
                    code=code
                )
                create_args['result'] = result
                create_args['result_type'] = result.result_type
                indicators = result.indicator_set.all()
                if indicators:
                    if indicators.count() == 1:
                        # use this indicator if we only have one
                        create_args['indicator'] = indicators[0]
                    else:
                        # attempt to fuzzy match by name
                        candidates = indicators.filter(
                            name__icontains=row['Indicator']
                        )
                        if candidates:
                            create_args['indicator'] = candidates[0]
                    # if we got this far also take the target
                    create_args['target'] = row.get('Target')
            except (ObjectDoesNotExist, MultipleObjectsReturned) as exp:
                not_found += 1
                #TODO: Log this
            else:
                result_chain, new = ResultChain.objects.get_or_create(**create_args)
                if new:
                    imported += 1
                else:
                    found += 1

        messages.info(
            self.request,
            u'Imported {} results, {} were imported already and {} were not found'.format(
                imported, found, not_found
            ))

    def clean(self):
        """
        Add elements to the partnership based on imports
        """
        cleaned_data = super(PCAForm, self).clean()

        partnership_type = cleaned_data[u'partnership_type']
        agreement = cleaned_data[u'agreement']
        p_codes =cleaned_data[u'p_codes']
        location_sector = cleaned_data[u'location_sector']

        work_plan = self.cleaned_data[u'work_plan']
        work_plan_sector = self.cleaned_data[u'work_plan_sector']

        if partnership_type == PCA.PD and not agreement:
            raise ValidationError(
                u'Please select the PCA agreement this Programme Document relates to'
            )

        if p_codes and not location_sector:
            raise ValidationError(
                u'Please select a sector to assign the locations against'
            )

        if p_codes and location_sector:
            self.add_locations(p_codes, location_sector)

        if work_plan and not work_plan_sector:
            raise ValidationError(
                u'Please select a sector to import results against'
            )

        if work_plan and work_plan_sector:
            self.import_results_from_work_plan(work_plan, work_plan_sector)

        return cleaned_data
