import netaddr
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.urls import reverse
from taggit.managers import TaggableManager

from dcim.models import Device, Interface
from extras.models import CustomFieldModel, ObjectChange, TaggedItem
from utilities.models import ChangeLoggedModel
from utilities.utils import serialize_object
from virtualization.models import VirtualMachine
from .choices import *
from .constants import *
from .fields import IPNetworkField, IPAddressField
from .managers import IPAddressManager
from .querysets import PrefixQuerySet
from .validators import DNSValidator


__all__ = (
    'Aggregate',
    'IPAddress',
    'Prefix',
    'RIR',
    'Role',
    'Service',
    'VLAN',
    'VLANGroup',
    'VRF',
)


class VRF(ChangeLoggedModel, CustomFieldModel):
    """
    A virtual routing and forwarding (VRF) table represents a discrete layer three forwarding domain (e.g. a routing
    table). Prefixes and IPAddresses can optionally be assigned to VRFs. (Prefixes and IPAddresses not assigned to a VRF
    are said to exist in the "global" table.)
    """
    name = models.CharField(
        max_length=50
    )
    rd = models.CharField(
        max_length=VRF_RD_MAX_LENGTH,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Route distinguisher'
    )
    tenant = models.ForeignKey(
        to='tenancy.Tenant',
        on_delete=models.PROTECT,
        related_name='vrfs',
        blank=True,
        null=True
    )
    enforce_unique = models.BooleanField(
        default=True,
        verbose_name='Enforce unique space',
        help_text='Prevent duplicate prefixes/IP addresses within this VRF'
    )
    description = models.CharField(
        max_length=100,
        blank=True
    )
    custom_field_values = GenericRelation(
        to='extras.CustomFieldValue',
        content_type_field='obj_type',
        object_id_field='obj_id'
    )

    tags = TaggableManager(through=TaggedItem)

    csv_headers = ['name', 'rd', 'tenant', 'enforce_unique', 'description']
    clone_fields = [
        'tenant', 'enforce_unique', 'description',
    ]

    class Meta:
        ordering = ('name', 'rd', 'pk')  # (name, rd) may be non-unique
        verbose_name = 'VRF'
        verbose_name_plural = 'VRFs'

    def __str__(self):
        return self.display_name or super().__str__()

    def get_absolute_url(self):
        return reverse('ipam:vrf', args=[self.pk])

    def to_csv(self):
        return (
            self.name,
            self.rd,
            self.tenant.name if self.tenant else None,
            self.enforce_unique,
            self.description,
        )

    @property
    def display_name(self):
        if self.rd:
            return "{} ({})".format(self.name, self.rd)
        return self.name


class RIR(ChangeLoggedModel):
    """
    A Regional Internet Registry (RIR) is responsible for the allocation of a large portion of the global IP address
    space. This can be an organization like ARIN or RIPE, or a governing standard such as RFC 1918.
    """
    name = models.CharField(
        max_length=50,
        unique=True
    )
    slug = models.SlugField(
        unique=True
    )
    is_private = models.BooleanField(
        default=False,
        verbose_name='Private',
        help_text='IP space managed by this RIR is considered private'
    )

    csv_headers = ['name', 'slug', 'is_private']

    class Meta:
        ordering = ['name']
        verbose_name = 'RIR'
        verbose_name_plural = 'RIRs'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return "{}?rir={}".format(reverse('ipam:aggregate_list'), self.slug)

    def to_csv(self):
        return (
            self.name,
            self.slug,
            self.is_private,
        )


