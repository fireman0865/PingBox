from django.contrib.contenttypes.models import ContentType
from drf_yasg.utils import swagger_serializer_method
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from taggit_serializer.serializers import TaggitSerializer, TagListSerializerField

from dcim.choices import *
from dcim.constants import *
from dcim.models import (
    Cable, ConsolePort, ConsolePortTemplate, ConsoleServerPort, ConsoleServerPortTemplate, Device, DeviceBay,
    DeviceBayTemplate, DeviceType, DeviceRole, FrontPort, FrontPortTemplate, Interface, InterfaceTemplate,
    Manufacturer, InventoryItem, Platform, PowerFeed, PowerOutlet, PowerOutletTemplate, PowerPanel, PowerPort,
    PowerPortTemplate, Rack, RackGroup, RackReservation, RackRole, RearPort, RearPortTemplate, Region, Site,
    VirtualChassis,
)
from extras.api.customfields import CustomFieldModelSerializer
from ipam.api.nested_serializers import NestedIPAddressSerializer, NestedVLANSerializer
from ipam.models import VLAN
from tenancy.api.nested_serializers import NestedTenantSerializer
from users.api.nested_serializers import NestedUserSerializer
from utilities.api import (
    ChoiceField, ContentTypeField, SerializedPKRelatedField, TimeZoneField, ValidatedModelSerializer,
    WritableNestedSerializer, get_serializer_for_model,
)
from virtualization.api.nested_serializers import NestedClusterSerializer
from .nested_serializers import *


class ConnectedEndpointSerializer(ValidatedModelSerializer):
    connected_endpoint_type = serializers.SerializerMethodField(read_only=True)
    connected_endpoint = serializers.SerializerMethodField(read_only=True)
    connection_status = ChoiceField(choices=CONNECTION_STATUS_CHOICES, read_only=True)

    def get_connected_endpoint_type(self, obj):
        if hasattr(obj, 'connected_endpoint') and obj.connected_endpoint is not None:
            return '{}.{}'.format(
                obj.connected_endpoint._meta.app_label,
                obj.connected_endpoint._meta.model_name
            )
        return None

    @swagger_serializer_method(serializer_or_field=serializers.DictField)
    def get_connected_endpoint(self, obj):
        """
        Return the appropriate serializer for the type of connected object.
        """
        if getattr(obj, 'connected_endpoint', None) is None:
            return None

        serializer = get_serializer_for_model(obj.connected_endpoint, prefix='Nested')
        context = {'request': self.context['request']}
        data = serializer(obj.connected_endpoint, context=context).data

        return data


#
# Regions/sites
#

class RegionSerializer(serializers.ModelSerializer):
    parent = NestedRegionSerializer(required=False, allow_null=True)
    site_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Region
        fields = ['id', 'name', 'slug', 'parent', 'site_count']


class SiteSerializer(TaggitSerializer, CustomFieldModelSerializer):
    status = ChoiceField(choices=SiteStatusChoices, required=False)
    region = NestedRegionSerializer(required=False, allow_null=True)
    tenant = NestedTenantSerializer(required=False, allow_null=True)
    time_zone = TimeZoneField(required=False)
    tags = TagListSerializerField(required=False)
    circuit_count = serializers.IntegerField(read_only=True)
    device_count = serializers.IntegerField(read_only=True)
    prefix_count = serializers.IntegerField(read_only=True)
    rack_count = serializers.IntegerField(read_only=True)
    virtualmachine_count = serializers.IntegerField(read_only=True)
    vlan_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Site
        fields = [
            'id', 'name', 'slug', 'status', 'region', 'tenant', 'facility', 'asn', 'time_zone', 'description',
            'physical_address', 'shipping_address', 'latitude', 'longitude', 'contact_name', 'contact_phone',
            'contact_email', 'comments', 'tags', 'custom_fields', 'created', 'last_updated', 'circuit_count',
            'device_count', 'prefix_count', 'rack_count', 'virtualmachine_count', 'vlan_count',
        ]


