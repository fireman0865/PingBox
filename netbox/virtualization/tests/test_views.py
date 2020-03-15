from netaddr import EUI

from dcim.choices import InterfaceModeChoices
from dcim.models import DeviceRole, Interface, Platform, Site
from ipam.models import VLAN
from utilities.testing import ViewTestCases
from virtualization.choices import *
from virtualization.models import Cluster, ClusterGroup, ClusterType, VirtualMachine


class ClusterGroupTestCase(ViewTestCases.OrganizationalObjectViewTestCase):
    model = ClusterGroup

    @classmethod
    def setUpTestData(cls):

        ClusterGroup.objects.bulk_create([
            ClusterGroup(name='Cluster Group 1', slug='cluster-group-1'),
            ClusterGroup(name='Cluster Group 2', slug='cluster-group-2'),
            ClusterGroup(name='Cluster Group 3', slug='cluster-group-3'),
        ])

        cls.form_data = {
            'name': 'Cluster Group X',
            'slug': 'cluster-group-x',
        }

        cls.csv_data = (
            "name,slug",
            "Cluster Group 4,cluster-group-4",
            "Cluster Group 5,cluster-group-5",
            "Cluster Group 6,cluster-group-6",
        )


class ClusterTypeTestCase(ViewTestCases.OrganizationalObjectViewTestCase):
    model = ClusterType

    @classmethod
    def setUpTestData(cls):

        ClusterType.objects.bulk_create([
            ClusterType(name='Cluster Type 1', slug='cluster-type-1'),
            ClusterType(name='Cluster Type 2', slug='cluster-type-2'),
            ClusterType(name='Cluster Type 3', slug='cluster-type-3'),
        ])

        cls.form_data = {
            'name': 'Cluster Type X',
            'slug': 'cluster-type-x',
        }

        cls.csv_data = (
            "name,slug",
            "Cluster Type 4,cluster-type-4",
            "Cluster Type 5,cluster-type-5",
            "Cluster Type 6,cluster-type-6",
        )


class ClusterTestCase(ViewTestCases.PrimaryObjectViewTestCase):
    model = Cluster

    @classmethod
    def setUpTestData(cls):

        sites = (
            Site(name='Site 1', slug='site-1'),
            Site(name='Site 2', slug='site-2'),
        )
        Site.objects.bulk_create(sites)

        clustergroups = (
            ClusterGroup(name='Cluster Group 1', slug='cluster-group-1'),
            ClusterGroup(name='Cluster Group 2', slug='cluster-group-2'),
        )
        ClusterGroup.objects.bulk_create(clustergroups)

        clustertypes = (
            ClusterType(name='Cluster Type 1', slug='cluster-type-1'),
            ClusterType(name='Cluster Type 2', slug='cluster-type-2'),
        )
        ClusterType.objects.bulk_create(clustertypes)

        Cluster.objects.bulk_create([
            Cluster(name='Cluster 1', group=clustergroups[0], type=clustertypes[0], site=sites[0]),
            Cluster(name='Cluster 2', group=clustergroups[0], type=clustertypes[0], site=sites[0]),
            Cluster(name='Cluster 3', group=clustergroups[0], type=clustertypes[0], site=sites[0]),
        ])

        cls.form_data = {
            'name': 'Cluster X',
            'group': clustergroups[1].pk,
            'type': clustertypes[1].pk,
            'tenant': None,
            'site': sites[1].pk,
            'comments': 'Some comments',
            'tags': 'Alpha,Bravo,Charlie',
        }

        cls.csv_data = (
            "name,type",
            "Cluster 4,Cluster Type 1",
            "Cluster 5,Cluster Type 1",
            "Cluster 6,Cluster Type 1",
        )

        cls.bulk_edit_data = {
            'group': clustergroups[1].pk,
            'type': clustertypes[1].pk,
            'tenant': None,
            'site': sites[1].pk,
            'comments': 'New comments',
        }