class Aggregate(ChangeLoggedModel, CustomFieldModel):
    """
    An aggregate exists at the root level of the IP address space hierarchy in NetBox. Aggregates are used to organize
    the hierarchy and track the overall utilization of available address space. Each Aggregate is assigned to a RIR.
    """
    family = models.PositiveSmallIntegerField(
        choices=IPAddressFamilyChoices
    )
    prefix = IPNetworkField()
    rir = models.ForeignKey(
        to='ipam.RIR',
        on_delete=models.PROTECT,
        related_name='aggregates',
        verbose_name='RIR'
    )
    date_added = models.DateField(
        blank=True,
        null=True
    )
    description = models.CharField(
        max_length=100,
        blank=True
    )
    custom_field_values = GenericRelation(
        to='extras.CustomFieldValue',
        content_type_field='obj_type',
        object_id_field='obj_id'
    )

    tags = TaggableManager(through=TaggedItem)

    csv_headers = ['prefix', 'rir', 'date_added', 'description']
    clone_fields = [
        'rir', 'date_added', 'description',
    ]

    class Meta:
        ordering = ('family', 'prefix', 'pk')  # (family, prefix) may be non-unique

    def __str__(self):
        return str(self.prefix)

    def get_absolute_url(self):
        return reverse('ipam:aggregate', args=[self.pk])

    def clean(self):

        if self.prefix:

            # Clear host bits from prefix
            self.prefix = self.prefix.cidr

            # /0 masks are not acceptable
            if self.prefix.prefixlen == 0:
                raise ValidationError({
                    'prefix': "Cannot create aggregate with /0 mask."
                })

            # Ensure that the aggregate being added is not covered by an existing aggregate
            covering_aggregates = Aggregate.objects.filter(prefix__net_contains_or_equals=str(self.prefix))
            if self.pk:
                covering_aggregates = covering_aggregates.exclude(pk=self.pk)
            if covering_aggregates:
                raise ValidationError({
                    'prefix': "Aggregates cannot overlap. {} is already covered by an existing aggregate ({}).".format(
                        self.prefix, covering_aggregates[0]
                    )
                })

            # Ensure that the aggregate being added does not cover an existing aggregate
            covered_aggregates = Aggregate.objects.filter(prefix__net_contained=str(self.prefix))
            if self.pk:
                covered_aggregates = covered_aggregates.exclude(pk=self.pk)
            if covered_aggregates:
                raise ValidationError({
                    'prefix': "Aggregates cannot overlap. {} covers an existing aggregate ({}).".format(
                        self.prefix, covered_aggregates[0]
                    )
                })

    def save(self, *args, **kwargs):
        if self.prefix:
            # Infer address family from IPNetwork object
            self.family = self.prefix.version
        super().save(*args, **kwargs)

    def to_csv(self):
        return (
            self.prefix,
            self.rir.name,
            self.date_added,
            self.description,
        )

    def get_utilization(self):
        """
        Determine the prefix utilization of the aggregate and return it as a percentage.
        """
        queryset = Prefix.objects.filter(prefix__net_contained_or_equal=str(self.prefix))
        child_prefixes = netaddr.IPSet([p.prefix for p in queryset])
        return int(float(child_prefixes.size) / self.prefix.size * 100)


class Role(ChangeLoggedModel):
    """
    A Role represents the functional role of a Prefix or VLAN; for example, "Customer," "Infrastructure," or
    "Management."
    """
    name = models.CharField(
        max_length=50,
        unique=True
    )
    slug = models.SlugField(
        unique=True
    )
    weight = models.PositiveSmallIntegerField(
        default=1000
    )
    description = models.CharField(
        max_length=100,
        blank=True,
    )

    csv_headers = ['name', 'slug', 'weight', 'description']

    class Meta:
        ordering = ['weight', 'name']

    def __str__(self):
        return self.name

    def to_csv(self):
        return (
            self.name,
            self.slug,
            self.weight,
            self.description,
        )