#
# Racks
#

class RackGroupSerializer(ValidatedModelSerializer):
    site = NestedSiteSerializer()
    rack_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = RackGroup
        fields = ['id', 'name', 'slug', 'site', 'rack_count']


class RackRoleSerializer(ValidatedModelSerializer):
    rack_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = RackRole
        fields = ['id', 'name', 'slug', 'color', 'description', 'rack_count']


class RackSerializer(TaggitSerializer, CustomFieldModelSerializer):
    site = NestedSiteSerializer()
    group = NestedRackGroupSerializer(required=False, allow_null=True, default=None)
    tenant = NestedTenantSerializer(required=False, allow_null=True)
    status = ChoiceField(choices=RackStatusChoices, required=False)
    role = NestedRackRoleSerializer(required=False, allow_null=True)
    type = ChoiceField(choices=RackTypeChoices, allow_blank=True, required=False)
    width = ChoiceField(choices=RackWidthChoices, required=False)
    outer_unit = ChoiceField(choices=RackDimensionUnitChoices, allow_blank=True, required=False)
    tags = TagListSerializerField(required=False)
    device_count = serializers.IntegerField(read_only=True)
    powerfeed_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Rack
        fields = [
            'id', 'name', 'facility_id', 'display_name', 'site', 'group', 'tenant', 'status', 'role', 'serial',
            'asset_tag', 'type', 'width', 'u_height', 'desc_units', 'outer_width', 'outer_depth', 'outer_unit',
            'comments', 'tags', 'custom_fields', 'created', 'last_updated', 'device_count', 'powerfeed_count',
        ]
        # Omit the UniqueTogetherValidator that would be automatically added to validate (group, facility_id). This
        # prevents facility_id from being interpreted as a required field.
        validators = [
            UniqueTogetherValidator(queryset=Rack.objects.all(), fields=('group', 'name'))
        ]

    def validate(self, data):

        # Validate uniqueness of (group, facility_id) since we omitted the automatically-created validator from Meta.
        if data.get('facility_id', None):
            validator = UniqueTogetherValidator(queryset=Rack.objects.all(), fields=('group', 'facility_id'))
            validator.set_context(self)
            validator(data)

        # Enforce model validation
        super().validate(data)

        return data


class RackUnitSerializer(serializers.Serializer):
    """
    A rack unit is an abstraction formed by the set (rack, position, face); it does not exist as a row in the database.
    """
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    face = ChoiceField(choices=DeviceFaceChoices, read_only=True)
    device = NestedDeviceSerializer(read_only=True)


class RackReservationSerializer(ValidatedModelSerializer):
    rack = NestedRackSerializer()
    user = NestedUserSerializer()
    tenant = NestedTenantSerializer(required=False, allow_null=True)

    class Meta:
        model = RackReservation
        fields = ['id', 'rack', 'units', 'created', 'user', 'tenant', 'description']


class RackElevationDetailFilterSerializer(serializers.Serializer):
    q = serializers.CharField(
        required=False,
        default=None
    )
    face = serializers.ChoiceField(
        choices=DeviceFaceChoices,
        default=DeviceFaceChoices.FACE_FRONT
    )
    render = serializers.ChoiceField(
        choices=RackElevationDetailRenderChoices,
        default=RackElevationDetailRenderChoices.RENDER_JSON
    )
    unit_width = serializers.IntegerField(
        default=RACK_ELEVATION_UNIT_WIDTH_DEFAULT
    )
    unit_height = serializers.IntegerField(
        default=RACK_ELEVATION_UNIT_HEIGHT_DEFAULT
    )
    legend_width = serializers.IntegerField(
        default=RACK_ELEVATION_LEGEND_WIDTH_DEFAULT
    )
    exclude = serializers.IntegerField(
        required=False,
        default=None
    )
    expand_devices = serializers.BooleanField(
        required=False,
        default=True
    )
    include_images = serializers.BooleanField(
        required=False,
        default=True
    )