class VirtualMachineTestCase(ViewTestCases.PrimaryObjectViewTestCase):
    model = VirtualMachine

    @classmethod
    def setUpTestData(cls):

        deviceroles = (
            DeviceRole(name='Device Role 1', slug='device-role-1'),
            DeviceRole(name='Device Role 2', slug='device-role-2'),
        )
        DeviceRole.objects.bulk_create(deviceroles)

        platforms = (
            Platform(name='Platform 1', slug='platform-1'),
            Platform(name='Platform 2', slug='platform-2'),
        )
        Platform.objects.bulk_create(platforms)

        clustertype = ClusterType.objects.create(name='Cluster Type 1', slug='cluster-type-1')

        clusters = (
            Cluster(name='Cluster 1', type=clustertype),
            Cluster(name='Cluster 2', type=clustertype),
        )
        Cluster.objects.bulk_create(clusters)

        VirtualMachine.objects.bulk_create([
            VirtualMachine(name='Virtual Machine 1', cluster=clusters[0], role=deviceroles[0], platform=platforms[0]),
            VirtualMachine(name='Virtual Machine 2', cluster=clusters[0], role=deviceroles[0], platform=platforms[0]),
            VirtualMachine(name='Virtual Machine 3', cluster=clusters[0], role=deviceroles[0], platform=platforms[0]),
        ])

        cls.form_data = {
            'cluster': clusters[1].pk,
            'tenant': None,
            'platform': platforms[1].pk,
            'name': 'Virtual Machine X',
            'status': VirtualMachineStatusChoices.STATUS_STAGED,
            'role': deviceroles[1].pk,
            'primary_ip4': None,
            'primary_ip6': None,
            'vcpus': 4,
            'memory': 32768,
            'disk': 4000,
            'comments': 'Some comments',
            'tags': 'Alpha,Bravo,Charlie',
            'local_context_data': None,
        }

        cls.csv_data = (
            "name,cluster",
            "Virtual Machine 4,Cluster 1",
            "Virtual Machine 5,Cluster 1",
            "Virtual Machine 6,Cluster 1",
        )

        cls.bulk_edit_data = {
            'cluster': clusters[1].pk,
            'tenant': None,
            'platform': platforms[1].pk,
            'status': VirtualMachineStatusChoices.STATUS_STAGED,
            'role': deviceroles[1].pk,
            'vcpus': 8,
            'memory': 65535,
            'disk': 8000,
            'comments': 'New comments',
        }


class InterfaceTestCase(
    ViewTestCases.GetObjectViewTestCase,
    ViewTestCases.DeviceComponentViewTestCase,
):
    model = Interface

    # Disable inapplicable tests
    test_list_objects = None
    test_import_objects = None

    def _get_base_url(self):
        # Interface belongs to the DCIM app, so we have to override the base URL
        return 'virtualization:interface_{}'

    @classmethod
    def setUpTestData(cls):

        site = Site.objects.create(name='Site 1', slug='site-1')
        devicerole = DeviceRole.objects.create(name='Device Role 1', slug='device-role-1')
        clustertype = ClusterType.objects.create(name='Cluster Type 1', slug='cluster-type-1')
        cluster = Cluster.objects.create(name='Cluster 1', type=clustertype, site=site)
        virtualmachines = (
            VirtualMachine(name='Virtual Machine 1', cluster=cluster, role=devicerole),
            VirtualMachine(name='Virtual Machine 2', cluster=cluster, role=devicerole),
        )
        VirtualMachine.objects.bulk_create(virtualmachines)

        Interface.objects.bulk_create([
            Interface(virtual_machine=virtualmachines[0], name='Interface 1', type=InterfaceTypeChoices.TYPE_VIRTUAL),
            Interface(virtual_machine=virtualmachines[0], name='Interface 2', type=InterfaceTypeChoices.TYPE_VIRTUAL),
            Interface(virtual_machine=virtualmachines[0], name='Interface 3', type=InterfaceTypeChoices.TYPE_VIRTUAL),
        ])

        vlans = (
            VLAN(vid=1, name='VLAN1', site=site),
            VLAN(vid=101, name='VLAN101', site=site),
            VLAN(vid=102, name='VLAN102', site=site),
            VLAN(vid=103, name='VLAN103', site=site),
        )
        VLAN.objects.bulk_create(vlans)

        cls.form_data = {
            'virtual_machine': virtualmachines[1].pk,
            'name': 'Interface X',
            'type': InterfaceTypeChoices.TYPE_VIRTUAL,
            'enabled': False,
            'mgmt_only': False,
            'mac_address': EUI('01-02-03-04-05-06'),
            'mtu': 2000,
            'description': 'New description',
            'mode': InterfaceModeChoices.MODE_TAGGED,
            'untagged_vlan': vlans[0].pk,
            'tagged_vlans': [v.pk for v in vlans[1:4]],
            'tags': 'Alpha,Bravo,Charlie',
        }

        cls.bulk_create_data = {
            'virtual_machine': virtualmachines[1].pk,
            'name_pattern': 'Interface [4-6]',
            'type': InterfaceTypeChoices.TYPE_VIRTUAL,
            'enabled': False,
            'mgmt_only': False,
            'mac_address': EUI('01-02-03-04-05-06'),
            'mtu': 2000,
            'description': 'New description',
            'mode': InterfaceModeChoices.MODE_TAGGED,
            'untagged_vlan': vlans[0].pk,
            'tagged_vlans': [v.pk for v in vlans[1:4]],
            'tags': 'Alpha,Bravo,Charlie',
        }

        cls.bulk_edit_data = {
            'virtual_machine': virtualmachines[1].pk,
            'enabled': False,
            'mtu': 2000,
            'description': 'New description',
            'mode': InterfaceModeChoices.MODE_TAGGED,
            # 'untagged_vlan': vlans[0].pk,
            # 'tagged_vlans': [v.pk for v in vlans[1:4]],
        }

        cls.csv_data = (
            "device,name,type",
            "Device 1,Interface 4,1000BASE-T (1GE)",
            "Device 1,Interface 5,1000BASE-T (1GE)",
            "Device 1,Interface 6,1000BASE-T (1GE)",
        )