class Prefix(ChangeLoggedModel, CustomFieldModel):
    """
    A Prefix represents an IPv4 or IPv6 network, including mask length. Prefixes can optionally be assigned to Sites and
    VRFs. A Prefix must be assigned a status and may optionally be assigned a used-define Role. A Prefix can also be
    assigned to a VLAN where appropriate.
    """
    family = models.PositiveSmallIntegerField(
        choices=IPAddressFamilyChoices,
        editable=False
    )
    prefix = IPNetworkField(
        help_text='IPv4 or IPv6 network with mask'
    )
    site = models.ForeignKey(
        to='dcim.Site',
        on_delete=models.PROTECT,
        related_name='prefixes',
        blank=True,
        null=True
    )
    vrf = models.ForeignKey(
        to='ipam.VRF',
        on_delete=models.PROTECT,
        related_name='prefixes',
        blank=True,
        null=True,
        verbose_name='VRF'
    )
    tenant = models.ForeignKey(
        to='tenancy.Tenant',
        on_delete=models.PROTECT,
        related_name='prefixes',
        blank=True,
        null=True
    )
    vlan = models.ForeignKey(
        to='ipam.VLAN',
        on_delete=models.PROTECT,
        related_name='prefixes',
        blank=True,
        null=True,
        verbose_name='VLAN'
    )
    status = models.CharField(
        max_length=50,
        choices=PrefixStatusChoices,
        default=PrefixStatusChoices.STATUS_ACTIVE,
        verbose_name='Status',
        help_text='Operational status of this prefix'
    )
    role = models.ForeignKey(
        to='ipam.Role',
        on_delete=models.SET_NULL,
        related_name='prefixes',
        blank=True,
        null=True,
        help_text='The primary function of this prefix'
    )
    is_pool = models.BooleanField(
        verbose_name='Is a pool',
        default=False,
        help_text='All IP addresses within this prefix are considered usable'
    )
    description = models.CharField(
        max_length=100,
        blank=True
    )
    custom_field_values = GenericRelation(
        to='extras.CustomFieldValue',
        content_type_field='obj_type',
        object_id_field='obj_id'
    )

    objects = PrefixQuerySet.as_manager()
    tags = TaggableManager(through=TaggedItem)

    csv_headers = [
        'prefix', 'vrf', 'tenant', 'site', 'vlan_group', 'vlan_vid', 'status', 'role', 'is_pool', 'description',
    ]
    clone_fields = [
        'site', 'vrf', 'tenant', 'vlan', 'status', 'role', 'is_pool', 'description',
    ]

    STATUS_CLASS_MAP = {
        'container': 'default',
        'active': 'primary',
        'reserved': 'info',
        'deprecated': 'danger',
    }

    class Meta:
        ordering = (F('vrf').asc(nulls_first=True), 'family', 'prefix', 'pk')  # (vrf, family, prefix) may be non-unique
        verbose_name_plural = 'prefixes'

    def __str__(self):
        return str(self.prefix)

    def get_absolute_url(self):
        return reverse('ipam:prefix', args=[self.pk])

    def clean(self):

        if self.prefix:

            # /0 masks are not acceptable
            if self.prefix.prefixlen == 0:
                raise ValidationError({
                    'prefix': "Cannot create prefix with /0 mask."
                })

            # Disallow host masks
            if self.prefix.version == 4 and self.prefix.prefixlen == 32:
                raise ValidationError({
                    'prefix': "Cannot create host addresses (/32) as prefixes. Create an IPv4 address instead."
                })
            elif self.prefix.version == 6 and self.prefix.prefixlen == 128:
                raise ValidationError({
                    'prefix': "Cannot create host addresses (/128) as prefixes. Create an IPv6 address instead."
                })

            # Enforce unique IP space (if applicable)
            if (self.vrf is None and settings.ENFORCE_GLOBAL_UNIQUE) or (self.vrf and self.vrf.enforce_unique):
                duplicate_prefixes = self.get_duplicates()
                if duplicate_prefixes:
                    raise ValidationError({
                        'prefix': "Duplicate prefix found in {}: {}".format(
                            "VRF {}".format(self.vrf) if self.vrf else "global table",
                            duplicate_prefixes.first(),
                        )
                    })

    def save(self, *args, **kwargs):

        if isinstance(self.prefix, netaddr.IPNetwork):

            # Clear host bits from prefix
            self.prefix = self.prefix.cidr

            # Record address family
            self.family = self.prefix.version

        super().save(*args, **kwargs)

    def to_csv(self):
        return (
            self.prefix,
            self.vrf.name if self.vrf else None,
            self.tenant.name if self.tenant else None,
            self.site.name if self.site else None,
            self.vlan.group.name if self.vlan and self.vlan.group else None,
            self.vlan.vid if self.vlan else None,
            self.get_status_display(),
            self.role.name if self.role else None,
            self.is_pool,
            self.description,
        )

    def _set_prefix_length(self, value):
        """
        Expose the IPNetwork object's prefixlen attribute on the parent model so that it can be manipulated directly,
        e.g. for bulk editing.
        """
        if self.prefix is not None:
            self.prefix.prefixlen = value
    prefix_length = property(fset=_set_prefix_length)

    def get_status_class(self):
        return self.STATUS_CLASS_MAP.get(self.status)

    def get_duplicates(self):
        return Prefix.objects.filter(vrf=self.vrf, prefix=str(self.prefix)).exclude(pk=self.pk)

    def get_child_prefixes(self):
        """
        Return all Prefixes within this Prefix and VRF. If this Prefix is a container in the global table, return child
        Prefixes belonging to any VRF.
        """
        if self.vrf is None and self.status == PrefixStatusChoices.STATUS_CONTAINER:
            return Prefix.objects.filter(prefix__net_contained=str(self.prefix))
        else:
            return Prefix.objects.filter(prefix__net_contained=str(self.prefix), vrf=self.vrf)

    def get_child_ips(self):
        """
        Return all IPAddresses within this Prefix and VRF. If this Prefix is a container in the global table, return
        child IPAddresses belonging to any VRF.
        """
        if self.vrf is None and self.status == PrefixStatusChoices.STATUS_CONTAINER:
            return IPAddress.objects.filter(address__net_host_contained=str(self.prefix))
        else:
            return IPAddress.objects.filter(address__net_host_contained=str(self.prefix), vrf=self.vrf)

    def get_available_prefixes(self):
        """
        Return all available Prefixes within this prefix as an IPSet.
        """
        prefix = netaddr.IPSet(self.prefix)
        child_prefixes = netaddr.IPSet([child.prefix for child in self.get_child_prefixes()])
        available_prefixes = prefix - child_prefixes

        return available_prefixes

    def get_available_ips(self):
        """
        Return all available IPs within this prefix as an IPSet.
        """
        prefix = netaddr.IPSet(self.prefix)
        child_ips = netaddr.IPSet([ip.address.ip for ip in self.get_child_ips()])
        available_ips = prefix - child_ips

        # All IP addresses within a pool are considered usable
        if self.is_pool:
            return available_ips

        # All IP addresses within a point-to-point prefix (IPv4 /31 or IPv6 /127) are considered usable
        if (
            self.family == 4 and self.prefix.prefixlen == 31  # RFC 3021
        ) or (
            self.family == 6 and self.prefix.prefixlen == 127  # RFC 6164
        ):
            return available_ips

        # Omit first and last IP address from the available set
        available_ips -= netaddr.IPSet([
            netaddr.IPAddress(self.prefix.first),
            netaddr.IPAddress(self.prefix.last),
        ])

        return available_ips

    def get_first_available_prefix(self):
        """
        Return the first available child prefix within the prefix (or None).
        """
        available_prefixes = self.get_available_prefixes()
        if not available_prefixes:
            return None
        return available_prefixes.iter_cidrs()[0]

    def get_first_available_ip(self):
        """
        Return the first available IP within the prefix (or None).
        """
        available_ips = self.get_available_ips()
        if not available_ips:
            return None
        return '{}/{}'.format(next(available_ips.__iter__()), self.prefix.prefixlen)

    def get_utilization(self):
        """
        Determine the utilization of the prefix and return it as a percentage. For Prefixes with a status of
        "container", calculate utilization based on child prefixes. For all others, count child IP addresses.
        """
        if self.status == PrefixStatusChoices.STATUS_CONTAINER:
            queryset = Prefix.objects.filter(prefix__net_contained=str(self.prefix), vrf=self.vrf)
            child_prefixes = netaddr.IPSet([p.prefix for p in queryset])
            return int(float(child_prefixes.size) / self.prefix.size * 100)
        else:
            # Compile an IPSet to avoid counting duplicate IPs
            child_count = netaddr.IPSet([ip.address.ip for ip in self.get_child_ips()]).size
            prefix_size = self.prefix.size
            if self.family == 4 and self.prefix.prefixlen < 31 and not self.is_pool:
                prefix_size -= 2
            return int(float(child_count) / prefix_size * 100)


