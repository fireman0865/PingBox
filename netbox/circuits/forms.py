from django import forms
from taggit.forms import TagField

from dcim.models import Region, Site
from extras.forms import (
    AddRemoveTagsForm, CustomFieldBulkEditForm, CustomFieldFilterForm, CustomFieldModelForm, CustomFieldModelCSVForm,
)
from tenancy.forms import TenancyFilterForm, TenancyForm
from tenancy.models import Tenant
from utilities.forms import (
    APISelect, APISelectMultiple, add_blank_choice, BootstrapMixin, CommentField, CSVChoiceField, DatePicker,
    DynamicModelChoiceField, DynamicModelMultipleChoiceField, SmallTextarea, SlugField, StaticSelect2,
    StaticSelect2Multiple, TagFilterField,
)
from .choices import CircuitStatusChoices
from .models import Circuit, CircuitTermination, CircuitType, Provider


#
# Providers
#

class ProviderForm(BootstrapMixin, CustomFieldModelForm):
    slug = SlugField()
    comments = CommentField()
    tags = TagField(
        required=False
    )

    class Meta:
        model = Provider
        fields = [
            'name', 'slug', 'asn', 'account', 'portal_url', 'noc_contact', 'admin_contact', 'comments', 'tags',
        ]
        widgets = {
            'noc_contact': SmallTextarea(
                attrs={'rows': 5}
            ),
            'admin_contact': SmallTextarea(
                attrs={'rows': 5}
            ),
        }
        help_texts = {
            'name': "Full name of the provider",
            'asn': "BGP autonomous system number (if applicable)",
            'portal_url': "URL of the provider's customer support portal",
            'noc_contact': "NOC email address and phone number",
            'admin_contact': "Administrative contact email address and phone number",
        }


class ProviderCSVForm(CustomFieldModelCSVForm):
    slug = SlugField()

    class Meta:
        model = Provider
        fields = Provider.csv_headers
        help_texts = {
            'name': 'Provider name',
            'asn': '32-bit autonomous system number',
            'portal_url': 'Portal URL',
            'comments': 'Free-form comments',
        }


class ProviderBulkEditForm(BootstrapMixin, AddRemoveTagsForm, CustomFieldBulkEditForm):
    pk = forms.ModelMultipleChoiceField(
        queryset=Provider.objects.all(),
        widget=forms.MultipleHiddenInput
    )
    asn = forms.IntegerField(
        required=False,
        label='ASN'
    )
    account = forms.CharField(
        max_length=30,
        required=False,
        label='Account number'
    )
    portal_url = forms.URLField(
        required=False,
        label='Portal'
    )
    noc_contact = forms.CharField(
        required=False,
        widget=SmallTextarea,
        label='NOC contact'
    )
    admin_contact = forms.CharField(
        required=False,
        widget=SmallTextarea,
        label='Admin contact'
    )
    comments = CommentField(
        widget=SmallTextarea,
        label='Comments'
    )

    class Meta:
        nullable_fields = [
            'asn', 'account', 'portal_url', 'noc_contact', 'admin_contact', 'comments',
        ]


class ProviderFilterForm(BootstrapMixin, CustomFieldFilterForm):
    model = Provider
    q = forms.CharField(
        required=False,
        label='Search'
    )
    region = DynamicModelMultipleChoiceField(
        queryset=Region.objects.all(),
        to_field_name='slug',
        required=False,
        widget=APISelectMultiple(
            api_url="/api/dcim/regions/",
            value_field="slug",
            filter_for={
                'site': 'region'
            }
        )
    )
    site = DynamicModelMultipleChoiceField(
        queryset=Site.objects.all(),
        to_field_name='slug',
        required=False,
        widget=APISelectMultiple(
            api_url="/api/dcim/sites/",
            value_field="slug",
        )
    )
    asn = forms.IntegerField(
        required=False,
        label='ASN'
    )
    tag = TagFilterField(model)


#
# Circuit types
#

class CircuitTypeForm(BootstrapMixin, forms.ModelForm):
    slug = SlugField()

    class Meta:
        model = CircuitType
        fields = [
            'name', 'slug', 'description',
        ]


class CircuitTypeCSVForm(forms.ModelForm):
    slug = SlugField()

    class Meta:
        model = CircuitType
        fields = CircuitType.csv_headers
        help_texts = {
            'name': 'Name of circuit type',
        }


#
# Circuits
#

class CircuitForm(BootstrapMixin, TenancyForm, CustomFieldModelForm):
    provider = DynamicModelChoiceField(
        queryset=Provider.objects.all(),
        widget=APISelect(
            api_url="/api/circuits/providers/"
        )
    )
    type = DynamicModelChoiceField(
        queryset=CircuitType.objects.all(),
        widget=APISelect(
            api_url="/api/circuits/circuit-types/"
        )
    )
    comments = CommentField()
    tags = TagField(
        required=False
    )

    class Meta:
        model = Circuit
        fields = [
            'cid', 'type', 'provider', 'status', 'install_date', 'commit_rate', 'description', 'tenant_group', 'tenant',
            'comments', 'tags',
        ]
        help_texts = {
            'cid': "Unique circuit ID",
            'commit_rate': "Committed rate",
        }
        widgets = {
            'status': StaticSelect2(),
            'install_date': DatePicker(),
        }