#
# Device types
#

class ManufacturerSerializer(ValidatedModelSerializer):
    devicetype_count = serializers.IntegerField(read_only=True)
    inventoryitem_count = serializers.IntegerField(read_only=True)
    platform_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Manufacturer
        fields = ['id', 'name', 'slug', 'devicetype_count', 'inventoryitem_count', 'platform_count']


class DeviceTypeSerializer(TaggitSerializer, CustomFieldModelSerializer):
    manufacturer = NestedManufacturerSerializer()
    subdevice_role = ChoiceField(choices=SubdeviceRoleChoices, allow_blank=True, required=False)
    tags = TagListSerializerField(required=False)
    device_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = DeviceType
        fields = [
            'id', 'manufacturer', 'model', 'slug', 'display_name', 'part_number', 'u_height', 'is_full_depth',
            'subdevice_role', 'front_image', 'rear_image', 'comments', 'tags', 'custom_fields', 'created',
            'last_updated', 'device_count',
        ]


class ConsolePortTemplateSerializer(ValidatedModelSerializer):
    device_type = NestedDeviceTypeSerializer()
    type = ChoiceField(
        choices=ConsolePortTypeChoices,
        allow_blank=True,
        required=False
    )

    class Meta:
        model = ConsolePortTemplate
        fields = ['id', 'device_type', 'name', 'type']


class ConsoleServerPortTemplateSerializer(ValidatedModelSerializer):
    device_type = NestedDeviceTypeSerializer()
    type = ChoiceField(
        choices=ConsolePortTypeChoices,
        allow_blank=True,
        required=False
    )

    class Meta:
        model = ConsoleServerPortTemplate
        fields = ['id', 'device_type', 'name', 'type']


class PowerPortTemplateSerializer(ValidatedModelSerializer):
    device_type = NestedDeviceTypeSerializer()
    type = ChoiceField(
        choices=PowerPortTypeChoices,
        allow_blank=True,
        required=False
    )

    class Meta:
        model = PowerPortTemplate
        fields = ['id', 'device_type', 'name', 'type', 'maximum_draw', 'allocated_draw']


class PowerOutletTemplateSerializer(ValidatedModelSerializer):
    device_type = NestedDeviceTypeSerializer()
    type = ChoiceField(
        choices=PowerOutletTypeChoices,
        allow_blank=True,
        required=False
    )
    power_port = NestedPowerPortTemplateSerializer(
        required=False
    )
    feed_leg = ChoiceField(
        choices=PowerOutletFeedLegChoices,
        allow_blank=True,
        required=False
    )

    class Meta:
        model = PowerOutletTemplate
        fields = ['id', 'device_type', 'name', 'type', 'power_port', 'feed_leg']


class InterfaceTemplateSerializer(ValidatedModelSerializer):
    device_type = NestedDeviceTypeSerializer()
    type = ChoiceField(choices=InterfaceTypeChoices)

    class Meta:
        model = InterfaceTemplate
        fields = ['id', 'device_type', 'name', 'type', 'mgmt_only']


class RearPortTemplateSerializer(ValidatedModelSerializer):
    device_type = NestedDeviceTypeSerializer()
    type = ChoiceField(choices=PortTypeChoices)

    class Meta:
        model = RearPortTemplate
        fields = ['id', 'device_type', 'name', 'type', 'positions']


class FrontPortTemplateSerializer(ValidatedModelSerializer):
    device_type = NestedDeviceTypeSerializer()
    type = ChoiceField(choices=PortTypeChoices)
    rear_port = NestedRearPortTemplateSerializer()

    class Meta:
        model = FrontPortTemplate
        fields = ['id', 'device_type', 'name', 'type', 'rear_port', 'rear_port_position']


