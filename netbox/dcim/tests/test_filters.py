from django.contrib.auth.models import User
from django.test import TestCase

from dcim.choices import *
from dcim.filters import *
from dcim.models import (
    Cable, ConsolePort, ConsolePortTemplate, ConsoleServerPort, ConsoleServerPortTemplate, Device, DeviceBay,
    DeviceBayTemplate, DeviceRole, DeviceType, FrontPort, FrontPortTemplate, Interface, InterfaceTemplate,
    InventoryItem, Manufacturer, Platform, PowerFeed, PowerPanel, PowerPort, PowerPortTemplate, PowerOutlet,
    PowerOutletTemplate, Rack, RackGroup, RackReservation, RackRole, RearPort, RearPortTemplate, Region, Site,
    VirtualChassis,
)
from ipam.models import IPAddress
from tenancy.models import Tenant, TenantGroup
from virtualization.models import Cluster, ClusterType


class RegionTestCase(TestCase):
    queryset = Region.objects.all()

    @classmethod
    def setUpTestData(cls):

        regions = (
            Region(name='Region 1', slug='region-1'),
            Region(name='Region 2', slug='region-2'),
            Region(name='Region 3', slug='region-3'),
        )
        for region in regions:
            region.save()

        child_regions = (
            Region(name='Region 1A', slug='region-1a', parent=regions[0]),
            Region(name='Region 1B', slug='region-1b', parent=regions[0]),
            Region(name='Region 2A', slug='region-2a', parent=regions[1]),
            Region(name='Region 2B', slug='region-2b', parent=regions[1]),
            Region(name='Region 3A', slug='region-3a', parent=regions[2]),
            Region(name='Region 3B', slug='region-3b', parent=regions[2]),
        )
        for region in child_regions:
            region.save()

    def test_id(self):
        id_list = self.queryset.values_list('id', flat=True)[:2]
        params = {'id': [str(id) for id in id_list]}
        self.assertEqual(RegionFilterSet(params, self.queryset).qs.count(), 2)

    def test_name(self):
        params = {'name': ['Region 1', 'Region 2']}
        self.assertEqual(RegionFilterSet(params, self.queryset).qs.count(), 2)

    def test_slug(self):
        params = {'slug': ['region-1', 'region-2']}
        self.assertEqual(RegionFilterSet(params, self.queryset).qs.count(), 2)

    def test_parent(self):
        parent_regions = Region.objects.filter(parent__isnull=True)[:2]
        params = {'parent_id': [parent_regions[0].pk, parent_regions[1].pk]}
        self.assertEqual(RegionFilterSet(params, self.queryset).qs.count(), 4)
        params = {'parent': [parent_regions[0].slug, parent_regions[1].slug]}
        self.assertEqual(RegionFilterSet(params, self.queryset).qs.count(), 4)