class IPAddress(ChangeLoggedModel, CustomFieldModel):
    """
    An IPAddress represents an individual IPv4 or IPv6 address and its mask. The mask length should match what is
    configured in the real world. (Typically, only loopback interfaces are configured with /32 or /128 masks.) Like
    Prefixes, IPAddresses can optionally be assigned to a VRF. An IPAddress can optionally be assigned to an Interface.
    Interfaces can have zero or more IPAddresses assigned to them.

    An IPAddress can also optionally point to a NAT inside IP, designating itself as a NAT outside IP. This is useful,
    for example, when mapping public addresses to private addresses. When an Interface has been assigned an IPAddress
    which has a NAT outside IP, that Interface's Device can use either the inside or outside IP as its primary IP.
    """
    family = models.PositiveSmallIntegerField(
        choices=IPAddressFamilyChoices,
        editable=False
    )
    address = IPAddressField(
        help_text='IPv4 or IPv6 address (with mask)'
    )
    vrf = models.ForeignKey(
        to='ipam.VRF',
        on_delete=models.PROTECT,
        related_name='ip_addresses',
        blank=True,
        null=True,
        verbose_name='VRF'
    )
    tenant = models.ForeignKey(
        to='tenancy.Tenant',
        on_delete=models.PROTECT,
        related_name='ip_addresses',
        blank=True,
        null=True
    )
    status = models.CharField(
        max_length=50,
        choices=IPAddressStatusChoices,
        default=IPAddressStatusChoices.STATUS_ACTIVE,
        help_text='The operational status of this IP'
    )
    role = models.CharField(
        max_length=50,
        choices=IPAddressRoleChoices,
        blank=True,
        help_text='The functional role of this IP'
    )
    interface = models.ForeignKey(
        to='dcim.Interface',
        on_delete=models.CASCADE,
        related_name='ip_addresses',
        blank=True,
        null=True
    )
    nat_inside = models.OneToOneField(
        to='self',
        on_delete=models.SET_NULL,
        related_name='nat_outside',
        blank=True,
        null=True,
        verbose_name='NAT (Inside)',
        help_text='The IP for which this address is the "outside" IP'
    )
    dns_name = models.CharField(
        max_length=255,
        blank=True,
        validators=[DNSValidator],
        verbose_name='DNS Name',
        help_text='Hostname or FQDN (not case-sensitive)'
    )
    description = models.CharField(
        max_length=100,
        blank=True
    )
    custom_field_values = GenericRelation(
        to='extras.CustomFieldValue',
        content_type_field='obj_type',
        object_id_field='obj_id'
    )

    objects = IPAddressManager()
    tags = TaggableManager(through=TaggedItem)

    csv_headers = [
        'address', 'vrf', 'tenant', 'status', 'role', 'device', 'virtual_machine', 'interface_name', 'is_primary',
        'dns_name', 'description',
    ]
    clone_fields = [
        'vrf', 'tenant', 'status', 'role', 'description',
    ]

    STATUS_CLASS_MAP = {
        'active': 'primary',
        'reserved': 'info',
        'deprecated': 'danger',
        'dhcp': 'success',
    }

    ROLE_CLASS_MAP = {
        'loopback': 'default',
        'secondary': 'primary',
        'anycast': 'warning',
        'vip': 'success',
        'vrrp': 'success',
        'hsrp': 'success',
        'glbp': 'success',
        'carp': 'success',
    }

    class Meta:
        ordering = ('family', 'address', 'pk')  # (family, address) may be non-unique
        verbose_name = 'IP address'
        verbose_name_plural = 'IP addresses'

    def __str__(self):
        return str(self.address)

    def get_absolute_url(self):
        return reverse('ipam:ipaddress', args=[self.pk])

    def get_duplicates(self):
        return IPAddress.objects.filter(vrf=self.vrf, address__net_host=str(self.address.ip)).exclude(pk=self.pk)

    def clean(self):

        if self.address:

            # /0 masks are not acceptable
            if self.address.prefixlen == 0:
                raise ValidationError({
                    'address': "Cannot create IP address with /0 mask."
                })

            # Enforce unique IP space (if applicable)
            if self.role not in IPADDRESS_ROLES_NONUNIQUE and ((
                self.vrf is None and settings.ENFORCE_GLOBAL_UNIQUE
            ) or (
                self.vrf and self.vrf.enforce_unique
            )):
                duplicate_ips = self.get_duplicates()
                if duplicate_ips:
                    raise ValidationError({
                        'address': "Duplicate IP address found in {}: {}".format(
                            "VRF {}".format(self.vrf) if self.vrf else "global table",
                            duplicate_ips.first(),
                        )
                    })

        if self.pk:

            # Check for primary IP assignment that doesn't match the assigned device/VM
            device = Device.objects.filter(Q(primary_ip4=self) | Q(primary_ip6=self)).first()
            if device:
                if self.interface is None:
                    raise ValidationError({
                        'interface': "IP address is primary for device {} but not assigned".format(device)
                    })
                elif (device.primary_ip4 == self or device.primary_ip6 == self) and self.interface.device != device:
                    raise ValidationError({
                        'interface': "IP address is primary for device {} but assigned to {} ({})".format(
                            device, self.interface.device, self.interface
                        )
                    })
            vm = VirtualMachine.objects.filter(Q(primary_ip4=self) | Q(primary_ip6=self)).first()
            if vm:
                if self.interface is None:
                    raise ValidationError({
                        'interface': "IP address is primary for virtual machine {} but not assigned".format(vm)
                    })
                elif (vm.primary_ip4 == self or vm.primary_ip6 == self) and self.interface.virtual_machine != vm:
                    raise ValidationError({
                        'interface': "IP address is primary for virtual machine {} but assigned to {} ({})".format(
                            vm, self.interface.virtual_machine, self.interface
                        )
                    })

    def save(self, *args, **kwargs):

        # Record address family
        if isinstance(self.address, netaddr.IPNetwork):
            self.family = self.address.version

        # Force dns_name to lowercase
        self.dns_name = self.dns_name.lower()

        super().save(*args, **kwargs)

    def to_objectchange(self, action):
        # Annotate the assigned Interface (if any)
        try:
            parent_obj = self.interface
        except ObjectDoesNotExist:
            parent_obj = None

        return ObjectChange(
            changed_object=self,
            object_repr=str(self),
            action=action,
            related_object=parent_obj,
            object_data=serialize_object(self)
        )

    def to_csv(self):

        # Determine if this IP is primary for a Device
        if self.family == 4 and getattr(self, 'primary_ip4_for', False):
            is_primary = True
        elif self.family == 6 and getattr(self, 'primary_ip6_for', False):
            is_primary = True
        else:
            is_primary = False

        return (
            self.address,
            self.vrf.name if self.vrf else None,
            self.tenant.name if self.tenant else None,
            self.get_status_display(),
            self.get_role_display(),
            self.device.identifier if self.device else None,
            self.virtual_machine.name if self.virtual_machine else None,
            self.interface.name if self.interface else None,
            is_primary,
            self.dns_name,
            self.description,
        )

    def _set_mask_length(self, value):
        """
        Expose the IPNetwork object's prefixlen attribute on the parent model so that it can be manipulated directly,
        e.g. for bulk editing.
        """
        if self.address is not None:
            self.address.prefixlen = value
    mask_length = property(fset=_set_mask_length)

    @property
    def device(self):
        if self.interface:
            return self.interface.device
        return None

    @property
    def virtual_machine(self):
        if self.interface:
            return self.interface.virtual_machine
        return None

    def get_status_class(self):
        return self.STATUS_CLASS_MAP.get(self.status)

    def get_role_class(self):
        return self.ROLE_CLASS_MAP[self.role]