class DeviceBayTemplateSerializer(ValidatedModelSerializer):
    device_type = NestedDeviceTypeSerializer()

    class Meta:
        model = DeviceBayTemplate
        fields = ['id', 'device_type', 'name']


#
# Devices
#

class DeviceRoleSerializer(ValidatedModelSerializer):
    device_count = serializers.IntegerField(read_only=True)
    virtualmachine_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = DeviceRole
        fields = [
            'id', 'name', 'slug', 'color', 'vm_role', 'description', 'device_count', 'virtualmachine_count',
        ]


class PlatformSerializer(ValidatedModelSerializer):
    manufacturer = NestedManufacturerSerializer(required=False, allow_null=True)
    device_count = serializers.IntegerField(read_only=True)
    virtualmachine_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Platform
        fields = [
            'id', 'name', 'slug', 'manufacturer', 'napalm_driver', 'napalm_args', 'device_count',
            'virtualmachine_count',
        ]


class DeviceSerializer(TaggitSerializer, CustomFieldModelSerializer):
    device_type = NestedDeviceTypeSerializer()
    device_role = NestedDeviceRoleSerializer()
    tenant = NestedTenantSerializer(required=False, allow_null=True)
    platform = NestedPlatformSerializer(required=False, allow_null=True)
    site = NestedSiteSerializer()
    rack = NestedRackSerializer(required=False, allow_null=True)
    face = ChoiceField(choices=DeviceFaceChoices, allow_blank=True, required=False)
    status = ChoiceField(choices=DeviceStatusChoices, required=False)
    primary_ip = NestedIPAddressSerializer(read_only=True)
    primary_ip4 = NestedIPAddressSerializer(required=False, allow_null=True)
    primary_ip6 = NestedIPAddressSerializer(required=False, allow_null=True)
    parent_device = serializers.SerializerMethodField()
    cluster = NestedClusterSerializer(required=False, allow_null=True)
    virtual_chassis = NestedVirtualChassisSerializer(required=False, allow_null=True)
    tags = TagListSerializerField(required=False)

    class Meta:
        model = Device
        fields = [
            'id', 'name', 'display_name', 'device_type', 'device_role', 'tenant', 'platform', 'serial', 'asset_tag',
            'site', 'rack', 'position', 'face', 'parent_device', 'status', 'primary_ip', 'primary_ip4', 'primary_ip6',
            'cluster', 'virtual_chassis', 'vc_position', 'vc_priority', 'comments', 'local_context_data', 'tags',
            'custom_fields', 'created', 'last_updated',
        ]
        validators = []

    def validate(self, data):

        # Validate uniqueness of (rack, position, face) since we omitted the automatically-created validator from Meta.
        if data.get('rack') and data.get('position') and data.get('face'):
            validator = UniqueTogetherValidator(queryset=Device.objects.all(), fields=('rack', 'position', 'face'))
            validator.set_context(self)
            validator(data)

        # Enforce model validation
        super().validate(data)

        return data

    @swagger_serializer_method(serializer_or_field=NestedDeviceSerializer)
    def get_parent_device(self, obj):
        try:
            device_bay = obj.parent_bay
        except DeviceBay.DoesNotExist:
            return None
        context = {'request': self.context['request']}
        data = NestedDeviceSerializer(instance=device_bay.device, context=context).data
        data['device_bay'] = NestedDeviceBaySerializer(instance=device_bay, context=context).data
        return data


class DeviceWithConfigContextSerializer(DeviceSerializer):
    config_context = serializers.SerializerMethodField()

    class Meta(DeviceSerializer.Meta):
        fields = [
            'id', 'name', 'display_name', 'device_type', 'device_role', 'tenant', 'platform', 'serial', 'asset_tag',
            'site', 'rack', 'position', 'face', 'parent_device', 'status', 'primary_ip', 'primary_ip4', 'primary_ip6',
            'cluster', 'virtual_chassis', 'vc_position', 'vc_priority', 'comments', 'local_context_data', 'tags',
            'custom_fields', 'config_context', 'created', 'last_updated',
        ]

    @swagger_serializer_method(serializer_or_field=serializers.DictField)
    def get_config_context(self, obj):
        return obj.get_config_context()


