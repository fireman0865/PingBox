from django.test import TestCase

from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site
from secrets.filters import *
from secrets.models import Secret, SecretRole


class SecretRoleTestCase(TestCase):
    queryset = SecretRole.objects.all()
    filterset = SecretRoleFilterSet

    @classmethod
    def setUpTestData(cls):

        roles = (
            SecretRole(name='Secret Role 1', slug='secret-role-1'),
            SecretRole(name='Secret Role 2', slug='secret-role-2'),
            SecretRole(name='Secret Role 3', slug='secret-role-3'),
        )
        SecretRole.objects.bulk_create(roles)

    def test_id(self):
        id_list = self.queryset.values_list('id', flat=True)[:2]
        params = {'id': [str(id) for id in id_list]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_name(self):
        params = {'name': ['Secret Role 1', 'Secret Role 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_slug(self):
        params = {'slug': ['secret-role-1', 'secret-role-2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)


class SecretTestCase(TestCase):
    queryset = Secret.objects.all()
    filterset = SecretFilterSet

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

        roles = (
            SecretRole(name='Secret Role 1', slug='secret-role-1'),
            SecretRole(name='Secret Role 2', slug='secret-role-2'),
            SecretRole(name='Secret Role 3', slug='secret-role-3'),
        )
        SecretRole.objects.bulk_create(roles)

        secrets = (
            Secret(device=devices[0], role=roles[0], name='Secret 1', plaintext='SECRET DATA'),
            Secret(device=devices[1], role=roles[1], name='Secret 2', plaintext='SECRET DATA'),
            Secret(device=devices[2], role=roles[2], name='Secret 3', plaintext='SECRET DATA'),
        )
        # Must call save() to encrypt Secrets
        for s in secrets:
            s.save()

    def test_name(self):
        params = {'name': ['Secret 1', 'Secret 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_id__in(self):
        id_list = self.queryset.values_list('id', flat=True)[:2]
        params = {'id__in': ','.join([str(id) for id in id_list])}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_role(self):
        roles = SecretRole.objects.all()[:2]
        params = {'role_id': [roles[0].pk, roles[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'role': [roles[0].slug, roles[1].slug]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_device(self):
        devices = Device.objects.all()[:2]
        params = {'device_id': [devices[0].pk, devices[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'device': [devices[0].name, devices[1].name]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