class SiteTestCase(TestCase):
    queryset = Site.objects.all()
    filterset = SiteFilterSet

    @classmethod
    def setUpTestData(cls):

        regions = (
            Region(name='Region 1', slug='region-1'),
            Region(name='Region 2', slug='region-2'),
            Region(name='Region 3', slug='region-3'),
        )
        for region in regions:
            region.save()

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

        sites = (
            Site(name='Site 1', slug='site-1', region=regions[0], tenant=tenants[0], status=SiteStatusChoices.STATUS_ACTIVE, facility='Facility 1', asn=65001, latitude=10, longitude=10, contact_name='Contact 1', contact_phone='123-555-0001', contact_email='contact1@example.com'),
            Site(name='Site 2', slug='site-2', region=regions[1], tenant=tenants[1], status=SiteStatusChoices.STATUS_PLANNED, facility='Facility 2', asn=65002, latitude=20, longitude=20, contact_name='Contact 2', contact_phone='123-555-0002', contact_email='contact2@example.com'),
            Site(name='Site 3', slug='site-3', region=regions[2], tenant=tenants[2], status=SiteStatusChoices.STATUS_RETIRED, facility='Facility 3', asn=65003, latitude=30, longitude=30, contact_name='Contact 3', contact_phone='123-555-0003', contact_email='contact3@example.com'),
        )
        Site.objects.bulk_create(sites)

    def test_id(self):
        id_list = self.queryset.values_list('id', flat=True)[:2]
        params = {'id': [str(id) for id in id_list]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name(self):
        params = {'name': ['Site 1', 'Site 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_slug(self):
        params = {'slug': ['site-1', 'site-2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_facility(self):
        params = {'facility': ['Facility 1', 'Facility 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_asn(self):
        params = {'asn': [65001, 65002]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_latitude(self):
        params = {'latitude': [10, 20]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_longitude(self):
        params = {'longitude': [10, 20]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_contact_name(self):
        params = {'contact_name': ['Contact 1', 'Contact 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_contact_phone(self):
        params = {'contact_phone': ['123-555-0001', '123-555-0002']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_contact_email(self):
        params = {'contact_email': ['contact1@example.com', 'contact2@example.com']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_id__in(self):
        id_list = self.queryset.values_list('id', flat=True)[:2]
        params = {'id__in': ','.join([str(id) for id in id_list])}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_status(self):
        params = {'status': [SiteStatusChoices.STATUS_ACTIVE, SiteStatusChoices.STATUS_PLANNED]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_region(self):
        regions = Region.objects.all()[:2]
        params = {'region_id': [regions[0].pk, regions[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'region': [regions[0].slug, regions[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_tenant(self):
        tenants = Tenant.objects.all()[:2]
        params = {'tenant_id': [tenants[0].pk, tenants[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'tenant': [tenants[0].slug, tenants[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_tenant_group(self):
        tenant_groups = TenantGroup.objects.all()[:2]
        params = {'tenant_group_id': [tenant_groups[0].pk, tenant_groups[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'tenant_group': [tenant_groups[0].slug, tenant_groups[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)


class RackGroupTestCase(TestCase):
    queryset = RackGroup.objects.all()
    filterset = RackGroupFilterSet

    @classmethod
    def setUpTestData(cls):

        regions = (
            Region(name='Region 1', slug='region-1'),
            Region(name='Region 2', slug='region-2'),
            Region(name='Region 3', slug='region-3'),
        )
        for region in regions:
            region.save()

        sites = (
            Site(name='Site 1', slug='site-1', region=regions[0]),
            Site(name='Site 2', slug='site-2', region=regions[1]),
            Site(name='Site 3', slug='site-3', region=regions[2]),
        )
        Site.objects.bulk_create(sites)

        rack_groups = (
            RackGroup(name='Rack Group 1', slug='rack-group-1', site=sites[0]),
            RackGroup(name='Rack Group 2', slug='rack-group-2', site=sites[1]),
            RackGroup(name='Rack Group 3', slug='rack-group-3', site=sites[2]),
        )
        RackGroup.objects.bulk_create(rack_groups)

    def test_id(self):
        id_list = self.queryset.values_list('id', flat=True)[:2]
        params = {'id': [str(id) for id in id_list]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name(self):
        params = {'name': ['Rack Group 1', 'Rack Group 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_slug(self):
        params = {'slug': ['rack-group-1', 'rack-group-2']}
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


class RackRoleTestCase(TestCase):
    queryset = RackRole.objects.all()
    filterset = RackRoleFilterSet

    @classmethod
    def setUpTestData(cls):

        rack_roles = (
            RackRole(name='Rack Role 1', slug='rack-role-1', color='ff0000'),
            RackRole(name='Rack Role 2', slug='rack-role-2', color='00ff00'),
            RackRole(name='Rack Role 3', slug='rack-role-3', color='0000ff'),
        )
        RackRole.objects.bulk_create(rack_roles)

    def test_id(self):
        id_list = self.queryset.values_list('id', flat=True)[:2]
        params = {'id': [str(id) for id in id_list]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name(self):
        params = {'name': ['Rack Role 1', 'Rack Role 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_slug(self):
        params = {'slug': ['rack-role-1', 'rack-role-2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_color(self):
        params = {'color': ['ff0000', '00ff00']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)


class RackTestCase(TestCase):
    queryset = Rack.objects.all()
    filterset = RackFilterSet

    @classmethod
    def setUpTestData(cls):

        regions = (
            Region(name='Region 1', slug='region-1'),
            Region(name='Region 2', slug='region-2'),
            Region(name='Region 3', slug='region-3'),
        )
        for region in regions:
            region.save()

        sites = (
            Site(name='Site 1', slug='site-1', region=regions[0]),
            Site(name='Site 2', slug='site-2', region=regions[1]),
            Site(name='Site 3', slug='site-3', region=regions[2]),
        )
        Site.objects.bulk_create(sites)

        rack_groups = (
            RackGroup(name='Rack Group 1', slug='rack-group-1', site=sites[0]),
            RackGroup(name='Rack Group 2', slug='rack-group-2', site=sites[1]),
            RackGroup(name='Rack Group 3', slug='rack-group-3', site=sites[2]),
        )
        RackGroup.objects.bulk_create(rack_groups)

        rack_roles = (
            RackRole(name='Rack Role 1', slug='rack-role-1'),
            RackRole(name='Rack Role 2', slug='rack-role-2'),
            RackRole(name='Rack Role 3', slug='rack-role-3'),
        )
        RackRole.objects.bulk_create(rack_roles)

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

        racks = (
            Rack(name='Rack 1', facility_id='rack-1', site=sites[0], group=rack_groups[0], tenant=tenants[0], status=RackStatusChoices.STATUS_ACTIVE, role=rack_roles[0], serial='ABC', asset_tag='1001', type=RackTypeChoices.TYPE_2POST, width=RackWidthChoices.WIDTH_19IN, u_height=42, desc_units=False, outer_width=100, outer_depth=100, outer_unit=RackDimensionUnitChoices.UNIT_MILLIMETER),
            Rack(name='Rack 2', facility_id='rack-2', site=sites[1], group=rack_groups[1], tenant=tenants[1], status=RackStatusChoices.STATUS_PLANNED, role=rack_roles[1], serial='DEF', asset_tag='1002', type=RackTypeChoices.TYPE_4POST, width=RackWidthChoices.WIDTH_19IN, u_height=43, desc_units=False, outer_width=200, outer_depth=200, outer_unit=RackDimensionUnitChoices.UNIT_MILLIMETER),
            Rack(name='Rack 3', facility_id='rack-3', site=sites[2], group=rack_groups[2], tenant=tenants[2], status=RackStatusChoices.STATUS_RESERVED, role=rack_roles[2], serial='GHI', asset_tag='1003', type=RackTypeChoices.TYPE_CABINET, width=RackWidthChoices.WIDTH_23IN, u_height=44, desc_units=True, outer_width=300, outer_depth=300, outer_unit=RackDimensionUnitChoices.UNIT_INCH),
        )
        Rack.objects.bulk_create(racks)

    def test_id(self):
        id_list = self.queryset.values_list('id', flat=True)[:2]
        params = {'id': [str(id) for id in id_list]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name(self):
        params = {'name': ['Rack 1', 'Rack 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_facility_id(self):
        params = {'facility_id': ['rack-1', 'rack-2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_asset_tag(self):
        params = {'asset_tag': ['1001', '1002']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_type(self):
        # TODO: Test for multiple values
        params = {'type': RackTypeChoices.TYPE_2POST}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_width(self):
        # TODO: Test for multiple values
        params = {'width': RackWidthChoices.WIDTH_19IN}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_u_height(self):
        params = {'u_height': [42, 43]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_desc_units(self):
        params = {'desc_units': 'true'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {'desc_units': 'false'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_outer_width(self):
        params = {'outer_width': [100, 200]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_outer_depth(self):
        params = {'outer_depth': [100, 200]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_outer_unit(self):
        self.assertEqual(Rack.objects.filter(outer_unit__isnull=False).count(), 3)
        params = {'outer_unit': RackDimensionUnitChoices.UNIT_MILLIMETER}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_id__in(self):
        id_list = self.queryset.values_list('id', flat=True)[:2]
        params = {'id__in': ','.join([str(id) for id in id_list])}
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

    def test_group(self):
        groups = RackGroup.objects.all()[:2]
        params = {'group_id': [groups[0].pk, groups[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'group': [groups[0].slug, groups[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_status(self):
        params = {'status': [RackStatusChoices.STATUS_ACTIVE, RackStatusChoices.STATUS_PLANNED]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_role(self):
        roles = RackRole.objects.all()[:2]
        params = {'role_id': [roles[0].pk, roles[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'role': [roles[0].slug, roles[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_serial(self):
        params = {'serial': 'ABC'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {'serial': 'abc'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_tenant(self):
        tenants = Tenant.objects.all()[:2]
        params = {'tenant_id': [tenants[0].pk, tenants[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'tenant': [tenants[0].slug, tenants[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_tenant_group(self):
        tenant_groups = TenantGroup.objects.all()[:2]
        params = {'tenant_group_id': [tenant_groups[0].pk, tenant_groups[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'tenant_group': [tenant_groups[0].slug, tenant_groups[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)


class RackReservationTestCase(TestCase):
    queryset = RackReservation.objects.all()
    filterset = RackReservationFilterSet

    @classmethod
    def setUpTestData(cls):

        sites = (
            Site(name='Site 1', slug='site-1'),
            Site(name='Site 2', slug='site-2'),
            Site(name='Site 3', slug='site-3'),
        )
        Site.objects.bulk_create(sites)

        rack_groups = (
            RackGroup(name='Rack Group 1', slug='rack-group-1', site=sites[0]),
            RackGroup(name='Rack Group 2', slug='rack-group-2', site=sites[1]),
            RackGroup(name='Rack Group 3', slug='rack-group-3', site=sites[2]),
        )
        RackGroup.objects.bulk_create(rack_groups)

        racks = (
            Rack(name='Rack 1', site=sites[0], group=rack_groups[0]),
            Rack(name='Rack 2', site=sites[1], group=rack_groups[1]),
            Rack(name='Rack 3', site=sites[2], group=rack_groups[2]),
        )
        Rack.objects.bulk_create(racks)

        users = (
            User(username='User 1'),
            User(username='User 2'),
            User(username='User 3'),
        )
        User.objects.bulk_create(users)

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

        reservations = (
            RackReservation(rack=racks[0], units=[1, 2, 3], user=users[0], tenant=tenants[0]),
            RackReservation(rack=racks[1], units=[4, 5, 6], user=users[1], tenant=tenants[1]),
            RackReservation(rack=racks[2], units=[7, 8, 9], user=users[2], tenant=tenants[2]),
        )
        RackReservation.objects.bulk_create(reservations)

    def test_id__in(self):
        id_list = self.queryset.values_list('id', flat=True)[:2]
        params = {'id__in': ','.join([str(id) for id in id_list])}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_site(self):
        sites = Site.objects.all()[:2]
        params = {'site_id': [sites[0].pk, sites[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'site': [sites[0].slug, sites[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_group(self):
        groups = RackGroup.objects.all()[:2]
        params = {'group_id': [groups[0].pk, groups[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'group': [groups[0].slug, groups[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_user(self):
        users = User.objects.all()[:2]
        params = {'user_id': [users[0].pk, users[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        # TODO: Filtering by username is broken
        # params = {'user': [users[0].username, users[1].username]}
        # self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_tenant(self):
        tenants = Tenant.objects.all()[:2]
        params = {'tenant_id': [tenants[0].pk, tenants[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'tenant': [tenants[0].slug, tenants[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_tenant_group(self):
        tenant_groups = TenantGroup.objects.all()[:2]
        params = {'tenant_group_id': [tenant_groups[0].pk, tenant_groups[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'tenant_group': [tenant_groups[0].slug, tenant_groups[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)


class ManufacturerTestCase(TestCase):
    queryset = Manufacturer.objects.all()
    filterset = ManufacturerFilterSet

    @classmethod
    def setUpTestData(cls):

        manufacturers = (
            Manufacturer(name='Manufacturer 1', slug='manufacturer-1'),
            Manufacturer(name='Manufacturer 2', slug='manufacturer-2'),
            Manufacturer(name='Manufacturer 3', slug='manufacturer-3'),
        )
        Manufacturer.objects.bulk_create(manufacturers)

    def test_id(self):
        id_list = self.queryset.values_list('id', flat=True)[:2]
        params = {'id': [str(id) for id in id_list]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name(self):
        params = {'name': ['Manufacturer 1', 'Manufacturer 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_slug(self):
        params = {'slug': ['manufacturer-1', 'manufacturer-2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)


class DeviceTypeTestCase(TestCase):
    queryset = DeviceType.objects.all()
    filterset = DeviceTypeFilterSet

    @classmethod
    def setUpTestData(cls):

        manufacturers = (
            Manufacturer(name='Manufacturer 1', slug='manufacturer-1'),
            Manufacturer(name='Manufacturer 2', slug='manufacturer-2'),
            Manufacturer(name='Manufacturer 3', slug='manufacturer-3'),
        )
        Manufacturer.objects.bulk_create(manufacturers)

        device_types = (
            DeviceType(manufacturer=manufacturers[0], model='Model 1', slug='model-1', part_number='Part Number 1', u_height=1, is_full_depth=True),
            DeviceType(manufacturer=manufacturers[1], model='Model 2', slug='model-2', part_number='Part Number 2', u_height=2, is_full_depth=True, subdevice_role=SubdeviceRoleChoices.ROLE_PARENT),
            DeviceType(manufacturer=manufacturers[2], model='Model 3', slug='model-3', part_number='Part Number 3', u_height=3, is_full_depth=False, subdevice_role=SubdeviceRoleChoices.ROLE_CHILD),
        )
        DeviceType.objects.bulk_create(device_types)

        # Add component templates for filtering
        ConsolePortTemplate.objects.bulk_create((
            ConsolePortTemplate(device_type=device_types[0], name='Console Port 1'),
            ConsolePortTemplate(device_type=device_types[1], name='Console Port 2'),
        ))
        ConsoleServerPortTemplate.objects.bulk_create((
            ConsoleServerPortTemplate(device_type=device_types[0], name='Console Server Port 1'),
            ConsoleServerPortTemplate(device_type=device_types[1], name='Console Server Port 2'),
        ))
        PowerPortTemplate.objects.bulk_create((
            PowerPortTemplate(device_type=device_types[0], name='Power Port 1'),
            PowerPortTemplate(device_type=device_types[1], name='Power Port 2'),
        ))
        PowerOutletTemplate.objects.bulk_create((
            PowerOutletTemplate(device_type=device_types[0], name='Power Outlet 1'),
            PowerOutletTemplate(device_type=device_types[1], name='Power Outlet 2'),
        ))
        InterfaceTemplate.objects.bulk_create((
            InterfaceTemplate(device_type=device_types[0], name='Interface 1'),
            InterfaceTemplate(device_type=device_types[1], name='Interface 2'),
        ))
        rear_ports = (
            RearPortTemplate(device_type=device_types[0], name='Rear Port 1', type=PortTypeChoices.TYPE_8P8C),
            RearPortTemplate(device_type=device_types[1], name='Rear Port 2', type=PortTypeChoices.TYPE_8P8C),
        )
        RearPortTemplate.objects.bulk_create(rear_ports)
        FrontPortTemplate.objects.bulk_create((
            FrontPortTemplate(device_type=device_types[0], name='Front Port 1', type=PortTypeChoices.TYPE_8P8C, rear_port=rear_ports[0]),
            FrontPortTemplate(device_type=device_types[1], name='Front Port 2', type=PortTypeChoices.TYPE_8P8C, rear_port=rear_ports[1]),
        ))
        DeviceBayTemplate.objects.bulk_create((
            DeviceBayTemplate(device_type=device_types[0], name='Device Bay 1'),
            DeviceBayTemplate(device_type=device_types[1], name='Device Bay 2'),
        ))

    def test_model(self):
        params = {'model': ['Model 1', 'Model 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_slug(self):
        params = {'slug': ['model-1', 'model-2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_part_number(self):
        params = {'part_number': ['Part Number 1', 'Part Number 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_u_height(self):
        params = {'u_height': [1, 2]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_is_full_depth(self):
        params = {'is_full_depth': 'true'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'is_full_depth': 'false'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_subdevice_role(self):
        params = {'subdevice_role': SubdeviceRoleChoices.ROLE_PARENT}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_id__in(self):
        id_list = self.queryset.values_list('id', flat=True)[:2]
        params = {'id__in': ','.join([str(id) for id in id_list])}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_manufacturer(self):
        manufacturers = Manufacturer.objects.all()[:2]
        params = {'manufacturer_id': [manufacturers[0].pk, manufacturers[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'manufacturer': [manufacturers[0].slug, manufacturers[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_console_ports(self):
        params = {'console_ports': 'true'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'console_ports': 'false'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_console_server_ports(self):
        params = {'console_server_ports': 'true'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'console_server_ports': 'false'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_power_ports(self):
        params = {'power_ports': 'true'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'power_ports': 'false'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_power_outlets(self):
        params = {'power_outlets': 'true'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'power_outlets': 'false'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_interfaces(self):
        params = {'interfaces': 'true'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'interfaces': 'false'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_pass_through_ports(self):
        params = {'pass_through_ports': 'true'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'pass_through_ports': 'false'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_device_bays(self):
        params = {'device_bays': 'true'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'device_bays': 'false'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)


class ConsolePortTemplateTestCase(TestCase):
    queryset = ConsolePortTemplate.objects.all()
    filterset = ConsolePortTemplateFilterSet

    @classmethod
    def setUpTestData(cls):

        manufacturer = Manufacturer.objects.create(name='Manufacturer 1', slug='manufacturer-1')

        device_types = (
            DeviceType(manufacturer=manufacturer, model='Model 1', slug='model-1'),
            DeviceType(manufacturer=manufacturer, model='Model 2', slug='model-2'),
            DeviceType(manufacturer=manufacturer, model='Model 3', slug='model-3'),
        )
        DeviceType.objects.bulk_create(device_types)

        ConsolePortTemplate.objects.bulk_create((
            ConsolePortTemplate(device_type=device_types[0], name='Console Port 1'),
            ConsolePortTemplate(device_type=device_types[1], name='Console Port 2'),
            ConsolePortTemplate(device_type=device_types[2], name='Console Port 3'),
        ))

    def test_id(self):
        id_list = self.queryset.values_list('id', flat=True)[:2]
        params = {'id': [str(id) for id in id_list]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name(self):
        params = {'name': ['Console Port 1', 'Console Port 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_devicetype_id(self):
        device_types = DeviceType.objects.all()[:2]
        params = {'devicetype_id': [device_types[0].pk, device_types[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)


class ConsoleServerPortTemplateTestCase(TestCase):
    queryset = ConsoleServerPortTemplate.objects.all()
    filterset = ConsoleServerPortTemplateFilterSet

    @classmethod
    def setUpTestData(cls):

        manufacturer = Manufacturer.objects.create(name='Manufacturer 1', slug='manufacturer-1')

        device_types = (
            DeviceType(manufacturer=manufacturer, model='Model 1', slug='model-1'),
            DeviceType(manufacturer=manufacturer, model='Model 2', slug='model-2'),
            DeviceType(manufacturer=manufacturer, model='Model 3', slug='model-3'),
        )
        DeviceType.objects.bulk_create(device_types)

        ConsoleServerPortTemplate.objects.bulk_create((
            ConsoleServerPortTemplate(device_type=device_types[0], name='Console Server Port 1'),
            ConsoleServerPortTemplate(device_type=device_types[1], name='Console Server Port 2'),
            ConsoleServerPortTemplate(device_type=device_types[2], name='Console Server Port 3'),
        ))

    def test_id(self):
        id_list = self.queryset.values_list('id', flat=True)[:2]
        params = {'id': [str(id) for id in id_list]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name(self):
        params = {'name': ['Console Server Port 1', 'Console Server Port 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_devicetype_id(self):
        device_types = DeviceType.objects.all()[:2]
        params = {'devicetype_id': [device_types[0].pk, device_types[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)


class PowerPortTemplateTestCase(TestCase):
    queryset = PowerPortTemplate.objects.all()
    filterset = PowerPortTemplateFilterSet

    @classmethod
    def setUpTestData(cls):

        manufacturer = Manufacturer.objects.create(name='Manufacturer 1', slug='manufacturer-1')

        device_types = (
            DeviceType(manufacturer=manufacturer, model='Model 1', slug='model-1'),
            DeviceType(manufacturer=manufacturer, model='Model 2', slug='model-2'),
            DeviceType(manufacturer=manufacturer, model='Model 3', slug='model-3'),
        )
        DeviceType.objects.bulk_create(device_types)

        PowerPortTemplate.objects.bulk_create((
            PowerPortTemplate(device_type=device_types[0], name='Power Port 1', maximum_draw=100, allocated_draw=50),
            PowerPortTemplate(device_type=device_types[1], name='Power Port 2', maximum_draw=200, allocated_draw=100),
            PowerPortTemplate(device_type=device_types[2], name='Power Port 3', maximum_draw=300, allocated_draw=150),
        ))

    def test_id(self):
        id_list = self.queryset.values_list('id', flat=True)[:2]
        params = {'id': [str(id) for id in id_list]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name(self):
        params = {'name': ['Power Port 1', 'Power Port 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_devicetype_id(self):
        device_types = DeviceType.objects.all()[:2]
        params = {'devicetype_id': [device_types[0].pk, device_types[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_maximum_draw(self):
        params = {'maximum_draw': [100, 200]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_allocated_draw(self):
        params = {'allocated_draw': [50, 100]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)


class PowerOutletTemplateTestCase(TestCase):
    queryset = PowerOutletTemplate.objects.all()
    filterset = PowerOutletTemplateFilterSet

    @classmethod
    def setUpTestData(cls):

        manufacturer = Manufacturer.objects.create(name='Manufacturer 1', slug='manufacturer-1')

        device_types = (
            DeviceType(manufacturer=manufacturer, model='Model 1', slug='model-1'),
            DeviceType(manufacturer=manufacturer, model='Model 2', slug='model-2'),
            DeviceType(manufacturer=manufacturer, model='Model 3', slug='model-3'),
        )
        DeviceType.objects.bulk_create(device_types)

        PowerOutletTemplate.objects.bulk_create((
            PowerOutletTemplate(device_type=device_types[0], name='Power Outlet 1', feed_leg=PowerOutletFeedLegChoices.FEED_LEG_A),
            PowerOutletTemplate(device_type=device_types[1], name='Power Outlet 2', feed_leg=PowerOutletFeedLegChoices.FEED_LEG_B),
            PowerOutletTemplate(device_type=device_types[2], name='Power Outlet 3', feed_leg=PowerOutletFeedLegChoices.FEED_LEG_C),
        ))

    def test_id(self):
        id_list = self.queryset.values_list('id', flat=True)[:2]
        params = {'id': [str(id) for id in id_list]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name(self):
        params = {'name': ['Power Outlet 1', 'Power Outlet 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_devicetype_id(self):
        device_types = DeviceType.objects.all()[:2]
        params = {'devicetype_id': [device_types[0].pk, device_types[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_feed_leg(self):
        # TODO: Support filtering for multiple values
        params = {'feed_leg': PowerOutletFeedLegChoices.FEED_LEG_A}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)


class InterfaceTemplateTestCase(TestCase):
    queryset = InterfaceTemplate.objects.all()
    filterset = InterfaceTemplateFilterSet

    @classmethod
    def setUpTestData(cls):

        manufacturer = Manufacturer.objects.create(name='Manufacturer 1', slug='manufacturer-1')

        device_types = (
            DeviceType(manufacturer=manufacturer, model='Model 1', slug='model-1'),
            DeviceType(manufacturer=manufacturer, model='Model 2', slug='model-2'),
            DeviceType(manufacturer=manufacturer, model='Model 3', slug='model-3'),
        )
        DeviceType.objects.bulk_create(device_types)

        InterfaceTemplate.objects.bulk_create((
            InterfaceTemplate(device_type=device_types[0], name='Interface 1', type=InterfaceTypeChoices.TYPE_1GE_FIXED, mgmt_only=True),
            InterfaceTemplate(device_type=device_types[1], name='Interface 2', type=InterfaceTypeChoices.TYPE_1GE_GBIC, mgmt_only=False),
            InterfaceTemplate(device_type=device_types[2], name='Interface 3', type=InterfaceTypeChoices.TYPE_1GE_SFP, mgmt_only=False),
        ))

    def test_id(self):
        id_list = self.queryset.values_list('id', flat=True)[:2]
        params = {'id': [str(id) for id in id_list]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name(self):
        params = {'name': ['Interface 1', 'Interface 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_devicetype_id(self):
        device_types = DeviceType.objects.all()[:2]
        params = {'devicetype_id': [device_types[0].pk, device_types[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_type(self):
        # TODO: Support filtering for multiple values
        params = {'type': InterfaceTypeChoices.TYPE_1GE_FIXED}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_mgmt_only(self):
        params = {'mgmt_only': 'true'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {'mgmt_only': 'false'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)


class FrontPortTemplateTestCase(TestCase):
    queryset = FrontPortTemplate.objects.all()
    filterset = FrontPortTemplateFilterSet

    @classmethod
    def setUpTestData(cls):

        manufacturer = Manufacturer.objects.create(name='Manufacturer 1', slug='manufacturer-1')

        device_types = (
            DeviceType(manufacturer=manufacturer, model='Model 1', slug='model-1'),
            DeviceType(manufacturer=manufacturer, model='Model 2', slug='model-2'),
            DeviceType(manufacturer=manufacturer, model='Model 3', slug='model-3'),
        )
        DeviceType.objects.bulk_create(device_types)

        rear_ports = (
            RearPortTemplate(device_type=device_types[0], name='Rear Port 1', type=PortTypeChoices.TYPE_8P8C),
            RearPortTemplate(device_type=device_types[1], name='Rear Port 2', type=PortTypeChoices.TYPE_8P8C),
            RearPortTemplate(device_type=device_types[2], name='Rear Port 3', type=PortTypeChoices.TYPE_8P8C),
        )
        RearPortTemplate.objects.bulk_create(rear_ports)

        FrontPortTemplate.objects.bulk_create((
            FrontPortTemplate(device_type=device_types[0], name='Front Port 1', rear_port=rear_ports[0], type=PortTypeChoices.TYPE_8P8C),
            FrontPortTemplate(device_type=device_types[1], name='Front Port 2', rear_port=rear_ports[1], type=PortTypeChoices.TYPE_110_PUNCH),
            FrontPortTemplate(device_type=device_types[2], name='Front Port 3', rear_port=rear_ports[2], type=PortTypeChoices.TYPE_BNC),
        ))

    def test_id(self):
        id_list = self.queryset.values_list('id', flat=True)[:2]
        params = {'id': [str(id) for id in id_list]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name(self):
        params = {'name': ['Front Port 1', 'Front Port 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_devicetype_id(self):
        device_types = DeviceType.objects.all()[:2]
        params = {'devicetype_id': [device_types[0].pk, device_types[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_type(self):
        # TODO: Support filtering for multiple values
        params = {'type': PortTypeChoices.TYPE_8P8C}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)


class RearPortTemplateTestCase(TestCase):
    queryset = RearPortTemplate.objects.all()
    filterset = RearPortTemplateFilterSet

    @classmethod
    def setUpTestData(cls):

        manufacturer = Manufacturer.objects.create(name='Manufacturer 1', slug='manufacturer-1')

        device_types = (
            DeviceType(manufacturer=manufacturer, model='Model 1', slug='model-1'),
            DeviceType(manufacturer=manufacturer, model='Model 2', slug='model-2'),
            DeviceType(manufacturer=manufacturer, model='Model 3', slug='model-3'),
        )
        DeviceType.objects.bulk_create(device_types)

        RearPortTemplate.objects.bulk_create((
            RearPortTemplate(device_type=device_types[0], name='Rear Port 1', type=PortTypeChoices.TYPE_8P8C, positions=1),
            RearPortTemplate(device_type=device_types[1], name='Rear Port 2', type=PortTypeChoices.TYPE_110_PUNCH, positions=2),
            RearPortTemplate(device_type=device_types[2], name='Rear Port 3', type=PortTypeChoices.TYPE_BNC, positions=3),
        ))

    def test_id(self):
        id_list = self.queryset.values_list('id', flat=True)[:2]
        params = {'id': [str(id) for id in id_list]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name(self):
        params = {'name': ['Rear Port 1', 'Rear Port 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_devicetype_id(self):
        device_types = DeviceType.objects.all()[:2]
        params = {'devicetype_id': [device_types[0].pk, device_types[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_type(self):
        # TODO: Support filtering for multiple values
        params = {'type': PortTypeChoices.TYPE_8P8C}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_positions(self):
        params = {'positions': [1, 2]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)


class DeviceBayTemplateTestCase(TestCase):
    queryset = DeviceBayTemplate.objects.all()
    filterset = DeviceBayTemplateFilterSet

    @classmethod
    def setUpTestData(cls):

        manufacturer = Manufacturer.objects.create(name='Manufacturer 1', slug='manufacturer-1')

        device_types = (
            DeviceType(manufacturer=manufacturer, model='Model 1', slug='model-1'),
            DeviceType(manufacturer=manufacturer, model='Model 2', slug='model-2'),
            DeviceType(manufacturer=manufacturer, model='Model 3', slug='model-3'),
        )
        DeviceType.objects.bulk_create(device_types)

        DeviceBayTemplate.objects.bulk_create((
            DeviceBayTemplate(device_type=device_types[0], name='Device Bay 1'),
            DeviceBayTemplate(device_type=device_types[1], name='Device Bay 2'),
            DeviceBayTemplate(device_type=device_types[2], name='Device Bay 3'),
        ))

    def test_id(self):
        id_list = self.queryset.values_list('id', flat=True)[:2]
        params = {'id': [str(id) for id in id_list]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name(self):
        params = {'name': ['Device Bay 1', 'Device Bay 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_devicetype_id(self):
        device_types = DeviceType.objects.all()[:2]
        params = {'devicetype_id': [device_types[0].pk, device_types[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)


class DeviceRoleTestCase(TestCase):
    queryset = DeviceRole.objects.all()
    filterset = DeviceRoleFilterSet

    @classmethod
    def setUpTestData(cls):

        device_roles = (
            DeviceRole(name='Device Role 1', slug='device-role-1', color='ff0000', vm_role=True),
            DeviceRole(name='Device Role 2', slug='device-role-2', color='00ff00', vm_role=True),
            DeviceRole(name='Device Role 3', slug='device-role-3', color='0000ff', vm_role=False),
        )
        DeviceRole.objects.bulk_create(device_roles)

    def test_id(self):
        id_list = self.queryset.values_list('id', flat=True)[:2]
        params = {'id': [str(id) for id in id_list]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name(self):
        params = {'name': ['Device Role 1', 'Device Role 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_slug(self):
        params = {'slug': ['device-role-1', 'device-role-2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_color(self):
        params = {'color': ['ff0000', '00ff00']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_vm_role(self):
        params = {'vm_role': 'true'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'vm_role': 'false'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)


class PlatformTestCase(TestCase):
    queryset = Platform.objects.all()
    filterset = PlatformFilterSet

    @classmethod
    def setUpTestData(cls):

        manufacturers = (
            Manufacturer(name='Manufacturer 1', slug='manufacturer-1'),
            Manufacturer(name='Manufacturer 2', slug='manufacturer-2'),
            Manufacturer(name='Manufacturer 3', slug='manufacturer-3'),
        )
        Manufacturer.objects.bulk_create(manufacturers)

        platforms = (
            Platform(name='Platform 1', slug='platform-1', manufacturer=manufacturers[0], napalm_driver='driver-1'),
            Platform(name='Platform 2', slug='platform-2', manufacturer=manufacturers[1], napalm_driver='driver-2'),
            Platform(name='Platform 3', slug='platform-3', manufacturer=manufacturers[2], napalm_driver='driver-3'),
        )
        Platform.objects.bulk_create(platforms)

    def test_id(self):
        id_list = self.queryset.values_list('id', flat=True)[:2]
        params = {'id': [str(id) for id in id_list]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name(self):
        params = {'name': ['Platform 1', 'Platform 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_slug(self):
        params = {'slug': ['platform-1', 'platform-2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_napalm_driver(self):
        params = {'napalm_driver': ['driver-1', 'driver-2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_manufacturer(self):
        manufacturers = Manufacturer.objects.all()[:2]
        params = {'manufacturer_id': [manufacturers[0].pk, manufacturers[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'manufacturer': [manufacturers[0].slug, manufacturers[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)


class DeviceTestCase(TestCase):
    queryset = Device.objects.all()
    filterset = DeviceFilterSet

    @classmethod
    def setUpTestData(cls):

        manufacturers = (
            Manufacturer(name='Manufacturer 1', slug='manufacturer-1'),
            Manufacturer(name='Manufacturer 2', slug='manufacturer-2'),
            Manufacturer(name='Manufacturer 3', slug='manufacturer-3'),
        )
        Manufacturer.objects.bulk_create(manufacturers)

        device_types = (
            DeviceType(manufacturer=manufacturers[0], model='Model 1', slug='model-1', is_full_depth=True),
            DeviceType(manufacturer=manufacturers[1], model='Model 2', slug='model-2', is_full_depth=True),
            DeviceType(manufacturer=manufacturers[2], model='Model 3', slug='model-3', is_full_depth=False),
        )
        DeviceType.objects.bulk_create(device_types)

        device_roles = (
            DeviceRole(name='Device Role 1', slug='device-role-1'),
            DeviceRole(name='Device Role 2', slug='device-role-2'),
            DeviceRole(name='Device Role 3', slug='device-role-3'),
        )
        DeviceRole.objects.bulk_create(device_roles)

        platforms = (
            Platform(name='Platform 1', slug='platform-1'),
            Platform(name='Platform 2', slug='platform-2'),
            Platform(name='Platform 3', slug='platform-3'),
        )
        Platform.objects.bulk_create(platforms)

        regions = (
            Region(name='Region 1', slug='region-1'),
            Region(name='Region 2', slug='region-2'),
            Region(name='Region 3', slug='region-3'),
        )
        for region in regions:
            region.save()

        sites = (
            Site(name='Site 1', slug='site-1', region=regions[0]),
            Site(name='Site 2', slug='site-2', region=regions[1]),
            Site(name='Site 3', slug='site-3', region=regions[2]),
        )
        Site.objects.bulk_create(sites)

        rack_groups = (
            RackGroup(name='Rack Group 1', slug='rack-group-1', site=sites[0]),
            RackGroup(name='Rack Group 2', slug='rack-group-2', site=sites[1]),
            RackGroup(name='Rack Group 3', slug='rack-group-3', site=sites[2]),
        )
        RackGroup.objects.bulk_create(rack_groups)

        racks = (
            Rack(name='Rack 1', site=sites[0], group=rack_groups[0]),
            Rack(name='Rack 2', site=sites[1], group=rack_groups[1]),
            Rack(name='Rack 3', site=sites[2], group=rack_groups[2]),
        )
        Rack.objects.bulk_create(racks)

        cluster_type = ClusterType.objects.create(name='Cluster Type 1', slug='cluster-type-1')
        clusters = (
            Cluster(name='Cluster 1', type=cluster_type),
            Cluster(name='Cluster 2', type=cluster_type),
            Cluster(name='Cluster 3', type=cluster_type),
        )
        Cluster.objects.bulk_create(clusters)

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

        devices = (
            Device(name='Device 1', device_type=device_types[0], device_role=device_roles[0], platform=platforms[0], tenant=tenants[0], serial='ABC', asset_tag='1001', site=sites[0], rack=racks[0], position=1, face=DeviceFaceChoices.FACE_FRONT, status=DeviceStatusChoices.STATUS_ACTIVE, cluster=clusters[0], local_context_data={"foo": 123}),
            Device(name='Device 2', device_type=device_types[1], device_role=device_roles[1], platform=platforms[1], tenant=tenants[1], serial='DEF', asset_tag='1002', site=sites[1], rack=racks[1], position=2, face=DeviceFaceChoices.FACE_FRONT, status=DeviceStatusChoices.STATUS_STAGED, cluster=clusters[1]),
            Device(name='Device 3', device_type=device_types[2], device_role=device_roles[2], platform=platforms[2], tenant=tenants[2], serial='GHI', asset_tag='1003', site=sites[2], rack=racks[2], position=3, face=DeviceFaceChoices.FACE_REAR, status=DeviceStatusChoices.STATUS_FAILED, cluster=clusters[2]),
        )
        Device.objects.bulk_create(devices)

        # Add components for filtering
        ConsolePort.objects.bulk_create((
            ConsolePort(device=devices[0], name='Console Port 1'),
            ConsolePort(device=devices[1], name='Console Port 2'),
        ))
        ConsoleServerPort.objects.bulk_create((
            ConsoleServerPort(device=devices[0], name='Console Server Port 1'),
            ConsoleServerPort(device=devices[1], name='Console Server Port 2'),
        ))
        PowerPort.objects.bulk_create((
            PowerPort(device=devices[0], name='Power Port 1'),
            PowerPort(device=devices[1], name='Power Port 2'),
        ))
        PowerOutlet.objects.bulk_create((
            PowerOutlet(device=devices[0], name='Power Outlet 1'),
            PowerOutlet(device=devices[1], name='Power Outlet 2'),
        ))
        interfaces = (
            Interface(device=devices[0], name='Interface 1', mac_address='00-00-00-00-00-01'),
            Interface(device=devices[1], name='Interface 2', mac_address='00-00-00-00-00-02'),
        )
        Interface.objects.bulk_create(interfaces)
        rear_ports = (
            RearPort(device=devices[0], name='Rear Port 1', type=PortTypeChoices.TYPE_8P8C),
            RearPort(device=devices[1], name='Rear Port 2', type=PortTypeChoices.TYPE_8P8C),
        )
        RearPort.objects.bulk_create(rear_ports)
        FrontPort.objects.bulk_create((
            FrontPort(device=devices[0], name='Front Port 1', type=PortTypeChoices.TYPE_8P8C, rear_port=rear_ports[0]),
            FrontPort(device=devices[1], name='Front Port 2', type=PortTypeChoices.TYPE_8P8C, rear_port=rear_ports[1]),
        ))
        DeviceBay.objects.bulk_create((
            DeviceBay(device=devices[0], name='Device Bay 1'),
            DeviceBay(device=devices[1], name='Device Bay 2'),
        ))

        # Assign primary IPs for filtering
        ipaddresses = (
            IPAddress(family=4, address='192.0.2.1/24', interface=interfaces[0]),
            IPAddress(family=4, address='192.0.2.2/24', interface=interfaces[1]),
        )
        IPAddress.objects.bulk_create(ipaddresses)
        Device.objects.filter(pk=devices[0].pk).update(primary_ip4=ipaddresses[0])
        Device.objects.filter(pk=devices[1].pk).update(primary_ip4=ipaddresses[1])

        # VirtualChassis assignment for filtering
        virtual_chassis = VirtualChassis.objects.create(master=devices[0])
        Device.objects.filter(pk=devices[0].pk).update(virtual_chassis=virtual_chassis, vc_position=1, vc_priority=1)
        Device.objects.filter(pk=devices[1].pk).update(virtual_chassis=virtual_chassis, vc_position=2, vc_priority=2)

    def test_id(self):
        id_list = self.queryset.values_list('id', flat=True)[:2]
        params = {'id': [str(id) for id in id_list]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name(self):
        params = {'name': ['Device 1', 'Device 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_asset_tag(self):
        params = {'asset_tag': ['1001', '1002']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_face(self):
        params = {'face': DeviceFaceChoices.FACE_FRONT}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_position(self):
        params = {'position': [1, 2]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_vc_position(self):
        params = {'vc_position': [1, 2]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_vc_priority(self):
        params = {'vc_priority': [1, 2]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_id__in(self):
        id_list = self.queryset.values_list('id', flat=True)[:2]
        params = {'id__in': ','.join([str(id) for id in id_list])}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_manufacturer(self):
        manufacturers = Manufacturer.objects.all()[:2]
        params = {'manufacturer_id': [manufacturers[0].pk, manufacturers[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'manufacturer': [manufacturers[0].slug, manufacturers[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_devicetype(self):
        device_types = DeviceType.objects.all()[:2]
        params = {'device_type_id': [device_types[0].pk, device_types[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_devicerole(self):
        device_roles = DeviceRole.objects.all()[:2]
        params = {'role_id': [device_roles[0].pk, device_roles[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'role': [device_roles[0].slug, device_roles[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_platform(self):
        platforms = Platform.objects.all()[:2]
        params = {'platform_id': [platforms[0].pk, platforms[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'platform': [platforms[0].slug, platforms[1].slug]}
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

    def test_rackgroup(self):
        rack_groups = RackGroup.objects.all()[:2]
        params = {'rack_group_id': [rack_groups[0].pk, rack_groups[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_rack(self):
        racks = Rack.objects.all()[:2]
        params = {'rack_id': [racks[0].pk, racks[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_cluster(self):
        clusters = Cluster.objects.all()[:2]
        params = {'cluster_id': [clusters[0].pk, clusters[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_model(self):
        params = {'model': ['model-1', 'model-2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_status(self):
        params = {'status': [DeviceStatusChoices.STATUS_ACTIVE, DeviceStatusChoices.STATUS_STAGED]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_is_full_depth(self):
        params = {'is_full_depth': 'true'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'is_full_depth': 'false'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_mac_address(self):
        params = {'mac_address': ['00-00-00-00-00-01', '00-00-00-00-00-02']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_serial(self):
        params = {'serial': 'ABC'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {'serial': 'abc'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_has_primary_ip(self):
        params = {'has_primary_ip': 'true'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'has_primary_ip': 'false'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_virtual_chassis_id(self):
        params = {'virtual_chassis_id': [VirtualChassis.objects.first().pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_virtual_chassis_member(self):
        params = {'virtual_chassis_member': 'true'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'virtual_chassis_member': 'false'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_console_ports(self):
        params = {'console_ports': 'true'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'console_ports': 'false'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_console_server_ports(self):
        params = {'console_server_ports': 'true'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'console_server_ports': 'false'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_power_ports(self):
        params = {'power_ports': 'true'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'power_ports': 'false'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_power_outlets(self):
        params = {'power_outlets': 'true'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'power_outlets': 'false'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_interfaces(self):
        params = {'interfaces': 'true'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'interfaces': 'false'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_pass_through_ports(self):
        params = {'pass_through_ports': 'true'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'pass_through_ports': 'false'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_device_bays(self):
        params = {'device_bays': 'true'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'device_bays': 'false'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_local_context_data(self):
        params = {'local_context_data': 'true'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {'local_context_data': 'false'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_tenant(self):
        tenants = Tenant.objects.all()[:2]
        params = {'tenant_id': [tenants[0].pk, tenants[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'tenant': [tenants[0].slug, tenants[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_tenant_group(self):
        tenant_groups = TenantGroup.objects.all()[:2]
        params = {'tenant_group_id': [tenant_groups[0].pk, tenant_groups[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'tenant_group': [tenant_groups[0].slug, tenant_groups[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)


class ConsolePortTestCase(TestCase):
    queryset = ConsolePort.objects.all()
    filterset = ConsolePortFilterSet

    @classmethod
    def setUpTestData(cls):

        regions = (
            Region(name='Region 1', slug='region-1'),
            Region(name='Region 2', slug='region-2'),
            Region(name='Region 3', slug='region-3'),
        )
        for region in regions:
            region.save()
        sites = Site.objects.bulk_create((
            Site(name='Site 1', slug='site-1', region=regions[0]),
            Site(name='Site 2', slug='site-2', region=regions[1]),
            Site(name='Site 3', slug='site-3', region=regions[2]),
            Site(name='Site X', slug='site-x'),
        ))
        manufacturer = Manufacturer.objects.create(name='Manufacturer 1', slug='manufacturer-1')
        device_type = DeviceType.objects.create(manufacturer=manufacturer, model='Model 1', slug='model-1')
        device_role = DeviceRole.objects.create(name='Device Role 1', slug='device-role-1')

        devices = (
            Device(name='Device 1', device_type=device_type, device_role=device_role, site=sites[0]),
            Device(name='Device 2', device_type=device_type, device_role=device_role, site=sites[1]),
            Device(name='Device 3', device_type=device_type, device_role=device_role, site=sites[2]),
            Device(name=None, device_type=device_type, device_role=device_role, site=sites[3]),  # For cable connections
        )
        Device.objects.bulk_create(devices)

        console_server_ports = (
            ConsoleServerPort(device=devices[3], name='Console Server Port 1'),
            ConsoleServerPort(device=devices[3], name='Console Server Port 2'),
        )
        ConsoleServerPort.objects.bulk_create(console_server_ports)

        console_ports = (
            ConsolePort(device=devices[0], name='Console Port 1', description='First'),
            ConsolePort(device=devices[1], name='Console Port 2', description='Second'),
            ConsolePort(device=devices[2], name='Console Port 3', description='Third'),
        )
        ConsolePort.objects.bulk_create(console_ports)

        # Cables
        Cable(termination_a=console_ports[0], termination_b=console_server_ports[0]).save()
        Cable(termination_a=console_ports[1], termination_b=console_server_ports[1]).save()
        # Third port is not connected

    def test_id(self):
        id_list = self.queryset.values_list('id', flat=True)[:2]
        params = {'id': [str(id) for id in id_list]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name(self):
        params = {'name': ['Console Port 1', 'Console Port 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_description(self):
        params = {'description': ['First', 'Second']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    # TODO: Fix boolean value
    def test_connection_status(self):
        params = {'connection_status': 'True'}
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

    def test_device(self):
        devices = Device.objects.all()[:2]
        params = {'device_id': [devices[0].pk, devices[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'device': [devices[0].name, devices[1].name]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_cabled(self):
        params = {'cabled': 'true'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'cabled': 'false'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)


class ConsoleServerPortTestCase(TestCase):
    queryset = ConsoleServerPort.objects.all()
    filterset = ConsoleServerPortFilterSet

    @classmethod
    def setUpTestData(cls):

        regions = (
            Region(name='Region 1', slug='region-1'),
            Region(name='Region 2', slug='region-2'),
            Region(name='Region 3', slug='region-3'),
        )
        for region in regions:
            region.save()
        sites = Site.objects.bulk_create((
            Site(name='Site 1', slug='site-1', region=regions[0]),
            Site(name='Site 2', slug='site-2', region=regions[1]),
            Site(name='Site 3', slug='site-3', region=regions[2]),
            Site(name='Site X', slug='site-x'),
        ))
        manufacturer = Manufacturer.objects.create(name='Manufacturer 1', slug='manufacturer-1')
        device_type = DeviceType.objects.create(manufacturer=manufacturer, model='Model 1', slug='model-1')
        device_role = DeviceRole.objects.create(name='Device Role 1', slug='device-role-1')

        devices = (
            Device(name='Device 1', device_type=device_type, device_role=device_role, site=sites[0]),
            Device(name='Device 2', device_type=device_type, device_role=device_role, site=sites[1]),
            Device(name='Device 3', device_type=device_type, device_role=device_role, site=sites[2]),
            Device(name=None, device_type=device_type, device_role=device_role, site=sites[3]),  # For cable connections
        )
        Device.objects.bulk_create(devices)

        console_ports = (
            ConsolePort(device=devices[3], name='Console Server Port 1'),
            ConsolePort(device=devices[3], name='Console Server Port 2'),
        )
        ConsolePort.objects.bulk_create(console_ports)

        console_server_ports = (
            ConsoleServerPort(device=devices[0], name='Console Server Port 1', description='First'),
            ConsoleServerPort(device=devices[1], name='Console Server Port 2', description='Second'),
            ConsoleServerPort(device=devices[2], name='Console Server Port 3', description='Third'),
        )
        ConsoleServerPort.objects.bulk_create(console_server_ports)

        # Cables
        Cable(termination_a=console_server_ports[0], termination_b=console_ports[0]).save()
        Cable(termination_a=console_server_ports[1], termination_b=console_ports[1]).save()
        # Third port is not connected

    def test_id(self):
        id_list = self.queryset.values_list('id', flat=True)[:2]
        params = {'id': [str(id) for id in id_list]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name(self):
        params = {'name': ['Console Server Port 1', 'Console Server Port 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_description(self):
        params = {'description': ['First', 'Second']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    # TODO: Fix boolean value
    def test_connection_status(self):
        params = {'connection_status': 'True'}
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

    def test_device(self):
        devices = Device.objects.all()[:2]
        params = {'device_id': [devices[0].pk, devices[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'device': [devices[0].name, devices[1].name]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_cabled(self):
        params = {'cabled': 'true'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'cabled': 'false'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)


class PowerPortTestCase(TestCase):
    queryset = PowerPort.objects.all()
    filterset = PowerPortFilterSet

    @classmethod
    def setUpTestData(cls):

        regions = (
            Region(name='Region 1', slug='region-1'),
            Region(name='Region 2', slug='region-2'),
            Region(name='Region 3', slug='region-3'),
        )
        for region in regions:
            region.save()
        sites = Site.objects.bulk_create((
            Site(name='Site 1', slug='site-1', region=regions[0]),
            Site(name='Site 2', slug='site-2', region=regions[1]),
            Site(name='Site 3', slug='site-3', region=regions[2]),
            Site(name='Site X', slug='site-x'),
        ))
        manufacturer = Manufacturer.objects.create(name='Manufacturer 1', slug='manufacturer-1')
        device_type = DeviceType.objects.create(manufacturer=manufacturer, model='Model 1', slug='model-1')
        device_role = DeviceRole.objects.create(name='Device Role 1', slug='device-role-1')

        devices = (
            Device(name='Device 1', device_type=device_type, device_role=device_role, site=sites[0]),
            Device(name='Device 2', device_type=device_type, device_role=device_role, site=sites[1]),
            Device(name='Device 3', device_type=device_type, device_role=device_role, site=sites[2]),
            Device(name=None, device_type=device_type, device_role=device_role, site=sites[3]),  # For cable connections
        )
        Device.objects.bulk_create(devices)

        power_outlets = (
            PowerOutlet(device=devices[3], name='Power Outlet 1'),
            PowerOutlet(device=devices[3], name='Power Outlet 2'),
        )
        PowerOutlet.objects.bulk_create(power_outlets)

        power_ports = (
            PowerPort(device=devices[0], name='Power Port 1', maximum_draw=100, allocated_draw=50, description='First'),
            PowerPort(device=devices[1], name='Power Port 2', maximum_draw=200, allocated_draw=100, description='Second'),
            PowerPort(device=devices[2], name='Power Port 3', maximum_draw=300, allocated_draw=150, description='Third'),
        )
        PowerPort.objects.bulk_create(power_ports)

        # Cables
        Cable(termination_a=power_ports[0], termination_b=power_outlets[0]).save()
        Cable(termination_a=power_ports[1], termination_b=power_outlets[1]).save()
        # Third port is not connected

    def test_id(self):
        id_list = self.queryset.values_list('id', flat=True)[:2]
        params = {'id': [str(id) for id in id_list]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name(self):
        params = {'name': ['Power Port 1', 'Power Port 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_description(self):
        params = {'description': ['First', 'Second']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_maximum_draw(self):
        params = {'maximum_draw': [100, 200]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_allocated_draw(self):
        params = {'allocated_draw': [50, 100]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    # TODO: Fix boolean value
    def test_connection_status(self):
        params = {'connection_status': 'True'}
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

    def test_device(self):
        devices = Device.objects.all()[:2]
        params = {'device_id': [devices[0].pk, devices[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'device': [devices[0].name, devices[1].name]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_cabled(self):
        params = {'cabled': 'true'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'cabled': 'false'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)


class PowerOutletTestCase(TestCase):
    queryset = PowerOutlet.objects.all()
    filterset = PowerOutletFilterSet

    @classmethod
    def setUpTestData(cls):

        regions = (
            Region(name='Region 1', slug='region-1'),
            Region(name='Region 2', slug='region-2'),
            Region(name='Region 3', slug='region-3'),
        )
        for region in regions:
            region.save()
        sites = Site.objects.bulk_create((
            Site(name='Site 1', slug='site-1', region=regions[0]),
            Site(name='Site 2', slug='site-2', region=regions[1]),
            Site(name='Site 3', slug='site-3', region=regions[2]),
            Site(name='Site X', slug='site-x'),
        ))
        manufacturer = Manufacturer.objects.create(name='Manufacturer 1', slug='manufacturer-1')
        device_type = DeviceType.objects.create(manufacturer=manufacturer, model='Model 1', slug='model-1')
        device_role = DeviceRole.objects.create(name='Device Role 1', slug='device-role-1')

        devices = (
            Device(name='Device 1', device_type=device_type, device_role=device_role, site=sites[0]),
            Device(name='Device 2', device_type=device_type, device_role=device_role, site=sites[1]),
            Device(name='Device 3', device_type=device_type, device_role=device_role, site=sites[2]),
            Device(name=None, device_type=device_type, device_role=device_role, site=sites[3]),  # For cable connections
        )
        Device.objects.bulk_create(devices)

        power_ports = (
            PowerPort(device=devices[3], name='Power Outlet 1'),
            PowerPort(device=devices[3], name='Power Outlet 2'),
        )
        PowerPort.objects.bulk_create(power_ports)

        power_outlets = (
            PowerOutlet(device=devices[0], name='Power Outlet 1', feed_leg=PowerOutletFeedLegChoices.FEED_LEG_A, description='First'),
            PowerOutlet(device=devices[1], name='Power Outlet 2', feed_leg=PowerOutletFeedLegChoices.FEED_LEG_B, description='Second'),
            PowerOutlet(device=devices[2], name='Power Outlet 3', feed_leg=PowerOutletFeedLegChoices.FEED_LEG_C, description='Third'),
        )
        PowerOutlet.objects.bulk_create(power_outlets)

        # Cables
        Cable(termination_a=power_outlets[0], termination_b=power_ports[0]).save()
        Cable(termination_a=power_outlets[1], termination_b=power_ports[1]).save()
        # Third port is not connected

    def test_id(self):
        id_list = self.queryset.values_list('id', flat=True)[:2]
        params = {'id': [str(id) for id in id_list]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name(self):
        params = {'name': ['Power Outlet 1', 'Power Outlet 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_description(self):
        params = {'description': ['First', 'Second']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_feed_leg(self):
        # TODO: Support filtering for multiple values
        params = {'feed_leg': PowerOutletFeedLegChoices.FEED_LEG_A}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    # TODO: Fix boolean value
    def test_connection_status(self):
        params = {'connection_status': 'True'}
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

    def test_device(self):
        devices = Device.objects.all()[:2]
        params = {'device_id': [devices[0].pk, devices[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'device': [devices[0].name, devices[1].name]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_cabled(self):
        params = {'cabled': 'true'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'cabled': 'false'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)


class InterfaceTestCase(TestCase):
    queryset = Interface.objects.all()
    filterset = InterfaceFilterSet

    @classmethod
    def setUpTestData(cls):

        regions = (
            Region(name='Region 1', slug='region-1'),
            Region(name='Region 2', slug='region-2'),
            Region(name='Region 3', slug='region-3'),
        )
        for region in regions:
            region.save()
        sites = Site.objects.bulk_create((
            Site(name='Site 1', slug='site-1', region=regions[0]),
            Site(name='Site 2', slug='site-2', region=regions[1]),
            Site(name='Site 3', slug='site-3', region=regions[2]),
            Site(name='Site X', slug='site-x'),
        ))
        manufacturer = Manufacturer.objects.create(name='Manufacturer 1', slug='manufacturer-1')
        device_type = DeviceType.objects.create(manufacturer=manufacturer, model='Model 1', slug='model-1')
        device_role = DeviceRole.objects.create(name='Device Role 1', slug='device-role-1')

        devices = (
            Device(name='Device 1', device_type=device_type, device_role=device_role, site=sites[0]),
            Device(name='Device 2', device_type=device_type, device_role=device_role, site=sites[1]),
            Device(name='Device 3', device_type=device_type, device_role=device_role, site=sites[2]),
            Device(name=None, device_type=device_type, device_role=device_role, site=sites[3]),  # For cable connections
        )
        Device.objects.bulk_create(devices)

        interfaces = (
            Interface(device=devices[0], name='Interface 1', type=InterfaceTypeChoices.TYPE_1GE_SFP, enabled=True, mgmt_only=True, mtu=100, mode=InterfaceModeChoices.MODE_ACCESS, mac_address='00-00-00-00-00-01', description='First'),
            Interface(device=devices[1], name='Interface 2', type=InterfaceTypeChoices.TYPE_1GE_GBIC, enabled=True, mgmt_only=True, mtu=200, mode=InterfaceModeChoices.MODE_TAGGED, mac_address='00-00-00-00-00-02', description='Second'),
            Interface(device=devices[2], name='Interface 3', type=InterfaceTypeChoices.TYPE_1GE_FIXED, enabled=False, mgmt_only=False, mtu=300, mode=InterfaceModeChoices.MODE_TAGGED_ALL, mac_address='00-00-00-00-00-03', description='Third'),
            Interface(device=devices[3], name='Interface 4', type=InterfaceTypeChoices.TYPE_OTHER, enabled=True, mgmt_only=True),
            Interface(device=devices[3], name='Interface 5', type=InterfaceTypeChoices.TYPE_OTHER, enabled=True, mgmt_only=True),
            Interface(device=devices[3], name='Interface 6', type=InterfaceTypeChoices.TYPE_OTHER, enabled=False, mgmt_only=False),
        )
        Interface.objects.bulk_create(interfaces)

        # Cables
        Cable(termination_a=interfaces[0], termination_b=interfaces[3]).save()
        Cable(termination_a=interfaces[1], termination_b=interfaces[4]).save()
        # Third pair is not connected

    def test_id(self):
        id_list = self.queryset.values_list('id', flat=True)[:3]
        params = {'id': [str(id) for id in id_list]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_name(self):
        params = {'name': ['Interface 1', 'Interface 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    # TODO: Fix boolean value
    def test_connection_status(self):
        params = {'connection_status': 'True'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)

    def test_enabled(self):
        params = {'enabled': 'true'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)
        params = {'enabled': 'false'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_mtu(self):
        params = {'mtu': [100, 200]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_mgmt_only(self):
        params = {'mgmt_only': 'true'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)
        params = {'mgmt_only': 'false'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_mode(self):
        params = {'mode': InterfaceModeChoices.MODE_ACCESS}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_description(self):
        params = {'description': ['First', 'Second']}
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

    def test_device(self):
        devices = Device.objects.all()[:2]
        params = {'device_id': [devices[0].pk, devices[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'device': [devices[0].name, devices[1].name]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_cabled(self):
        params = {'cabled': 'true'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)
        params = {'cabled': 'false'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_kind(self):
        params = {'kind': 'physical'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 6)
        params = {'kind': 'virtual'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)

    def test_mac_address(self):
        params = {'mac_address': ['00-00-00-00-00-01', '00-00-00-00-00-02']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_type(self):
        params = {'type': [InterfaceTypeChoices.TYPE_1GE_FIXED, InterfaceTypeChoices.TYPE_1GE_GBIC]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)


class FrontPortTestCase(TestCase):
    queryset = FrontPort.objects.all()
    filterset = FrontPortFilterSet

    @classmethod
    def setUpTestData(cls):

        regions = (
            Region(name='Region 1', slug='region-1'),
            Region(name='Region 2', slug='region-2'),
            Region(name='Region 3', slug='region-3'),
        )
        for region in regions:
            region.save()
        sites = Site.objects.bulk_create((
            Site(name='Site 1', slug='site-1', region=regions[0]),
            Site(name='Site 2', slug='site-2', region=regions[1]),
            Site(name='Site 3', slug='site-3', region=regions[2]),
            Site(name='Site X', slug='site-x'),
        ))
        manufacturer = Manufacturer.objects.create(name='Manufacturer 1', slug='manufacturer-1')
        device_type = DeviceType.objects.create(manufacturer=manufacturer, model='Model 1', slug='model-1')
        device_role = DeviceRole.objects.create(name='Device Role 1', slug='device-role-1')

        devices = (
            Device(name='Device 1', device_type=device_type, device_role=device_role, site=sites[0]),
            Device(name='Device 2', device_type=device_type, device_role=device_role, site=sites[1]),
            Device(name='Device 3', device_type=device_type, device_role=device_role, site=sites[2]),
            Device(name=None, device_type=device_type, device_role=device_role, site=sites[3]),  # For cable connections
        )
        Device.objects.bulk_create(devices)

        rear_ports = (
            RearPort(device=devices[0], name='Rear Port 1', type=PortTypeChoices.TYPE_8P8C, positions=6),
            RearPort(device=devices[1], name='Rear Port 2', type=PortTypeChoices.TYPE_8P8C, positions=6),
            RearPort(device=devices[2], name='Rear Port 3', type=PortTypeChoices.TYPE_8P8C, positions=6),
            RearPort(device=devices[3], name='Rear Port 4', type=PortTypeChoices.TYPE_8P8C, positions=6),
            RearPort(device=devices[3], name='Rear Port 5', type=PortTypeChoices.TYPE_8P8C, positions=6),
            RearPort(device=devices[3], name='Rear Port 6', type=PortTypeChoices.TYPE_8P8C, positions=6),
        )
        RearPort.objects.bulk_create(rear_ports)

        front_ports = (
            FrontPort(device=devices[0], name='Front Port 1', type=PortTypeChoices.TYPE_8P8C, rear_port=rear_ports[0], rear_port_position=1, description='First'),
            FrontPort(device=devices[1], name='Front Port 2', type=PortTypeChoices.TYPE_110_PUNCH, rear_port=rear_ports[1], rear_port_position=2, description='Second'),
            FrontPort(device=devices[2], name='Front Port 3', type=PortTypeChoices.TYPE_BNC, rear_port=rear_ports[2], rear_port_position=3, description='Third'),
            FrontPort(device=devices[3], name='Front Port 4', type=PortTypeChoices.TYPE_FC, rear_port=rear_ports[3], rear_port_position=1),
            FrontPort(device=devices[3], name='Front Port 5', type=PortTypeChoices.TYPE_FC, rear_port=rear_ports[4], rear_port_position=1),
            FrontPort(device=devices[3], name='Front Port 6', type=PortTypeChoices.TYPE_FC, rear_port=rear_ports[5], rear_port_position=1),
        )
        FrontPort.objects.bulk_create(front_ports)

        # Cables
        Cable(termination_a=front_ports[0], termination_b=front_ports[3]).save()
        Cable(termination_a=front_ports[1], termination_b=front_ports[4]).save()
        # Third port is not connected

    def test_id(self):
        id_list = self.queryset.values_list('id', flat=True)[:2]
        params = {'id': [str(id) for id in id_list]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name(self):
        params = {'name': ['Front Port 1', 'Front Port 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_type(self):
        # TODO: Test for multiple values
        params = {'type': PortTypeChoices.TYPE_8P8C}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_description(self):
        params = {'description': ['First', 'Second']}
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

    def test_device(self):
        devices = Device.objects.all()[:2]
        params = {'device_id': [devices[0].pk, devices[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'device': [devices[0].name, devices[1].name]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_cabled(self):
        params = {'cabled': 'true'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)
        params = {'cabled': 'false'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)


class RearPortTestCase(TestCase):
    queryset = RearPort.objects.all()
    filterset = RearPortFilterSet

    @classmethod
    def setUpTestData(cls):

        regions = (
            Region(name='Region 1', slug='region-1'),
            Region(name='Region 2', slug='region-2'),
            Region(name='Region 3', slug='region-3'),
        )
        for region in regions:
            region.save()
        sites = Site.objects.bulk_create((
            Site(name='Site 1', slug='site-1', region=regions[0]),
            Site(name='Site 2', slug='site-2', region=regions[1]),
            Site(name='Site 3', slug='site-3', region=regions[2]),
            Site(name='Site X', slug='site-x'),
        ))
        manufacturer = Manufacturer.objects.create(name='Manufacturer 1', slug='manufacturer-1')
        device_type = DeviceType.objects.create(manufacturer=manufacturer, model='Model 1', slug='model-1')
        device_role = DeviceRole.objects.create(name='Device Role 1', slug='device-role-1')

        devices = (
            Device(name='Device 1', device_type=device_type, device_role=device_role, site=sites[0]),
            Device(name='Device 2', device_type=device_type, device_role=device_role, site=sites[1]),
            Device(name='Device 3', device_type=device_type, device_role=device_role, site=sites[2]),
            Device(name=None, device_type=device_type, device_role=device_role, site=sites[3]),  # For cable connections
        )
        Device.objects.bulk_create(devices)

        rear_ports = (
            RearPort(device=devices[0], name='Rear Port 1', type=PortTypeChoices.TYPE_8P8C, positions=1, description='First'),
            RearPort(device=devices[1], name='Rear Port 2', type=PortTypeChoices.TYPE_110_PUNCH, positions=2, description='Second'),
            RearPort(device=devices[2], name='Rear Port 3', type=PortTypeChoices.TYPE_BNC, positions=3, description='Third'),
            RearPort(device=devices[3], name='Rear Port 4', type=PortTypeChoices.TYPE_FC, positions=4),
            RearPort(device=devices[3], name='Rear Port 5', type=PortTypeChoices.TYPE_FC, positions=5),
            RearPort(device=devices[3], name='Rear Port 6', type=PortTypeChoices.TYPE_FC, positions=6),
        )
        RearPort.objects.bulk_create(rear_ports)

        # Cables
        Cable(termination_a=rear_ports[0], termination_b=rear_ports[3]).save()
        Cable(termination_a=rear_ports[1], termination_b=rear_ports[4]).save()
        # Third port is not connected

    def test_id(self):
        id_list = self.queryset.values_list('id', flat=True)[:2]
        params = {'id': [str(id) for id in id_list]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name(self):
        params = {'name': ['Rear Port 1', 'Rear Port 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_type(self):
        # TODO: Test for multiple values
        params = {'type': PortTypeChoices.TYPE_8P8C}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_positions(self):
        params = {'positions': [1, 2]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_description(self):
        params = {'description': ['First', 'Second']}
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

    def test_device(self):
        devices = Device.objects.all()[:2]
        params = {'device_id': [devices[0].pk, devices[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'device': [devices[0].name, devices[1].name]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_cabled(self):
        params = {'cabled': 'true'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)
        params = {'cabled': 'false'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)


class DeviceBayTestCase(TestCase):
    queryset = DeviceBay.objects.all()
    filterset = DeviceBayFilterSet

    @classmethod
    def setUpTestData(cls):

        regions = (
            Region(name='Region 1', slug='region-1'),
            Region(name='Region 2', slug='region-2'),
            Region(name='Region 3', slug='region-3'),
        )
        for region in regions:
            region.save()
        sites = Site.objects.bulk_create((
            Site(name='Site 1', slug='site-1', region=regions[0]),
            Site(name='Site 2', slug='site-2', region=regions[1]),
            Site(name='Site 3', slug='site-3', region=regions[2]),
            Site(name='Site X', slug='site-x'),
        ))
        manufacturer = Manufacturer.objects.create(name='Manufacturer 1', slug='manufacturer-1')
        device_type = DeviceType.objects.create(manufacturer=manufacturer, model='Model 1', slug='model-1')
        device_role = DeviceRole.objects.create(name='Device Role 1', slug='device-role-1')

        devices = (
            Device(name='Device 1', device_type=device_type, device_role=device_role, site=sites[0]),
            Device(name='Device 2', device_type=device_type, device_role=device_role, site=sites[1]),
            Device(name='Device 3', device_type=device_type, device_role=device_role, site=sites[2]),
        )
        Device.objects.bulk_create(devices)

        device_bays = (
            DeviceBay(device=devices[0], name='Device Bay 1', description='First'),
            DeviceBay(device=devices[1], name='Device Bay 2', description='Second'),
            DeviceBay(device=devices[2], name='Device Bay 3', description='Third'),
        )
        DeviceBay.objects.bulk_create(device_bays)

    def test_id(self):
        id_list = self.queryset.values_list('id', flat=True)[:2]
        params = {'id': [str(id) for id in id_list]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name(self):
        params = {'name': ['Device Bay 1', 'Device Bay 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_description(self):
        params = {'description': ['First', 'Second']}
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

    def test_device(self):
        devices = Device.objects.all()[:2]
        params = {'device_id': [devices[0].pk, devices[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'device': [devices[0].name, devices[1].name]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)


class InventoryItemTestCase(TestCase):
    queryset = InventoryItem.objects.all()
    filterset = InventoryItemFilterSet

    @classmethod
    def setUpTestData(cls):

        manufacturers = (
            Manufacturer(name='Manufacturer 1', slug='manufacturer-1'),
            Manufacturer(name='Manufacturer 2', slug='manufacturer-2'),
            Manufacturer(name='Manufacturer 3', slug='manufacturer-3'),
        )
        Manufacturer.objects.bulk_create(manufacturers)

        device_type = DeviceType.objects.create(manufacturer=manufacturers[0], model='Model 1', slug='model-1')
        device_role = DeviceRole.objects.create(name='Device Role 1', slug='device-role-1')

        regions = (
            Region(name='Region 1', slug='region-1'),
            Region(name='Region 2', slug='region-2'),
            Region(name='Region 3', slug='region-3'),
        )
        for region in regions:
            region.save()

        sites = (
            Site(name='Site 1', slug='site-1', region=regions[0]),
            Site(name='Site 2', slug='site-2', region=regions[1]),
            Site(name='Site 3', slug='site-3', region=regions[2]),
        )
        Site.objects.bulk_create(sites)

        devices = (
            Device(name='Device 1', device_type=device_type, device_role=device_role, site=sites[0]),
            Device(name='Device 2', device_type=device_type, device_role=device_role, site=sites[1]),
            Device(name='Device 3', device_type=device_type, device_role=device_role, site=sites[2]),
        )
        Device.objects.bulk_create(devices)

        inventory_items = (
            InventoryItem(device=devices[0], manufacturer=manufacturers[0], name='Inventory Item 1', part_id='1001', serial='ABC', asset_tag='1001', discovered=True, description='First'),
            InventoryItem(device=devices[1], manufacturer=manufacturers[1], name='Inventory Item 2', part_id='1002', serial='DEF', asset_tag='1002', discovered=True, description='Second'),
            InventoryItem(device=devices[2], manufacturer=manufacturers[2], name='Inventory Item 3', part_id='1003', serial='GHI', asset_tag='1003', discovered=False, description='Third'),
        )
        InventoryItem.objects.bulk_create(inventory_items)

        child_inventory_items = (
            InventoryItem(device=devices[0], name='Inventory Item 1A', parent=inventory_items[0]),
            InventoryItem(device=devices[1], name='Inventory Item 2A', parent=inventory_items[1]),
            InventoryItem(device=devices[2], name='Inventory Item 3A', parent=inventory_items[2]),
        )
        InventoryItem.objects.bulk_create(child_inventory_items)

    def test_id(self):
        id_list = self.queryset.values_list('id', flat=True)[:2]
        params = {'id': [str(id) for id in id_list]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name(self):
        params = {'name': ['Inventory Item 1', 'Inventory Item 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_part_id(self):
        params = {'part_id': ['1001', '1002']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_asset_tag(self):
        params = {'asset_tag': ['1001', '1002']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_discovered(self):
        # TODO: Fix boolean value
        params = {'discovered': True}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'discovered': False}
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

    def test_device(self):
        # TODO: Allow multiple values
        device = Device.objects.first()
        params = {'device_id': device.pk}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'device': device.name}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_parent_id(self):
        parent_items = InventoryItem.objects.filter(parent__isnull=True)[:2]
        params = {'parent_id': [parent_items[0].pk, parent_items[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_manufacturer(self):
        manufacturers = Manufacturer.objects.all()[:2]
        params = {'manufacturer_id': [manufacturers[0].pk, manufacturers[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'manufacturer': [manufacturers[0].slug, manufacturers[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_serial(self):
        params = {'serial': 'ABC'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {'serial': 'abc'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)


class VirtualChassisTestCase(TestCase):
    queryset = VirtualChassis.objects.all()
    filterset = VirtualChassisFilterSet

    @classmethod
    def setUpTestData(cls):

        manufacturer = Manufacturer.objects.create(name='Manufacturer 1', slug='manufacturer-1')
        device_type = DeviceType.objects.create(manufacturer=manufacturer, model='Model 1', slug='model-1')
        device_role = DeviceRole.objects.create(name='Device Role 1', slug='device-role-1')

        regions = (
            Region(name='Region 1', slug='region-1'),
            Region(name='Region 2', slug='region-2'),
            Region(name='Region 3', slug='region-3'),
        )
        for region in regions:
            region.save()

        sites = (
            Site(name='Site 1', slug='site-1', region=regions[0]),
            Site(name='Site 2', slug='site-2', region=regions[1]),
            Site(name='Site 3', slug='site-3', region=regions[2]),
        )
        Site.objects.bulk_create(sites)

        devices = (
            Device(name='Device 1', device_type=device_type, device_role=device_role, site=sites[0], vc_position=1),
            Device(name='Device 2', device_type=device_type, device_role=device_role, site=sites[0], vc_position=2),
            Device(name='Device 3', device_type=device_type, device_role=device_role, site=sites[1], vc_position=1),
            Device(name='Device 4', device_type=device_type, device_role=device_role, site=sites[1], vc_position=2),
            Device(name='Device 5', device_type=device_type, device_role=device_role, site=sites[2], vc_position=1),
            Device(name='Device 6', device_type=device_type, device_role=device_role, site=sites[2], vc_position=2),
        )
        Device.objects.bulk_create(devices)

        virtual_chassis = (
            VirtualChassis(master=devices[0], domain='Domain 1'),
            VirtualChassis(master=devices[2], domain='Domain 2'),
            VirtualChassis(master=devices[4], domain='Domain 3'),
        )
        VirtualChassis.objects.bulk_create(virtual_chassis)

        Device.objects.filter(pk=devices[1].pk).update(virtual_chassis=virtual_chassis[0])
        Device.objects.filter(pk=devices[3].pk).update(virtual_chassis=virtual_chassis[1])
        Device.objects.filter(pk=devices[5].pk).update(virtual_chassis=virtual_chassis[2])

    def test_id(self):
        id_list = self.queryset.values_list('id', flat=True)[:2]
        params = {'id': [str(id) for id in id_list]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_domain(self):
        params = {'domain': ['Domain 1', 'Domain 2']}
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


class CableTestCase(TestCase):
    queryset = Cable.objects.all()
    filterset = CableFilterSet

    @classmethod
    def setUpTestData(cls):

        sites = (
            Site(name='Site 1', slug='site-1'),
            Site(name='Site 2', slug='site-2'),
            Site(name='Site 3', slug='site-3'),
        )
        Site.objects.bulk_create(sites)

        tenants = (
            Tenant(name='Tenant 1', slug='tenant-1'),
            Tenant(name='Tenant 2', slug='tenant-2'),
        )
        Tenant.objects.bulk_create(tenants)

        racks = (
            Rack(name='Rack 1', site=sites[0]),
            Rack(name='Rack 2', site=sites[1]),
            Rack(name='Rack 3', site=sites[2]),
        )
        Rack.objects.bulk_create(racks)

        manufacturer = Manufacturer.objects.create(name='Manufacturer 1', slug='manufacturer-1')
        device_type = DeviceType.objects.create(manufacturer=manufacturer, model='Model 1', slug='model-1')
        device_role = DeviceRole.objects.create(name='Device Role 1', slug='device-role-1')

        devices = (
            Device(name='Device 1', device_type=device_type, device_role=device_role, site=sites[0], rack=racks[0], position=1, tenant=tenants[0]),
            Device(name='Device 2', device_type=device_type, device_role=device_role, site=sites[0], rack=racks[0], position=2, tenant=tenants[0]),
            Device(name='Device 3', device_type=device_type, device_role=device_role, site=sites[1], rack=racks[1], position=1, tenant=tenants[1]),
            Device(name='Device 4', device_type=device_type, device_role=device_role, site=sites[1], rack=racks[1], position=2),
            Device(name='Device 5', device_type=device_type, device_role=device_role, site=sites[2], rack=racks[2], position=1),
            Device(name='Device 6', device_type=device_type, device_role=device_role, site=sites[2], rack=racks[2], position=2),
        )
        Device.objects.bulk_create(devices)

        interfaces = (
            Interface(device=devices[0], name='Interface 1', type=InterfaceTypeChoices.TYPE_1GE_FIXED),
            Interface(device=devices[0], name='Interface 2', type=InterfaceTypeChoices.TYPE_1GE_FIXED),
            Interface(device=devices[1], name='Interface 3', type=InterfaceTypeChoices.TYPE_1GE_FIXED),
            Interface(device=devices[1], name='Interface 4', type=InterfaceTypeChoices.TYPE_1GE_FIXED),
            Interface(device=devices[2], name='Interface 5', type=InterfaceTypeChoices.TYPE_1GE_FIXED),
            Interface(device=devices[2], name='Interface 6', type=InterfaceTypeChoices.TYPE_1GE_FIXED),
            Interface(device=devices[3], name='Interface 7', type=InterfaceTypeChoices.TYPE_1GE_FIXED),
            Interface(device=devices[3], name='Interface 8', type=InterfaceTypeChoices.TYPE_1GE_FIXED),
            Interface(device=devices[4], name='Interface 9', type=InterfaceTypeChoices.TYPE_1GE_FIXED),
            Interface(device=devices[4], name='Interface 10', type=InterfaceTypeChoices.TYPE_1GE_FIXED),
            Interface(device=devices[5], name='Interface 11', type=InterfaceTypeChoices.TYPE_1GE_FIXED),
            Interface(device=devices[5], name='Interface 12', type=InterfaceTypeChoices.TYPE_1GE_FIXED),
        )
        Interface.objects.bulk_create(interfaces)

        # Cables
        Cable(termination_a=interfaces[1], termination_b=interfaces[2], label='Cable 1', type=CableTypeChoices.TYPE_CAT3, status=CableStatusChoices.STATUS_CONNECTED, color='aa1409', length=10, length_unit=CableLengthUnitChoices.UNIT_FOOT).save()
        Cable(termination_a=interfaces[3], termination_b=interfaces[4], label='Cable 2', type=CableTypeChoices.TYPE_CAT3, status=CableStatusChoices.STATUS_CONNECTED, color='aa1409', length=20, length_unit=CableLengthUnitChoices.UNIT_FOOT).save()
        Cable(termination_a=interfaces[5], termination_b=interfaces[6], label='Cable 3', type=CableTypeChoices.TYPE_CAT5E, status=CableStatusChoices.STATUS_CONNECTED, color='f44336', length=30, length_unit=CableLengthUnitChoices.UNIT_FOOT).save()
        Cable(termination_a=interfaces[7], termination_b=interfaces[8], label='Cable 4', type=CableTypeChoices.TYPE_CAT5E, status=CableStatusChoices.STATUS_PLANNED, color='f44336', length=40, length_unit=CableLengthUnitChoices.UNIT_FOOT).save()
        Cable(termination_a=interfaces[9], termination_b=interfaces[10], label='Cable 5', type=CableTypeChoices.TYPE_CAT6, status=CableStatusChoices.STATUS_PLANNED, color='e91e63', length=10, length_unit=CableLengthUnitChoices.UNIT_METER).save()
        Cable(termination_a=interfaces[11], termination_b=interfaces[0], label='Cable 6', type=CableTypeChoices.TYPE_CAT6, status=CableStatusChoices.STATUS_PLANNED, color='e91e63', length=20, length_unit=CableLengthUnitChoices.UNIT_METER).save()

    def test_id(self):
        id_list = self.queryset.values_list('id', flat=True)[:2]
        params = {'id': [str(id) for id in id_list]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_label(self):
        params = {'label': ['Cable 1', 'Cable 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_length(self):
        params = {'length': [10, 20]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)

    def test_length_unit(self):
        params = {'length_unit': CableLengthUnitChoices.UNIT_FOOT}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)

    def test_type(self):
        params = {'type': [CableTypeChoices.TYPE_CAT3, CableTypeChoices.TYPE_CAT5E]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)

    def test_status(self):
        params = {'status': [CableStatusChoices.STATUS_CONNECTED]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)
        params = {'status': [CableStatusChoices.STATUS_PLANNED]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_color(self):
        params = {'color': ['aa1409', 'f44336']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)

    def test_device(self):
        devices = Device.objects.all()[:2]
        params = {'device_id': [devices[0].pk, devices[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)
        params = {'device': [devices[0].name, devices[1].name]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 3)

    def test_rack(self):
        racks = Rack.objects.all()[:2]
        params = {'rack_id': [racks[0].pk, racks[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 5)
        params = {'rack': [racks[0].name, racks[1].name]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 5)

    def test_site(self):
        site = Site.objects.all()[:2]
        params = {'site_id': [site[0].pk, site[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 5)
        params = {'site': [site[0].slug, site[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 5)

    def test_tenant(self):
        tenant = Tenant.objects.all()[:2]
        params = {'tenant_id': [tenant[0].pk, tenant[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)
        params = {'tenant': [tenant[0].slug, tenant[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)


class PowerPanelTestCase(TestCase):
    queryset = PowerPanel.objects.all()
    filterset = PowerPanelFilterSet

    @classmethod
    def setUpTestData(cls):

        regions = (
            Region(name='Region 1', slug='region-1'),
            Region(name='Region 2', slug='region-2'),
            Region(name='Region 3', slug='region-3'),
        )
        for region in regions:
            region.save()

        sites = (
            Site(name='Site 1', slug='site-1', region=regions[0]),
            Site(name='Site 2', slug='site-2', region=regions[1]),
            Site(name='Site 3', slug='site-3', region=regions[2]),
        )
        Site.objects.bulk_create(sites)

        rack_groups = (
            RackGroup(name='Rack Group 1', slug='rack-group-1', site=sites[0]),
            RackGroup(name='Rack Group 2', slug='rack-group-2', site=sites[1]),
            RackGroup(name='Rack Group 3', slug='rack-group-3', site=sites[2]),
        )
        RackGroup.objects.bulk_create(rack_groups)

        power_panels = (
            PowerPanel(name='Power Panel 1', site=sites[0], rack_group=rack_groups[0]),
            PowerPanel(name='Power Panel 2', site=sites[1], rack_group=rack_groups[1]),
            PowerPanel(name='Power Panel 3', site=sites[2], rack_group=rack_groups[2]),
        )
        PowerPanel.objects.bulk_create(power_panels)

    def test_name(self):
        params = {'name': ['Power Panel 1', 'Power Panel 2']}
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

    def test_rack_group(self):
        rack_groups = RackGroup.objects.all()[:2]
        params = {'rack_group_id': [rack_groups[0].pk, rack_groups[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)


class PowerFeedTestCase(TestCase):
    queryset = PowerFeed.objects.all()
    filterset = PowerFeedFilterSet

    @classmethod
    def setUpTestData(cls):

        regions = (
            Region(name='Region 1', slug='region-1'),
            Region(name='Region 2', slug='region-2'),
            Region(name='Region 3', slug='region-3'),
        )
        for region in regions:
            region.save()

        sites = (
            Site(name='Site 1', slug='site-1', region=regions[0]),
            Site(name='Site 2', slug='site-2', region=regions[1]),
            Site(name='Site 3', slug='site-3', region=regions[2]),
        )
        Site.objects.bulk_create(sites)

        racks = (
            Rack(name='Rack 1', site=sites[0]),
            Rack(name='Rack 2', site=sites[1]),
            Rack(name='Rack 3', site=sites[2]),
        )
        Rack.objects.bulk_create(racks)

        power_panels = (
            PowerPanel(name='Power Panel 1', site=sites[0]),
            PowerPanel(name='Power Panel 2', site=sites[1]),
            PowerPanel(name='Power Panel 3', site=sites[2]),
        )
        PowerPanel.objects.bulk_create(power_panels)

        power_feeds = (
            PowerFeed(power_panel=power_panels[0], rack=racks[0], name='Power Feed 1', status=PowerFeedStatusChoices.STATUS_ACTIVE, type=PowerFeedTypeChoices.TYPE_PRIMARY, supply=PowerFeedSupplyChoices.SUPPLY_AC, phase=PowerFeedPhaseChoices.PHASE_3PHASE, voltage=100, amperage=100, max_utilization=10),
            PowerFeed(power_panel=power_panels[1], rack=racks[1], name='Power Feed 2', status=PowerFeedStatusChoices.STATUS_FAILED, type=PowerFeedTypeChoices.TYPE_PRIMARY, supply=PowerFeedSupplyChoices.SUPPLY_AC, phase=PowerFeedPhaseChoices.PHASE_3PHASE, voltage=200, amperage=200, max_utilization=20),
            PowerFeed(power_panel=power_panels[2], rack=racks[2], name='Power Feed 3', status=PowerFeedStatusChoices.STATUS_OFFLINE, type=PowerFeedTypeChoices.TYPE_REDUNDANT, supply=PowerFeedSupplyChoices.SUPPLY_DC, phase=PowerFeedPhaseChoices.PHASE_SINGLE, voltage=300, amperage=300, max_utilization=30),
        )
        PowerFeed.objects.bulk_create(power_feeds)

    def test_name(self):
        params = {'name': ['Power Feed 1', 'Power Feed 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_status(self):
        # TODO: Test for multiple values
        params = {'status': PowerFeedStatusChoices.STATUS_ACTIVE}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_type(self):
        params = {'type': PowerFeedTypeChoices.TYPE_PRIMARY}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_supply(self):
        params = {'supply': PowerFeedSupplyChoices.SUPPLY_AC}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_phase(self):
        params = {'phase': PowerFeedPhaseChoices.PHASE_3PHASE}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_voltage(self):
        params = {'voltage': [100, 200]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_amperage(self):
        params = {'amperage': [100, 200]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_max_utilization(self):
        params = {'max_utilization': [10, 20]}
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

    def test_power_panel_id(self):
        power_panels = PowerPanel.objects.all()[:2]
        params = {'power_panel_id': [power_panels[0].pk, power_panels[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_rack_id(self):
        racks = Rack.objects.all()[:2]
        params = {'rack_id': [racks[0].pk, racks[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)


# TODO: Connection filters