class DeviceNAPALMSerializer(serializers.Serializer):
    method = serializers.DictField()


class ConsoleServerPortSerializer(TaggitSerializer, ConnectedEndpointSerializer):
    device = NestedDeviceSerializer()
    type = ChoiceField(
        choices=ConsolePortTypeChoices,
        allow_blank=True,
        required=False
    )
    cable = NestedCableSerializer(read_only=True)
    tags = TagListSerializerField(required=False)

    class Meta:
        model = ConsoleServerPort
        fields = [
            'id', 'device', 'name', 'type', 'description', 'connected_endpoint_type', 'connected_endpoint',
            'connection_status', 'cable', 'tags',
        ]


class ConsolePortSerializer(TaggitSerializer, ConnectedEndpointSerializer):
    device = NestedDeviceSerializer()
    type = ChoiceField(
        choices=ConsolePortTypeChoices,
        allow_blank=True,
        required=False
    )
    cable = NestedCableSerializer(read_only=True)
    tags = TagListSerializerField(required=False)

    class Meta:
        model = ConsolePort
        fields = [
            'id', 'device', 'name', 'type', 'description', 'connected_endpoint_type', 'connected_endpoint',
            'connection_status', 'cable', 'tags',
        ]


class PowerOutletSerializer(TaggitSerializer, ConnectedEndpointSerializer):
    device = NestedDeviceSerializer()
    type = ChoiceField(
        choices=PowerOutletTypeChoices,
        allow_blank=True,
        required=False
    )
    power_port = NestedPowerPortSerializer(
        required=False
    )
    feed_leg = ChoiceField(
        choices=PowerOutletFeedLegChoices,
        allow_blank=True,
        required=False
    )
    cable = NestedCableSerializer(
        read_only=True
    )
    tags = TagListSerializerField(
        required=False
    )

    class Meta:
        model = PowerOutlet
        fields = [
            'id', 'device', 'name', 'type', 'power_port', 'feed_leg', 'description', 'connected_endpoint_type',
            'connected_endpoint', 'connection_status', 'cable', 'tags',
        ]


class PowerPortSerializer(TaggitSerializer, ConnectedEndpointSerializer):
    device = NestedDeviceSerializer()
    type = ChoiceField(
        choices=PowerPortTypeChoices,
        allow_blank=True,
        required=False
    )
    cable = NestedCableSerializer(read_only=True)
    tags = TagListSerializerField(required=False)

    class Meta:
        model = PowerPort
        fields = [
            'id', 'device', 'name', 'type', 'maximum_draw', 'allocated_draw', 'description', 'connected_endpoint_type',
            'connected_endpoint', 'connection_status', 'cable', 'tags',
        ]