class VLANGroup(ChangeLoggedModel):
    """
    A VLAN group is an arbitrary collection of VLANs within which VLAN IDs and names must be unique.
    """
    name = models.CharField(
        max_length=50
    )
    slug = models.SlugField()
    site = models.ForeignKey(
        to='dcim.Site',
        on_delete=models.PROTECT,
        related_name='vlan_groups',
        blank=True,
        null=True
    )

    csv_headers = ['name', 'slug', 'site']

    class Meta:
        ordering = ('site', 'name', 'pk')  # (site, name) may be non-unique
        unique_together = [
            ['site', 'name'],
            ['site', 'slug'],
        ]
        verbose_name = 'VLAN group'
        verbose_name_plural = 'VLAN groups'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('ipam:vlangroup_vlans', args=[self.pk])

    def to_csv(self):
        return (
            self.name,
            self.slug,
            self.site.name if self.site else None,
        )

    def get_next_available_vid(self):
        """
        Return the first available VLAN ID (1-4094) in the group.
        """
        vids = [vlan['vid'] for vlan in self.vlans.order_by('vid').values('vid')]
        for i in range(1, 4095):
            if i not in vids:
                return i
        return None


class VLAN(ChangeLoggedModel, CustomFieldModel):
    """
    A VLAN is a distinct layer two forwarding domain identified by a 12-bit integer (1-4094). Each VLAN must be assigned
    to a Site, however VLAN IDs need not be unique within a Site. A VLAN may optionally be assigned to a VLANGroup,
    within which all VLAN IDs and names but be unique.

    Like Prefixes, each VLAN is assigned an operational status and optionally a user-defined Role. A VLAN can have zero
    or more Prefixes assigned to it.
    """
    site = models.ForeignKey(
        to='dcim.Site',
        on_delete=models.PROTECT,
        related_name='vlans',
        blank=True,
        null=True
    )
    group = models.ForeignKey(
        to='ipam.VLANGroup',
        on_delete=models.PROTECT,
        related_name='vlans',
        blank=True,
        null=True
    )
    vid = models.PositiveSmallIntegerField(
        verbose_name='ID',
        validators=[MinValueValidator(1), MaxValueValidator(4094)]
    )
    name = models.CharField(
        max_length=64
    )
    tenant = models.ForeignKey(
        to='tenancy.Tenant',
        on_delete=models.PROTECT,
        related_name='vlans',
        blank=True,
        null=True
    )
    status = models.CharField(
        max_length=50,
        choices=VLANStatusChoices,
        default=VLANStatusChoices.STATUS_ACTIVE
    )
    role = models.ForeignKey(
        to='ipam.Role',
        on_delete=models.SET_NULL,
        related_name='vlans',
        blank=True,
        null=True
    )
    description = models.CharField(
        max_length=100,
        blank=True
    )
    custom_field_values = GenericRelation(
        to='extras.CustomFieldValue',
        content_type_field='obj_type',
        object_id_field='obj_id'
    )

    tags = TaggableManager(through=TaggedItem)

    csv_headers = ['site', 'group_name', 'vid', 'name', 'tenant', 'status', 'role', 'description']
    clone_fields = [
        'site', 'group', 'tenant', 'status', 'role', 'description',
    ]

    STATUS_CLASS_MAP = {
        'active': 'primary',
        'reserved': 'info',
        'deprecated': 'danger',
    }

    class Meta:
        ordering = ('site', 'group', 'vid', 'pk')  # (site, group, vid) may be non-unique
        unique_together = [
            ['group', 'vid'],
            ['group', 'name'],
        ]
        verbose_name = 'VLAN'
        verbose_name_plural = 'VLANs'

    def __str__(self):
        return self.display_name or super().__str__()

    def get_absolute_url(self):
        return reverse('ipam:vlan', args=[self.pk])

    def clean(self):

        # Validate VLAN group
        if self.group and self.group.site != self.site:
            raise ValidationError({
                'group': "VLAN group must belong to the assigned site ({}).".format(self.site)
            })

    def to_csv(self):
        return (
            self.site.name if self.site else None,
            self.group.name if self.group else None,
            self.vid,
            self.name,
            self.tenant.name if self.tenant else None,
            self.get_status_display(),
            self.role.name if self.role else None,
            self.description,
        )

    @property
    def display_name(self):
        if self.vid and self.name:
            return "{} ({})".format(self.vid, self.name)
        return None

    def get_status_class(self):
        return self.STATUS_CLASS_MAP[self.status]

    def get_members(self):
        # Return all interfaces assigned to this VLAN
        return Interface.objects.filter(
            Q(untagged_vlan_id=self.pk) |
            Q(tagged_vlans=self.pk)
        ).distinct()