class CircuitCSVForm(CustomFieldModelCSVForm):
    provider = forms.ModelChoiceField(
        queryset=Provider.objects.all(),
        to_field_name='name',
        help_text='Name of parent provider',
        error_messages={
            'invalid_choice': 'Provider not found.'
        }
    )
    type = forms.ModelChoiceField(
        queryset=CircuitType.objects.all(),
        to_field_name='name',
        help_text='Type of circuit',
        error_messages={
            'invalid_choice': 'Invalid circuit type.'
        }
    )
    status = CSVChoiceField(
        choices=CircuitStatusChoices,
        required=False,
        help_text='Operational status'
    )
    tenant = forms.ModelChoiceField(
        queryset=Tenant.objects.all(),
        required=False,
        to_field_name='name',
        help_text='Name of assigned tenant',
        error_messages={
            'invalid_choice': 'Tenant not found.'
        }
    )

    class Meta:
        model = Circuit
        fields = [
            'cid', 'provider', 'type', 'status', 'tenant', 'install_date', 'commit_rate', 'description', 'comments',
        ]


class CircuitBulkEditForm(BootstrapMixin, AddRemoveTagsForm, CustomFieldBulkEditForm):
    pk = forms.ModelMultipleChoiceField(
        queryset=Circuit.objects.all(),
        widget=forms.MultipleHiddenInput
    )
    type = DynamicModelChoiceField(
        queryset=CircuitType.objects.all(),
        required=False,
        widget=APISelect(
            api_url="/api/circuits/circuit-types/"
        )
    )
    provider = DynamicModelChoiceField(
        queryset=Provider.objects.all(),
        required=False,
        widget=APISelect(
            api_url="/api/circuits/providers/"
        )
    )
    status = forms.ChoiceField(
        choices=add_blank_choice(CircuitStatusChoices),
        required=False,
        initial='',
        widget=StaticSelect2()
    )
    tenant = DynamicModelChoiceField(
        queryset=Tenant.objects.all(),
        required=False,
        widget=APISelect(
            api_url="/api/tenancy/tenants/"
        )
    )
    commit_rate = forms.IntegerField(
        required=False,
        label='Commit rate (Kbps)'
    )
    description = forms.CharField(
        max_length=100,
        required=False
    )
    comments = CommentField(
        widget=SmallTextarea,
        label='Comments'
    )

    class Meta:
        nullable_fields = [
            'tenant', 'commit_rate', 'description', 'comments',
        ]


class CircuitFilterForm(BootstrapMixin, TenancyFilterForm, CustomFieldFilterForm):
    model = Circuit
    field_order = [
        'q', 'type', 'provider', 'status', 'region', 'site', 'tenant_group', 'tenant', 'commit_rate',
    ]
    q = forms.CharField(
        required=False,
        label='Search'
    )
    type = DynamicModelMultipleChoiceField(
        queryset=CircuitType.objects.all(),
        to_field_name='slug',
        required=False,
        widget=APISelectMultiple(
            api_url="/api/circuits/circuit-types/",
            value_field="slug",
        )
    )
    provider = DynamicModelMultipleChoiceField(
        queryset=Provider.objects.all(),
        to_field_name='slug',
        required=False,
        widget=APISelectMultiple(
            api_url="/api/circuits/providers/",
            value_field="slug",
        )
    )
    status = forms.MultipleChoiceField(
        choices=CircuitStatusChoices,
        required=False,
        widget=StaticSelect2Multiple()
    )
    region = DynamicModelMultipleChoiceField(
        queryset=Region.objects.all(),
        to_field_name='slug',
        required=False,
        widget=APISelectMultiple(
            api_url="/api/dcim/regions/",
            value_field="slug",
            filter_for={
                'site': 'region'
            }
        )
    )
    site = DynamicModelMultipleChoiceField(
        queryset=Site.objects.all(),
        to_field_name='slug',
        required=False,
        widget=APISelectMultiple(
            api_url="/api/dcim/sites/",
            value_field="slug",
        )
    )
    commit_rate = forms.IntegerField(
        required=False,
        min_value=0,
        label='Commit rate (Kbps)'
    )
    tag = TagFilterField(model)


#
# Circuit terminations
#

class CircuitTerminationForm(BootstrapMixin, forms.ModelForm):

    class Meta:
        model = CircuitTermination
        fields = [
            'term_side', 'site', 'port_speed', 'upstream_speed', 'xconnect_id', 'pp_info', 'description',
        ]
        help_texts = {
            'port_speed': "Physical circuit speed",
            'xconnect_id': "ID of the local cross-connect",
            'pp_info': "Patch panel ID and port number(s)"
        }
        widgets = {
            'term_side': forms.HiddenInput(),
            'site': APISelect(
                api_url="/api/dcim/sites/"
            )
        }