class InterfaceSerializer(TaggitSerializer, ConnectedEndpointSerializer):
    device = NestedDeviceSerializer()
    type = ChoiceField(choices=InterfaceTypeChoices)
    lag = NestedInterfaceSerializer(required=False, allow_null=True)
    mode = ChoiceField(choices=InterfaceModeChoices, allow_blank=True, required=False)
    untagged_vlan = NestedVLANSerializer(required=False, allow_null=True)
    tagged_vlans = SerializedPKRelatedField(
        queryset=VLAN.objects.all(),
        serializer=NestedVLANSerializer,
        required=False,
        many=True
    )
    cable = NestedCableSerializer(read_only=True)
    tags = TagListSerializerField(required=False)

    class Meta:
        model = Interface
        fields = [
            'id', 'device', 'name', 'type', 'enabled', 'lag', 'mtu', 'mac_address', 'mgmt_only', 'description',
            'connected_endpoint_type', 'connected_endpoint', 'connection_status', 'cable', 'mode', 'untagged_vlan',
            'tagged_vlans', 'tags', 'count_ipaddresses',
        ]

    # TODO: This validation should be handled by Interface.clean()
    def validate(self, data):

        # All associated VLANs be global or assigned to the parent device's site.
        device = self.instance.device if self.instance else data.get('device')
        untagged_vlan = data.get('untagged_vlan')
        if untagged_vlan and untagged_vlan.site not in [device.site, None]:
            raise serializers.ValidationError({
                'untagged_vlan': "VLAN {} must belong to the same site as the interface's parent device, or it must be "
                                 "global.".format(untagged_vlan)
            })
        for vlan in data.get('tagged_vlans', []):
            if vlan.site not in [device.site, None]:
                raise serializers.ValidationError({
                    'tagged_vlans': "VLAN {} must belong to the same site as the interface's parent device, or it must "
                                    "be global.".format(vlan)
                })

        return super().validate(data)


class RearPortSerializer(TaggitSerializer, ValidatedModelSerializer):
    device = NestedDeviceSerializer()
    type = ChoiceField(choices=PortTypeChoices)
    cable = NestedCableSerializer(read_only=True)
    tags = TagListSerializerField(required=False)

    class Meta:
        model = RearPort
        fields = ['id', 'device', 'name', 'type', 'positions', 'description', 'cable', 'tags']


class FrontPortRearPortSerializer(WritableNestedSerializer):
    """
    NestedRearPortSerializer but with parent device omitted (since front and rear ports must belong to same device)
    """
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:rearport-detail')

    class Meta:
        model = RearPort
        fields = ['id', 'url', 'name']


class FrontPortSerializer(TaggitSerializer, ValidatedModelSerializer):
    device = NestedDeviceSerializer()
    type = ChoiceField(choices=PortTypeChoices)
    rear_port = FrontPortRearPortSerializer()
    cable = NestedCableSerializer(read_only=True)
    tags = TagListSerializerField(required=False)

    class Meta:
        model = FrontPort
        fields = ['id', 'device', 'name', 'type', 'rear_port', 'rear_port_position', 'description', 'cable', 'tags']


class DeviceBaySerializer(TaggitSerializer, ValidatedModelSerializer):
    device = NestedDeviceSerializer()
    installed_device = NestedDeviceSerializer(required=False, allow_null=True)
    tags = TagListSerializerField(required=False)

    class Meta:
        model = DeviceBay
        fields = ['id', 'device', 'name', 'description', 'installed_device', 'tags']


#
# Inventory items
#

class InventoryItemSerializer(TaggitSerializer, ValidatedModelSerializer):
    device = NestedDeviceSerializer()
    # Provide a default value to satisfy UniqueTogetherValidator
    parent = serializers.PrimaryKeyRelatedField(queryset=InventoryItem.objects.all(), allow_null=True, default=None)
    manufacturer = NestedManufacturerSerializer(required=False, allow_null=True, default=None)
    tags = TagListSerializerField(required=False)

    class Meta:
        model = InventoryItem
        fields = [
            'id', 'device', 'parent', 'name', 'manufacturer', 'part_id', 'serial', 'asset_tag', 'discovered',
            'description', 'tags',
        ]


#
# Cables
#

