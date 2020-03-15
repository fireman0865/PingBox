from tenancy.models import Tenant, TenantGroup
from utilities.testing import ViewTestCases


class TenantGroupTestCase(ViewTestCases.OrganizationalObjectViewTestCase):
    model = TenantGroup

    @classmethod
    def setUpTestData(cls):

        TenantGroup.objects.bulk_create([
            TenantGroup(name='Tenant Group 1', slug='tenant-group-1'),
            TenantGroup(name='Tenant Group 2', slug='tenant-group-2'),
            TenantGroup(name='Tenant Group 3', slug='tenant-group-3'),
        ])

        cls.form_data = {
            'name': 'Tenant Group X',
            'slug': 'tenant-group-x',
        }

        cls.csv_data = (
            "name,slug",
            "Tenant Group 4,tenant-group-4",
            "Tenant Group 5,tenant-group-5",
            "Tenant Group 6,tenant-group-6",
        )


class TenantTestCase(ViewTestCases.PrimaryObjectViewTestCase):
    model = Tenant

    @classmethod
    def setUpTestData(cls):

        tenantgroups = (
            TenantGroup(name='Tenant Group 1', slug='tenant-group-1'),
            TenantGroup(name='Tenant Group 2', slug='tenant-group-2'),
        )
        TenantGroup.objects.bulk_create(tenantgroups)

        Tenant.objects.bulk_create([
            Tenant(name='Tenant 1', slug='tenant-1', group=tenantgroups[0]),
            Tenant(name='Tenant 2', slug='tenant-2', group=tenantgroups[0]),
            Tenant(name='Tenant 3', slug='tenant-3', group=tenantgroups[0]),
        ])

        cls.form_data = {
            'name': 'Tenant X',
            'slug': 'tenant-x',
            'group': tenantgroups[1].pk,
            'description': 'A new tenant',
            'comments': 'Some comments',
            'tags': 'Alpha,Bravo,Charlie',
        }

        cls.csv_data = (
            "name,slug",
            "Tenant 4,tenant-4",
            "Tenant 5,tenant-5",
            "Tenant 6,tenant-6",
        )

        cls.bulk_edit_data = {
            'group': tenantgroups[1].pk,
        }
