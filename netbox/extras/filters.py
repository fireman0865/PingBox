import django_filters
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from dcim.models import DeviceRole, Platform, Region, Site
from tenancy.models import Tenant, TenantGroup
from virtualization.models import Cluster, ClusterGroup
from .choices import *
from .models import ConfigContext, CustomField, Graph, ExportTemplate, ObjectChange, Tag


__all__ = (
    'ConfigContextFilterSet',
    'CreatedUpdatedFilterSet',
    'CustomFieldFilter',
    'CustomFieldFilterSet',
    'ExportTemplateFilterSet',
    'GraphFilterSet',
    'LocalConfigContextFilterSet',
    'ObjectChangeFilterSet',
    'TagFilterSet',
)


class CustomFieldFilter(django_filters.Filter):
    """
    Filter objects by the presence of a CustomFieldValue. The filter's name is used as the CustomField name.
    """

    def __init__(self, custom_field, *args, **kwargs):
        self.cf_type = custom_field.type
        self.filter_logic = custom_field.filter_logic
        super().__init__(*args, **kwargs)

    def filter(self, queryset, value):

        # Skip filter on empty value
        if value is None or not value.strip():
            return queryset

        # Selection fields get special treatment (values must be integers)
        if self.cf_type == CustomFieldTypeChoices.TYPE_SELECT:
            try:
                # Treat 0 as None
                if int(value) == 0:
                    return queryset.exclude(
                        custom_field_values__field__name=self.field_name,
                    )
                # Match on exact CustomFieldChoice PK
                else:
                    return queryset.filter(
                        custom_field_values__field__name=self.field_name,
                        custom_field_values__serialized_value=value,
                    )
            except ValueError:
                return queryset.none()

        # Apply the assigned filter logic (exact or loose)
        if (self.cf_type == CustomFieldTypeChoices.TYPE_BOOLEAN or
                self.filter_logic == CustomFieldFilterLogicChoices.FILTER_EXACT):
            queryset = queryset.filter(
                custom_field_values__field__name=self.field_name,
                custom_field_values__serialized_value=value
            )
        else:
            queryset = queryset.filter(
                custom_field_values__field__name=self.field_name,
                custom_field_values__serialized_value__icontains=value
            )

        return queryset


class CustomFieldFilterSet(django_filters.FilterSet):
    """
    Dynamically add a Filter for each CustomField applicable to the parent model.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        obj_type = ContentType.objects.get_for_model(self._meta.model)
        custom_fields = CustomField.objects.filter(
            obj_type=obj_type
        ).exclude(
            filter_logic=CustomFieldFilterLogicChoices.FILTER_DISABLED
        )
        for cf in custom_fields:
            self.filters['cf_{}'.format(cf.name)] = CustomFieldFilter(field_name=cf.name, custom_field=cf)


class GraphFilterSet(django_filters.FilterSet):

    class Meta:
        model = Graph
        fields = ['type', 'name', 'template_language']


class ExportTemplateFilterSet(django_filters.FilterSet):

    class Meta:
        model = ExportTemplate
        fields = ['content_type', 'name', 'template_language']


class TagFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method='search',
        label='Search',
    )

    class Meta:
        model = Tag
        fields = ['name', 'slug']

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) |
            Q(slug__icontains=value)
        )


class ConfigContextFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method='search',
        label='Search',
    )
    region_id = django_filters.ModelMultipleChoiceFilter(
        field_name='regions',
        queryset=Region.objects.all(),
        label='Region',
    )
    region = django_filters.ModelMultipleChoiceFilter(
        field_name='regions__slug',
        queryset=Region.objects.all(),
        to_field_name='slug',
        label='Region (slug)',
    )
    site_id = django_filters.ModelMultipleChoiceFilter(
        field_name='sites',
        queryset=Site.objects.all(),
        label='Site',
    )
    site = django_filters.ModelMultipleChoiceFilter(
        field_name='sites__slug',
        queryset=Site.objects.all(),
        to_field_name='slug',
        label='Site (slug)',
    )
    role_id = django_filters.ModelMultipleChoiceFilter(
        field_name='roles',
        queryset=DeviceRole.objects.all(),
        label='Role',
    )
    role = django_filters.ModelMultipleChoiceFilter(
        field_name='roles__slug',
        queryset=DeviceRole.objects.all(),
        to_field_name='slug',
        label='Role (slug)',
    )
    platform_id = django_filters.ModelMultipleChoiceFilter(
        field_name='platforms',
        queryset=Platform.objects.all(),
        label='Platform',
    )
    platform = django_filters.ModelMultipleChoiceFilter(
        field_name='platforms__slug',
        queryset=Platform.objects.all(),
        to_field_name='slug',
        label='Platform (slug)',
    )
    cluster_group_id = django_filters.ModelMultipleChoiceFilter(
        field_name='cluster_groups',
        queryset=ClusterGroup.objects.all(),
        label='Cluster group',
    )
    cluster_group = django_filters.ModelMultipleChoiceFilter(
        field_name='cluster_groups__slug',
        queryset=ClusterGroup.objects.all(),
        to_field_name='slug',
        label='Cluster group (slug)',
    )
    cluster_id = django_filters.ModelMultipleChoiceFilter(
        field_name='clusters',
        queryset=Cluster.objects.all(),
        label='Cluster',
    )
    tenant_group_id = django_filters.ModelMultipleChoiceFilter(
        field_name='tenant_groups',
        queryset=TenantGroup.objects.all(),
        label='Tenant group',
    )
    tenant_group = django_filters.ModelMultipleChoiceFilter(
        field_name='tenant_groups__slug',
        queryset=TenantGroup.objects.all(),
        to_field_name='slug',
        label='Tenant group (slug)',
    )
    tenant_id = django_filters.ModelMultipleChoiceFilter(
        field_name='tenants',
        queryset=Tenant.objects.all(),
        label='Tenant',
    )
    tenant = django_filters.ModelMultipleChoiceFilter(
        field_name='tenants__slug',
        queryset=Tenant.objects.all(),
        to_field_name='slug',
        label='Tenant (slug)',
    )
    tag = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        queryset=Tag.objects.all(),
        to_field_name='slug',
        label='Tag (slug)',
    )

    class Meta:
        model = ConfigContext
        fields = ['name', 'is_active']

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value) |
            Q(data__icontains=value)
        )


#
# Filter for Local Config Context Data
#

class LocalConfigContextFilterSet(django_filters.FilterSet):
    local_context_data = django_filters.BooleanFilter(
        method='_local_context_data',
        label='Has local config context data',
    )

    def _local_context_data(self, queryset, name, value):
        return queryset.exclude(local_context_data__isnull=value)


class ObjectChangeFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method='search',
        label='Search',
    )
    time = django_filters.DateTimeFromToRangeFilter()

    class Meta:
        model = ObjectChange
        fields = [
            'user', 'user_name', 'request_id', 'action', 'changed_object_type', 'changed_object_id', 'object_repr',
        ]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(user_name__icontains=value) |
            Q(object_repr__icontains=value)
        )


class CreatedUpdatedFilterSet(django_filters.FilterSet):
    created = django_filters.DateFilter()
    created__gte = django_filters.DateFilter(
        field_name='created',
        lookup_expr='gte'
    )
    created__lte = django_filters.DateFilter(
        field_name='created',
        lookup_expr='lte'
    )
    last_updated = django_filters.DateTimeFilter()
    last_updated__gte = django_filters.DateTimeFilter(
        field_name='last_updated',
        lookup_expr='gte'
    )
    last_updated__lte = django_filters.DateTimeFilter(
        field_name='last_updated',
        lookup_expr='lte'
    )