class Service(ChangeLoggedModel, CustomFieldModel):
    """
    A Service represents a layer-four service (e.g. HTTP or SSH) running on a Device or VirtualMachine. A Service may
    optionally be tied to one or more specific IPAddresses belonging to its parent.
    """
    device = models.ForeignKey(
        to='dcim.Device',
        on_delete=models.CASCADE,
        related_name='services',
        verbose_name='device',
        null=True,
        blank=True
    )
    virtual_machine = models.ForeignKey(
        to='virtualization.VirtualMachine',
        on_delete=models.CASCADE,
        related_name='services',
        null=True,
        blank=True
    )
    name = models.CharField(
        max_length=30
    )
    protocol = models.CharField(
        max_length=50,
        choices=ServiceProtocolChoices
    )
    port = models.PositiveIntegerField(
        validators=[MinValueValidator(SERVICE_PORT_MIN), MaxValueValidator(SERVICE_PORT_MAX)],
        verbose_name='Port number'
    )
    ipaddresses = models.ManyToManyField(
        to='ipam.IPAddress',
        related_name='services',
        blank=True,
        verbose_name='IP addresses'
    )
    description = models.CharField(
        max_length=100,
        blank=True
    )
    custom_field_values = GenericRelation(
        to='extras.CustomFieldValue',
        content_type_field='obj_type',
        object_id_field='obj_id'
    )

    tags = TaggableManager(through=TaggedItem)

    csv_headers = ['device', 'virtual_machine', 'name', 'protocol', 'description']

    class Meta:
        ordering = ('protocol', 'port', 'pk')  # (protocol, port) may be non-unique

    def __str__(self):
        return '{} ({}/{})'.format(self.name, self.port, self.get_protocol_display())

    def get_absolute_url(self):
        return reverse('ipam:service', args=[self.pk])

    @property
    def parent(self):
        return self.device or self.virtual_machine

    def clean(self):

        # A Service must belong to a Device *or* to a VirtualMachine
        if self.device and self.virtual_machine:
            raise ValidationError("A service cannot be associated with both a device and a virtual machine.")
        if not self.device and not self.virtual_machine:
            raise ValidationError("A service must be associated with either a device or a virtual machine.")

    def to_csv(self):
        return (
            self.device.name if self.device else None,
            self.virtual_machine.name if self.virtual_machine else None,
            self.name,
            self.get_protocol_display(),
            self.port,
            self.description,
        )
