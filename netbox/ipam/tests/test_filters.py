from django.test import TestCase

from dcim.models import Device, DeviceRole, DeviceType, Interface, Manufacturer, Region, Site
from ipam.choices import *
from ipam.filters import *
from ipam.models import Aggregate, IPAddress, Prefix, RIR, Role, Service, VLAN, VLANGroup, VRF
from virtualization.models import Cluster, ClusterType, VirtualMachine
from tenancy.models import Tenant, TenantGroup


class VRFTestCase(TestCase):
    queryset = VRF.objects.all()
    filterset = VRFFilterSet

    @classmethod
    def setUpTestData(cls):

        tenant_groups = (
            TenantGroup(name='Tenant group 1', slug='tenant-group-1'),
            TenantGroup(name='Tenant group 2', slug='tenant-group-2'),
            TenantGroup(name='Tenant group 3', slug='tenant-group-3'),
        )
        TenantGroup.objects.bulk_create(tenant_groups)

        tenants = (
            Tenant(name='Tenant 1', slug='tenant-1', group=tenant_groups[0]),
            Tenant(name='Tenant 2', slug='tenant-2', group=tenant_groups[1]),
            Tenant(name='Tenant 3', slug='tenant-3', group=tenant_groups[2]),
        )
        Tenant.objects.bulk_create(tenants)

        vrfs = (
            VRF(name='VRF 1', rd='65000:100', tenant=tenants[0], enforce_unique=False),
            VRF(name='VRF 2', rd='65000:200', tenant=tenants[0], enforce_unique=False),
            VRF(name='VRF 3', rd='65000:300', tenant=tenants[1], enforce_unique=False),
            VRF(name='VRF 4', rd='65000:400', tenant=tenants[1], enforce_unique=True),
            VRF(name='VRF 5', rd='65000:500', tenant=tenants[2], enforce_unique=True),
            VRF(name='VRF 6', rd='65000:600', tenant=tenants[2], enforce_unique=True),
        )
        VRF.objects.bulk_create(vrfs)

    def test_name(self):
        params = {'name': ['VRF 1', 'VRF 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_rd(self):
        params = {'rd': ['65000:100', '65000:200']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_enforce_unique(self):
        params = {'enforce_unique': 'true'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)
        params = {'enforce_unique': 'false'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_id__in(self):
        id_list = self.queryset.values_list('id', flat=True)[:3]
        params = {'id__in': ','.join([str(id) for id in id_list])}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_tenant(self):
        tenants = Tenant.objects.all()[:2]
        params = {'tenant_id': [tenants[0].pk, tenants[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)
        params = {'tenant': [tenants[0].slug, tenants[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)

    def test_tenant_group(self):
        tenant_groups = TenantGroup.objects.all()[:2]
        params = {'tenant_group_id': [tenant_groups[0].pk, tenant_groups[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)
        params = {'tenant_group': [tenant_groups[0].slug, tenant_groups[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)


class RIRTestCase(TestCase):
    queryset = RIR.objects.all()
    filterset = RIRFilterSet

    @classmethod
    def setUpTestData(cls):

        rirs = (
            RIR(name='RIR 1', slug='rir-1', is_private=False),
            RIR(name='RIR 2', slug='rir-2', is_private=False),
            RIR(name='RIR 3', slug='rir-3', is_private=False),
            RIR(name='RIR 4', slug='rir-4', is_private=True),
            RIR(name='RIR 5', slug='rir-5', is_private=True),
            RIR(name='RIR 6', slug='rir-6', is_private=True),
        )
        RIR.objects.bulk_create(rirs)

    def test_name(self):
        params = {'name': ['RIR 1', 'RIR 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_slug(self):
        params = {'slug': ['rir-1', 'rir-2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_is_private(self):
        params = {'is_private': 'true'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)
        params = {'is_private': 'false'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_id__in(self):
        id_list = self.queryset.values_list('id', flat=True)[:3]
        params = {'id__in': ','.join([str(id) for id in id_list])}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)


class AggregateTestCase(TestCase):
    queryset = Aggregate.objects.all()
    filterset = AggregateFilterSet

    @classmethod
    def setUpTestData(cls):

        rirs = (
            RIR(name='RIR 1', slug='rir-1'),
            RIR(name='RIR 2', slug='rir-2'),
            RIR(name='RIR 3', slug='rir-3'),
        )
        RIR.objects.bulk_create(rirs)

        aggregates = (
            Aggregate(family=4, prefix='10.1.0.0/16', rir=rirs[0], date_added='2020-01-01'),
            Aggregate(family=4, prefix='10.2.0.0/16', rir=rirs[0], date_added='2020-01-02'),
            Aggregate(family=4, prefix='10.3.0.0/16', rir=rirs[1], date_added='2020-01-03'),
            Aggregate(family=6, prefix='2001:db8:1::/48', rir=rirs[1], date_added='2020-01-04'),
            Aggregate(family=6, prefix='2001:db8:2::/48', rir=rirs[2], date_added='2020-01-05'),
            Aggregate(family=6, prefix='2001:db8:3::/48', rir=rirs[2], date_added='2020-01-06'),
        )
        Aggregate.objects.bulk_create(aggregates)

    def test_family(self):
        params = {'family': '4'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_date_added(self):
        params = {'date_added': ['2020-01-01', '2020-01-02']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    # TODO: Test for multiple values
    def test_prefix(self):
        params = {'prefix': '10.1.0.0/16'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_rir(self):
        rirs = RIR.objects.all()[:2]
        params = {'rir_id': [rirs[0].pk, rirs[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)
        params = {'rir': [rirs[0].slug, rirs[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)


class RoleTestCase(TestCase):
    queryset = Role.objects.all()
    filterset = RoleFilterSet

    @classmethod
    def setUpTestData(cls):

        roles = (
            Role(name='Role 1', slug='role-1'),
            Role(name='Role 2', slug='role-2'),
            Role(name='Role 3', slug='role-3'),
        )
        Role.objects.bulk_create(roles)

    def test_id(self):
        id_list = self.queryset.values_list('id', flat=True)[:2]
        params = {'id': [str(id) for id in id_list]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name(self):
        params = {'name': ['Role 1', 'Role 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_slug(self):
        params = {'slug': ['role-1', 'role-2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)


class PrefixTestCase(TestCase):
    queryset = Prefix.objects.all()
    filterset = PrefixFilterSet

    @classmethod
    def setUpTestData(cls):

        regions = (
            Region(name='Test Region 1', slug='test-region-1'),
            Region(name='Test Region 2', slug='test-region-2'),
            Region(name='Test Region 3', slug='test-region-3'),
        )
        # Can't use bulk_create for models with MPTT fields
        for r in regions:
            r.save()

        sites = (
            Site(name='Test Site 1', slug='test-site-1', region=regions[0]),
            Site(name='Test Site 2', slug='test-site-2', region=regions[1]),
            Site(name='Test Site 3', slug='test-site-3', region=regions[2]),
        )
        Site.objects.bulk_create(sites)

        vrfs = (
            VRF(name='VRF 1', rd='65000:100'),
            VRF(name='VRF 2', rd='65000:200'),
            VRF(name='VRF 3', rd='65000:300'),
        )
        VRF.objects.bulk_create(vrfs)

        vlans = (
            VLAN(vid=1, name='VLAN 1'),
            VLAN(vid=2, name='VLAN 2'),
            VLAN(vid=3, name='VLAN 3'),
        )
        VLAN.objects.bulk_create(vlans)

        roles = (
            Role(name='Role 1', slug='role-1'),
            Role(name='Role 2', slug='role-2'),
            Role(name='Role 3', slug='role-3'),
        )
        Role.objects.bulk_create(roles)

        tenant_groups = (
            TenantGroup(name='Tenant group 1', slug='tenant-group-1'),
            TenantGroup(name='Tenant group 2', slug='tenant-group-2'),
            TenantGroup(name='Tenant group 3', slug='tenant-group-3'),
        )
        TenantGroup.objects.bulk_create(tenant_groups)

        tenants = (
            Tenant(name='Tenant 1', slug='tenant-1', group=tenant_groups[0]),
            Tenant(name='Tenant 2', slug='tenant-2', group=tenant_groups[1]),
            Tenant(name='Tenant 3', slug='tenant-3', group=tenant_groups[2]),
        )
        Tenant.objects.bulk_create(tenants)

        prefixes = (
            Prefix(family=4, prefix='10.0.0.0/24', tenant=None, site=None, vrf=None, vlan=None, role=None, is_pool=True),
            Prefix(family=4, prefix='10.0.1.0/24', tenant=tenants[0], site=sites[0], vrf=vrfs[0], vlan=vlans[0], role=roles[0]),
            Prefix(family=4, prefix='10.0.2.0/24', tenant=tenants[1], site=sites[1], vrf=vrfs[1], vlan=vlans[1], role=roles[1], status=PrefixStatusChoices.STATUS_DEPRECATED),
            Prefix(family=4, prefix='10.0.3.0/24', tenant=tenants[2], site=sites[2], vrf=vrfs[2], vlan=vlans[2], role=roles[2], status=PrefixStatusChoices.STATUS_RESERVED),
            Prefix(family=6, prefix='2001:db8::/64', tenant=None, site=None, vrf=None, vlan=None, role=None, is_pool=True),
            Prefix(family=6, prefix='2001:db8:0:1::/64', tenant=tenants[0], site=sites[0], vrf=vrfs[0], vlan=vlans[0], role=roles[0]),
            Prefix(family=6, prefix='2001:db8:0:2::/64', tenant=tenants[1], site=sites[1], vrf=vrfs[1], vlan=vlans[1], role=roles[1], status=PrefixStatusChoices.STATUS_DEPRECATED),
            Prefix(family=6, prefix='2001:db8:0:3::/64', tenant=tenants[2], site=sites[2], vrf=vrfs[2], vlan=vlans[2], role=roles[2], status=PrefixStatusChoices.STATUS_RESERVED),
            Prefix(family=4, prefix='10.0.0.0/16'),
            Prefix(family=6, prefix='2001:db8::/32'),
        )
        Prefix.objects.bulk_create(prefixes)

    def test_family(self):
        params = {'family': '6'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 5)

    def test_is_pool(self):
        params = {'is_pool': 'true'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'is_pool': 'false'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 8)

    def test_id__in(self):
        id_list = self.queryset.values_list('id', flat=True)[:3]
        params = {'id__in': ','.join([str(id) for id in id_list])}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_within(self):
        params = {'within': '10.0.0.0/16'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)

    def test_within_include(self):
        params = {'within_include': '10.0.0.0/16'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 5)

    def test_contains(self):
        params = {'contains': '10.0.1.0/24'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'contains': '2001:db8:0:1::/64'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_mask_length(self):
        params = {'mask_length': '24'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)

    def test_vrf(self):
        vrfs = VRF.objects.all()[:2]
        params = {'vrf_id': [vrfs[0].pk, vrfs[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)
        params = {'vrf': [vrfs[0].rd, vrfs[1].rd]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)

    def test_region(self):
        regions = Region.objects.all()[:2]
        params = {'region_id': [regions[0].pk, regions[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)
        params = {'region': [regions[0].slug, regions[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)

    def test_site(self):
        sites = Site.objects.all()[:2]
        params = {'site_id': [sites[0].pk, sites[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)
        params = {'site': [sites[0].slug, sites[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)

    def test_vlan(self):
        vlans = VLAN.objects.all()[:2]
        params = {'vlan_id': [vlans[0].pk, vlans[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)
        # TODO: Test for multiple values
        params = {'vlan_vid': vlans[0].vid}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_role(self):
        roles = Role.objects.all()[:2]
        params = {'role_id': [roles[0].pk, roles[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)
        params = {'role': [roles[0].slug, roles[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)

    def test_status(self):
        params = {'status': [PrefixStatusChoices.STATUS_DEPRECATED, PrefixStatusChoices.STATUS_RESERVED]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)

    def test_tenant(self):
        tenants = Tenant.objects.all()[:2]
        params = {'tenant_id': [tenants[0].pk, tenants[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)
        params = {'tenant': [tenants[0].slug, tenants[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)

    def test_tenant_group(self):
        tenant_groups = TenantGroup.objects.all()[:2]
        params = {'tenant_group_id': [tenant_groups[0].pk, tenant_groups[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)
        params = {'tenant_group': [tenant_groups[0].slug, tenant_groups[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)


class IPAddressTestCase(TestCase):
    queryset = IPAddress.objects.all()
    filterset = IPAddressFilterSet

    @classmethod
    def setUpTestData(cls):

        vrfs = (
            VRF(name='VRF 1', rd='65000:100'),
            VRF(name='VRF 2', rd='65000:200'),
            VRF(name='VRF 3', rd='65000:300'),
        )
        VRF.objects.bulk_create(vrfs)

        site = Site.objects.create(name='Site 1', slug='site-1')
        manufacturer = Manufacturer.objects.create(name='Manufacturer 1', slug='manufacturer-1')
        device_type = DeviceType.objects.create(manufacturer=manufacturer, model='Device Type 1')
        device_role = DeviceRole.objects.create(name='Device Role 1', slug='device-role-1')

        devices = (
            Device(device_type=device_type, name='Device 1', site=site, device_role=device_role),
            Device(device_type=device_type, name='Device 2', site=site, device_role=device_role),
            Device(device_type=device_type, name='Device 3', site=site, device_role=device_role),
        )
        Device.objects.bulk_create(devices)

        clustertype = ClusterType.objects.create(name='Cluster Type 1', slug='cluster-type-1')
        cluster = Cluster.objects.create(type=clustertype, name='Cluster 1')

        virtual_machines = (
            VirtualMachine(name='Virtual Machine 1', cluster=cluster),
            VirtualMachine(name='Virtual Machine 2', cluster=cluster),
            VirtualMachine(name='Virtual Machine 3', cluster=cluster),
        )
        VirtualMachine.objects.bulk_create(virtual_machines)

        interfaces = (
            Interface(device=devices[0], name='Interface 1'),
            Interface(device=devices[1], name='Interface 2'),
            Interface(device=devices[2], name='Interface 3'),
            Interface(virtual_machine=virtual_machines[0], name='Interface 1'),
            Interface(virtual_machine=virtual_machines[1], name='Interface 2'),
            Interface(virtual_machine=virtual_machines[2], name='Interface 3'),
        )
        Interface.objects.bulk_create(interfaces)

        tenant_groups = (
            TenantGroup(name='Tenant group 1', slug='tenant-group-1'),
            TenantGroup(name='Tenant group 2', slug='tenant-group-2'),
            TenantGroup(name='Tenant group 3', slug='tenant-group-3'),
        )
        TenantGroup.objects.bulk_create(tenant_groups)

        tenants = (
            Tenant(name='Tenant 1', slug='tenant-1', group=tenant_groups[0]),
            Tenant(name='Tenant 2', slug='tenant-2', group=tenant_groups[1]),
            Tenant(name='Tenant 3', slug='tenant-3', group=tenant_groups[2]),
        )
        Tenant.objects.bulk_create(tenants)

        ipaddresses = (
            IPAddress(family=4, address='10.0.0.1/24', tenant=None, vrf=None, interface=None, status=IPAddressStatusChoices.STATUS_ACTIVE, dns_name='ipaddress-a'),
            IPAddress(family=4, address='10.0.0.2/24', tenant=tenants[0], vrf=vrfs[0], interface=interfaces[0], status=IPAddressStatusChoices.STATUS_ACTIVE, dns_name='ipaddress-b'),
            IPAddress(family=4, address='10.0.0.3/24', tenant=tenants[1], vrf=vrfs[1], interface=interfaces[1], status=IPAddressStatusChoices.STATUS_RESERVED, role=IPAddressRoleChoices.ROLE_VIP, dns_name='ipaddress-c'),
            IPAddress(family=4, address='10.0.0.4/24', tenant=tenants[2], vrf=vrfs[2], interface=interfaces[2], status=IPAddressStatusChoices.STATUS_DEPRECATED, role=IPAddressRoleChoices.ROLE_SECONDARY, dns_name='ipaddress-d'),
            IPAddress(family=4, address='10.0.0.1/25', tenant=None, vrf=None, interface=None, status=IPAddressStatusChoices.STATUS_ACTIVE),
            IPAddress(family=6, address='2001:db8::1/64', tenant=None, vrf=None, interface=None, status=IPAddressStatusChoices.STATUS_ACTIVE, dns_name='ipaddress-a'),
            IPAddress(family=6, address='2001:db8::2/64', tenant=tenants[0], vrf=vrfs[0], interface=interfaces[3], status=IPAddressStatusChoices.STATUS_ACTIVE, dns_name='ipaddress-b'),
            IPAddress(family=6, address='2001:db8::3/64', tenant=tenants[1], vrf=vrfs[1], interface=interfaces[4], status=IPAddressStatusChoices.STATUS_RESERVED, role=IPAddressRoleChoices.ROLE_VIP, dns_name='ipaddress-c'),
            IPAddress(family=6, address='2001:db8::4/64', tenant=tenants[2], vrf=vrfs[2], interface=interfaces[5], status=IPAddressStatusChoices.STATUS_DEPRECATED, role=IPAddressRoleChoices.ROLE_SECONDARY, dns_name='ipaddress-d'),
            IPAddress(family=6, address='2001:db8::1/65', tenant=None, vrf=None, interface=None, status=IPAddressStatusChoices.STATUS_ACTIVE),

        )
        IPAddress.objects.bulk_create(ipaddresses)

    def test_family(self):
        params = {'family': '6'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 5)

    def test_dns_name(self):
        params = {'dns_name': ['ipaddress-a', 'ipaddress-b']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)

    def test_id__in(self):
        id_list = self.queryset.values_list('id', flat=True)[:3]
        params = {'id__in': ','.join([str(id) for id in id_list])}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_parent(self):
        params = {'parent': '10.0.0.0/24'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 5)
        params = {'parent': '2001:db8::/64'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 5)

    def test_filter_address(self):
        # Check IPv4 and IPv6, with and without a mask
        params = {'address': ['10.0.0.1/24']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {'address': ['10.0.0.1']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'address': ['10.0.0.1/24', '10.0.0.1/25']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'address': ['2001:db8::1/64']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {'address': ['2001:db8::1']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'address': ['2001:db8::1/64', '2001:db8::1/65']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_mask_length(self):
        params = {'mask_length': '24'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)

    def test_vrf(self):
        vrfs = VRF.objects.all()[:2]
        params = {'vrf_id': [vrfs[0].pk, vrfs[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)
        params = {'vrf': [vrfs[0].rd, vrfs[1].rd]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)

    def test_device(self):
        devices = Device.objects.all()[:2]
        params = {'device_id': [devices[0].pk, devices[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'device': [devices[0].name, devices[1].name]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_virtual_machine(self):
        vms = VirtualMachine.objects.all()[:2]
        params = {'virtual_machine_id': [vms[0].pk, vms[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'virtual_machine': [vms[0].name, vms[1].name]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_interface(self):
        interfaces = Interface.objects.all()[:2]
        params = {'interface_id': [interfaces[0].pk, interfaces[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'interface': ['Interface 1', 'Interface 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)

    def test_assigned_to_interface(self):
        params = {'assigned_to_interface': 'true'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 6)
        params = {'assigned_to_interface': 'false'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)

    def test_status(self):
        params = {'status': [PrefixStatusChoices.STATUS_DEPRECATED, PrefixStatusChoices.STATUS_RESERVED]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)

    def test_role(self):
        params = {'role': [IPAddressRoleChoices.ROLE_SECONDARY, IPAddressRoleChoices.ROLE_VIP]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)

    def test_tenant(self):
        tenants = Tenant.objects.all()[:2]
        params = {'tenant_id': [tenants[0].pk, tenants[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)
        params = {'tenant': [tenants[0].slug, tenants[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)

    def test_tenant_group(self):
        tenant_groups = TenantGroup.objects.all()[:2]
        params = {'tenant_group_id': [tenant_groups[0].pk, tenant_groups[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)
        params = {'tenant_group': [tenant_groups[0].slug, tenant_groups[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)


class VLANGroupTestCase(TestCase):
    queryset = VLANGroup.objects.all()
    filterset = VLANGroupFilterSet

    @classmethod
    def setUpTestData(cls):

        regions = (
            Region(name='Test Region 1', slug='test-region-1'),
            Region(name='Test Region 2', slug='test-region-2'),
            Region(name='Test Region 3', slug='test-region-3'),
        )
        # Can't use bulk_create for models with MPTT fields
        for r in regions:
            r.save()

        sites = (
            Site(name='Test Site 1', slug='test-site-1', region=regions[0]),
            Site(name='Test Site 2', slug='test-site-2', region=regions[1]),
            Site(name='Test Site 3', slug='test-site-3', region=regions[2]),
        )
        Site.objects.bulk_create(sites)

        vlan_groups = (
            VLANGroup(name='VLAN Group 1', slug='vlan-group-1', site=sites[0]),
            VLANGroup(name='VLAN Group 2', slug='vlan-group-2', site=sites[1]),
            VLANGroup(name='VLAN Group 3', slug='vlan-group-3', site=sites[2]),
            VLANGroup(name='VLAN Group 4', slug='vlan-group-4', site=None),
        )
        VLANGroup.objects.bulk_create(vlan_groups)

    def test_id(self):
        id_list = self.queryset.values_list('id', flat=True)[:2]
        params = {'id': [str(id) for id in id_list]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name(self):
        params = {'name': ['VLAN Group 1', 'VLAN Group 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_slug(self):
        params = {'slug': ['vlan-group-1', 'vlan-group-2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_region(self):
        regions = Region.objects.all()[:2]
        params = {'region_id': [regions[0].pk, regions[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'region': [regions[0].slug, regions[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_site(self):
        sites = Site.objects.all()[:2]
        params = {'site_id': [sites[0].pk, sites[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'site': [sites[0].slug, sites[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)


class VLANTestCase(TestCase):
    queryset = VLAN.objects.all()
    filterset = VLANFilterSet

    @classmethod
    def setUpTestData(cls):

        regions = (
            Region(name='Test Region 1', slug='test-region-1'),
            Region(name='Test Region 2', slug='test-region-2'),
            Region(name='Test Region 3', slug='test-region-3'),
        )
        # Can't use bulk_create for models with MPTT fields
        for r in regions:
            r.save()

        sites = (
            Site(name='Test Site 1', slug='test-site-1', region=regions[0]),
            Site(name='Test Site 2', slug='test-site-2', region=regions[1]),
            Site(name='Test Site 3', slug='test-site-3', region=regions[2]),
        )
        Site.objects.bulk_create(sites)

        roles = (
            Role(name='Role 1', slug='role-1'),
            Role(name='Role 2', slug='role-2'),
            Role(name='Role 3', slug='role-3'),
        )
        Role.objects.bulk_create(roles)

        groups = (
            VLANGroup(name='VLAN Group 1', slug='vlan-group-1', site=sites[0]),
            VLANGroup(name='VLAN Group 2', slug='vlan-group-2', site=sites[1]),
            VLANGroup(name='VLAN Group 3', slug='vlan-group-3', site=None),
        )
        VLANGroup.objects.bulk_create(groups)

        tenant_groups = (
            TenantGroup(name='Tenant group 1', slug='tenant-group-1'),
            TenantGroup(name='Tenant group 2', slug='tenant-group-2'),
            TenantGroup(name='Tenant group 3', slug='tenant-group-3'),
        )
        TenantGroup.objects.bulk_create(tenant_groups)

        tenants = (
            Tenant(name='Tenant 1', slug='tenant-1', group=tenant_groups[0]),
            Tenant(name='Tenant 2', slug='tenant-2', group=tenant_groups[1]),
            Tenant(name='Tenant 3', slug='tenant-3', group=tenant_groups[2]),
        )
        Tenant.objects.bulk_create(tenants)

        vlans = (
            VLAN(vid=101, name='VLAN 101', site=sites[0], group=groups[0], role=roles[0], tenant=tenants[0], status=VLANStatusChoices.STATUS_ACTIVE),
            VLAN(vid=102, name='VLAN 102', site=sites[0], group=groups[0], role=roles[0], tenant=tenants[0], status=VLANStatusChoices.STATUS_ACTIVE),
            VLAN(vid=201, name='VLAN 201', site=sites[1], group=groups[1], role=roles[1], tenant=tenants[1], status=VLANStatusChoices.STATUS_DEPRECATED),
            VLAN(vid=202, name='VLAN 202', site=sites[1], group=groups[1], role=roles[1], tenant=tenants[1], status=VLANStatusChoices.STATUS_DEPRECATED),
            VLAN(vid=301, name='VLAN 301', site=sites[2], group=groups[2], role=roles[2], tenant=tenants[2], status=VLANStatusChoices.STATUS_RESERVED),
            VLAN(vid=302, name='VLAN 302', site=sites[2], group=groups[2], role=roles[2], tenant=tenants[2], status=VLANStatusChoices.STATUS_RESERVED),
        )
        VLAN.objects.bulk_create(vlans)

    def test_name(self):
        params = {'name': ['VLAN 101', 'VLAN 102']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_rd(self):
        params = {'vid': ['101', '201', '301']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_id__in(self):
        id_list = self.queryset.values_list('id', flat=True)[:3]
        params = {'id__in': ','.join([str(id) for id in id_list])}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_region(self):
        regions = Region.objects.all()[:2]
        params = {'region_id': [regions[0].pk, regions[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)
        params = {'region': [regions[0].slug, regions[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)

    def test_site(self):
        sites = Site.objects.all()[:2]
        params = {'site_id': [sites[0].pk, sites[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)
        params = {'site': [sites[0].slug, sites[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)

    def test_group(self):
        groups = VLANGroup.objects.all()[:2]
        params = {'group_id': [groups[0].pk, groups[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)
        params = {'group': [groups[0].slug, groups[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)

    def test_role(self):
        roles = Role.objects.all()[:2]
        params = {'role_id': [roles[0].pk, roles[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)
        params = {'role': [roles[0].slug, roles[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)

    def test_status(self):
        params = {'status': [VLANStatusChoices.STATUS_ACTIVE, VLANStatusChoices.STATUS_DEPRECATED]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)

    def test_tenant(self):
        tenants = Tenant.objects.all()[:2]
        params = {'tenant_id': [tenants[0].pk, tenants[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)
        params = {'tenant': [tenants[0].slug, tenants[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)

    def test_tenant_group(self):
        tenant_groups = TenantGroup.objects.all()[:2]
        params = {'tenant_group_id': [tenant_groups[0].pk, tenant_groups[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)
        params = {'tenant_group': [tenant_groups[0].slug, tenant_groups[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)


class ServiceTestCase(TestCase):
    queryset = Service.objects.all()
    filterset = ServiceFilterSet

    @classmethod
    def setUpTestData(cls):

        site = Site.objects.create(name='Site 1', slug='site-1')
        manufacturer = Manufacturer.objects.create(name='Manufacturer 1', slug='manufacturer-1')
        device_type = DeviceType.objects.create(manufacturer=manufacturer, model='Device Type 1')
        device_role = DeviceRole.objects.create(name='Device Role 1', slug='device-role-1')

        devices = (
            Device(device_type=device_type, name='Device 1', site=site, device_role=device_role),
            Device(device_type=device_type, name='Device 2', site=site, device_role=device_role),
            Device(device_type=device_type, name='Device 3', site=site, device_role=device_role),
        )
        Device.objects.bulk_create(devices)

        clustertype = ClusterType.objects.create(name='Cluster Type 1', slug='cluster-type-1')
        cluster = Cluster.objects.create(type=clustertype, name='Cluster 1')

        virtual_machines = (
            VirtualMachine(name='Virtual Machine 1', cluster=cluster),
            VirtualMachine(name='Virtual Machine 2', cluster=cluster),
            VirtualMachine(name='Virtual Machine 3', cluster=cluster),
        )
        VirtualMachine.objects.bulk_create(virtual_machines)

        services = (
            Service(device=devices[0], name='Service 1', protocol=ServiceProtocolChoices.PROTOCOL_TCP, port=1001),
            Service(device=devices[1], name='Service 2', protocol=ServiceProtocolChoices.PROTOCOL_TCP, port=1002),
            Service(device=devices[2], name='Service 3', protocol=ServiceProtocolChoices.PROTOCOL_UDP, port=1003),
            Service(virtual_machine=virtual_machines[0], name='Service 4', protocol=ServiceProtocolChoices.PROTOCOL_TCP, port=2001),
            Service(virtual_machine=virtual_machines[1], name='Service 5', protocol=ServiceProtocolChoices.PROTOCOL_TCP, port=2002),
            Service(virtual_machine=virtual_machines[2], name='Service 6', protocol=ServiceProtocolChoices.PROTOCOL_UDP, port=2003),
        )
        Service.objects.bulk_create(services)

    def test_id(self):
        id_list = self.queryset.values_list('id', flat=True)[:3]
        params = {'id': [str(id) for id in id_list]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_name(self):
        params = {'name': ['Service 1', 'Service 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_protocol(self):
        params = {'protocol': ServiceProtocolChoices.PROTOCOL_TCP}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)

    def test_port(self):
        params = {'port': ['1001', '1002', '1003']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_device(self):
        devices = Device.objects.all()[:2]
        params = {'device_id': [devices[0].pk, devices[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'device': [devices[0].name, devices[1].name]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_virtual_machine(self):
        vms = VirtualMachine.objects.all()[:2]
        params = {'virtual_machine_id': [vms[0].pk, vms[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'virtual_machine': [vms[0].name, vms[1].name]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