class CableSerializer(ValidatedModelSerializer):
    termination_a_type = ContentTypeField(
        queryset=ContentType.objects.filter(CABLE_TERMINATION_MODELS)
    )
    termination_b_type = ContentTypeField(
        queryset=ContentType.objects.filter(CABLE_TERMINATION_MODELS)
    )
    termination_a = serializers.SerializerMethodField(read_only=True)
    termination_b = serializers.SerializerMethodField(read_only=True)
    status = ChoiceField(choices=CableStatusChoices, required=False)
    length_unit = ChoiceField(choices=CableLengthUnitChoices, allow_blank=True, required=False)

    class Meta:
        model = Cable
        fields = [
            'id', 'termination_a_type', 'termination_a_id', 'termination_a', 'termination_b_type', 'termination_b_id',
            'termination_b', 'type', 'status', 'label', 'color', 'length', 'length_unit',
        ]

    def _get_termination(self, obj, side):
        """
        Serialize a nested representation of a termination.
        """
        if side.lower() not in ['a', 'b']:
            raise ValueError("Termination side must be either A or B.")
        termination = getattr(obj, 'termination_{}'.format(side.lower()))
        if termination is None:
            return None
        serializer = get_serializer_for_model(termination, prefix='Nested')
        context = {'request': self.context['request']}
        data = serializer(termination, context=context).data

        return data

    @swagger_serializer_method(serializer_or_field=serializers.DictField)
    def get_termination_a(self, obj):
        return self._get_termination(obj, 'a')

    @swagger_serializer_method(serializer_or_field=serializers.DictField)
    def get_termination_b(self, obj):
        return self._get_termination(obj, 'b')


class TracedCableSerializer(serializers.ModelSerializer):
    """
    Used only while tracing a cable path.
    """
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:cable-detail')

    class Meta:
        model = Cable
        fields = [
            'id', 'url', 'type', 'status', 'label', 'color', 'length', 'length_unit',
        ]


#
# Interface connections
#

class InterfaceConnectionSerializer(ValidatedModelSerializer):
    interface_a = serializers.SerializerMethodField()
    interface_b = NestedInterfaceSerializer(source='connected_endpoint')
    connection_status = ChoiceField(choices=CONNECTION_STATUS_CHOICES, required=False)

    class Meta:
        model = Interface
        fields = ['interface_a', 'interface_b', 'connection_status']

    @swagger_serializer_method(serializer_or_field=NestedInterfaceSerializer)
    def get_interface_a(self, obj):
        context = {'request': self.context['request']}
        return NestedInterfaceSerializer(instance=obj, context=context).data


#
# Virtual chassis
#

class VirtualChassisSerializer(TaggitSerializer, ValidatedModelSerializer):
    master = NestedDeviceSerializer()
    tags = TagListSerializerField(required=False)
    member_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = VirtualChassis
        fields = ['id', 'master', 'domain', 'tags', 'member_count']


#
# Power panels
#

class PowerPanelSerializer(ValidatedModelSerializer):
    site = NestedSiteSerializer()
    rack_group = NestedRackGroupSerializer(
        required=False,
        allow_null=True,
        default=None
    )
    powerfeed_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = PowerPanel
        fields = ['id', 'site', 'rack_group', 'name', 'powerfeed_count']


class PowerFeedSerializer(TaggitSerializer, CustomFieldModelSerializer):
    power_panel = NestedPowerPanelSerializer()
    rack = NestedRackSerializer(
        required=False,
        allow_null=True,
        default=None
    )
    type = ChoiceField(
        choices=PowerFeedTypeChoices,
        default=PowerFeedTypeChoices.TYPE_PRIMARY
    )
    status = ChoiceField(
        choices=PowerFeedStatusChoices,
        default=PowerFeedStatusChoices.STATUS_ACTIVE
    )
    supply = ChoiceField(
        choices=PowerFeedSupplyChoices,
        default=PowerFeedSupplyChoices.SUPPLY_AC
    )
    phase = ChoiceField(
        choices=PowerFeedPhaseChoices,
        default=PowerFeedPhaseChoices.PHASE_SINGLE
    )
    tags = TagListSerializerField(
        required=False
    )

    class Meta:
        model = PowerFeed
        fields = [
            'id', 'power_panel', 'rack', 'name', 'status', 'type', 'supply', 'phase', 'voltage', 'amperage',
            'max_utilization', 'comments', 'tags', 'custom_fields', 'created', 'last_updated',
        ]
