from django.contrib.auth.models import Permission, User
from django.core.exceptions import ObjectDoesNotExist
from django.forms.models import model_to_dict
from django.test import Client, TestCase as _TestCase, override_settings
from django.urls import reverse, NoReverseMatch
from rest_framework.test import APIClient

from users.models import Token
from .utils import disable_warnings, post_data


class TestCase(_TestCase):
    user_permissions = ()

    def setUp(self):

        # Create the test user and assign permissions
        self.user = User.objects.create_user(username='testuser')
        self.add_permissions(*self.user_permissions)

        # Initialize the test client
        self.client = Client()
        self.client.force_login(self.user)

    #
    # Permissions management
    #

    def add_permissions(self, *names):
        """
        Assign a set of permissions to the test user. Accepts permission names in the form <app>.<action>_<model>.
        """
        for name in names:
            app, codename = name.split('.')
            perm = Permission.objects.get(content_type__app_label=app, codename=codename)
            self.user.user_permissions.add(perm)

    def remove_permissions(self, *names):
        """
        Remove a set of permissions from the test user, if assigned.
        """
        for name in names:
            app, codename = name.split('.')
            perm = Permission.objects.get(content_type__app_label=app, codename=codename)
            self.user.user_permissions.remove(perm)

    #
    # Convenience methods
    #

    def assertHttpStatus(self, response, expected_status):
        """
        TestCase method. Provide more detail in the event of an unexpected HTTP response.
        """
        err_message = "Expected HTTP status {}; received {}: {}"
        self.assertEqual(response.status_code, expected_status, err_message.format(
            expected_status, response.status_code, getattr(response, 'data', 'No data')
        ))


class ModelViewTestCase(TestCase):
    """
    Base TestCase for model views. Subclass to test individual views.
    """
    model = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.model is None:
            raise Exception("Test case requires model to be defined")

    def _get_base_url(self):
        """
        Return the base format for a URL for the test's model. Override this to test for a model which belongs
        to a different app (e.g. testing Interfaces within the virtualization app).
        """
        return '{}:{}_{{}}'.format(
            self.model._meta.app_label,
            self.model._meta.model_name
        )

    def _get_url(self, action, instance=None):
        """
        Return the URL name for a specific action. An instance must be specified for
        get/edit/delete views.
        """
        url_format = self._get_base_url()

        if action in ('list', 'add', 'import', 'bulk_edit', 'bulk_delete'):
            return reverse(url_format.format(action))

        elif action in ('get', 'edit', 'delete'):
            if instance is None:
                raise Exception("Resolving {} URL requires specifying an instance".format(action))
            # Attempt to resolve using slug first
            if hasattr(self.model, 'slug'):
                try:
                    return reverse(url_format.format(action), kwargs={'slug': instance.slug})
                except NoReverseMatch:
                    pass
            return reverse(url_format.format(action), kwargs={'pk': instance.pk})

        else:
            raise Exception("Invalid action for URL resolution: {}".format(action))

    def assertInstanceEqual(self, instance, data):
        """
        Compare a model instance to a dictionary, checking that its attribute values match those specified
        in the dictionary.
        """
        model_dict = model_to_dict(instance, fields=data.keys())

        for key in list(model_dict.keys()):

            # TODO: Differentiate between tags assigned to the instance and a M2M field for tags (ex: ConfigContext)
            if key == 'tags':
                model_dict[key] = ','.join(sorted([tag.name for tag in model_dict['tags']]))

            # Convert ManyToManyField to list of instance PKs
            elif model_dict[key] and type(model_dict[key]) in (list, tuple) and hasattr(model_dict[key][0], 'pk'):
                model_dict[key] = [obj.pk for obj in model_dict[key]]

        # Omit any dictionary keys which are not instance attributes
        relevant_data = {
            k: v for k, v in data.items() if hasattr(instance, k)
        }

        self.assertDictEqual(model_dict, relevant_data)


class APITestCase(TestCase):
    client_class = APIClient

    def setUp(self):
        """
        Create a superuser and token for API calls.
        """
        self.user = User.objects.create(username='testuser', is_superuser=True)
        self.token = Token.objects.create(user=self.user)
        self.header = {'HTTP_AUTHORIZATION': 'Token {}'.format(self.token.key)}


class ViewTestCases:
    """
    We keep any TestCases with test_* methods inside a class to prevent unittest from trying to run them.
    """
    class GetObjectViewTestCase(ModelViewTestCase):
        """
        Retrieve a single instance.
        """
        @override_settings(EXEMPT_VIEW_PERMISSIONS=[])
        def test_get_object(self):
            instance = self.model.objects.first()

            # Attempt to make the request without required permissions
            with disable_warnings('django.request'):
                self.assertHttpStatus(self.client.get(instance.get_absolute_url()), 403)

            # Assign the required permission and submit again
            self.add_permissions(
                '{}.view_{}'.format(self.model._meta.app_label, self.model._meta.model_name)
            )
            response = self.client.get(instance.get_absolute_url())
            self.assertHttpStatus(response, 200)

    class CreateObjectViewTestCase(ModelViewTestCase):
        """
        Create a single new instance.
        """
        form_data = {}

        @override_settings(EXEMPT_VIEW_PERMISSIONS=[])
        def test_create_object(self):

            # Try GET without permission
            with disable_warnings('django.request'):
                self.assertHttpStatus(self.client.post(self._get_url('add')), 403)

            # Try GET with permission
            self.add_permissions(
                '{}.add_{}'.format(self.model._meta.app_label, self.model._meta.model_name)
            )
            response = self.client.get(path=self._get_url('add'))
            self.assertHttpStatus(response, 200)

            # Try POST with permission
            initial_count = self.model.objects.count()
            request = {
                'path': self._get_url('add'),
                'data': post_data(self.form_data),
                'follow': False,  # Do not follow 302 redirects
            }
            response = self.client.post(**request)
            self.assertHttpStatus(response, 302)

            # Validate object creation
            self.assertEqual(initial_count + 1, self.model.objects.count())
            instance = self.model.objects.order_by('-pk').first()
            self.assertInstanceEqual(instance, self.form_data)

    class EditObjectViewTestCase(ModelViewTestCase):
        """
        Edit a single existing instance.
        """
        form_data = {}

        @override_settings(EXEMPT_VIEW_PERMISSIONS=[])
        def test_edit_object(self):
            instance = self.model.objects.first()

            # Try GET without permission
            with disable_warnings('django.request'):
                self.assertHttpStatus(self.client.post(self._get_url('edit', instance)), 403)

            # Try GET with permission
            self.add_permissions(
                '{}.change_{}'.format(self.model._meta.app_label, self.model._meta.model_name)
            )
            response = self.client.get(path=self._get_url('edit', instance))
            self.assertHttpStatus(response, 200)

            # Try POST with permission
            request = {
                'path': self._get_url('edit', instance),
                'data': post_data(self.form_data),
                'follow': False,  # Do not follow 302 redirects
            }
            response = self.client.post(**request)
            self.assertHttpStatus(response, 302)

            # Validate object modifications
            instance = self.model.objects.get(pk=instance.pk)
            self.assertInstanceEqual(instance, self.form_data)

    class DeleteObjectViewTestCase(ModelViewTestCase):
        """
        Delete a single instance.
        """
        @override_settings(EXEMPT_VIEW_PERMISSIONS=[])
        def test_delete_object(self):
            instance = self.model.objects.first()

            # Try GET without permissions
            with disable_warnings('django.request'):
                self.assertHttpStatus(self.client.post(self._get_url('delete', instance)), 403)

            # Try GET with permission
            self.add_permissions(
                '{}.delete_{}'.format(self.model._meta.app_label, self.model._meta.model_name)
            )
            response = self.client.get(path=self._get_url('delete', instance))
            self.assertHttpStatus(response, 200)

            request = {
                'path': self._get_url('delete', instance),
                'data': {'confirm': True},
                'follow': False,  # Do not follow 302 redirects
            }
            response = self.client.post(**request)
            self.assertHttpStatus(response, 302)

            # Validate object deletion
            with self.assertRaises(ObjectDoesNotExist):
                self.model.objects.get(pk=instance.pk)

    class ListObjectsViewTestCase(ModelViewTestCase):
        """
        Retrieve multiple instances.
        """
        @override_settings(EXEMPT_VIEW_PERMISSIONS=[])
        def test_list_objects(self):
            # Attempt to make the request without required permissions
            with disable_warnings('django.request'):
                self.assertHttpStatus(self.client.get(self._get_url('list')), 403)

            # Assign the required permission and submit again
            self.add_permissions(
                '{}.view_{}'.format(self.model._meta.app_label, self.model._meta.model_name)
            )
            response = self.client.get(self._get_url('list'))
            self.assertHttpStatus(response, 200)

            # Built-in CSV export
            if hasattr(self.model, 'csv_headers'):
                response = self.client.get('{}?export'.format(self._get_url('list')))
                self.assertHttpStatus(response, 200)
                self.assertEqual(response.get('Content-Type'), 'text/csv')

    class BulkCreateObjectsViewTestCase(ModelViewTestCase):
        """
        Create multiple instances using a single form. Expects the creation of three new instances by default.
        """
        bulk_create_count = 3
        bulk_create_data = {}

        @override_settings(EXEMPT_VIEW_PERMISSIONS=[])
        def test_bulk_create_objects(self):
            initial_count = self.model.objects.count()
            request = {
                'path': self._get_url('add'),
                'data': post_data(self.bulk_create_data),
                'follow': False,  # Do not follow 302 redirects
            }

            # Attempt to make the request without required permissions
            with disable_warnings('django.request'):
                self.assertHttpStatus(self.client.post(**request), 403)

            # Assign the required permission and submit again
            self.add_permissions(
                '{}.add_{}'.format(self.model._meta.app_label, self.model._meta.model_name)
            )
            response = self.client.post(**request)
            self.assertHttpStatus(response, 302)

            self.assertEqual(initial_count + self.bulk_create_count, self.model.objects.count())
            for instance in self.model.objects.order_by('-pk')[:self.bulk_create_count]:
                self.assertInstanceEqual(instance, self.bulk_create_data)

    class ImportObjectsViewTestCase(ModelViewTestCase):
        """
        Create multiple instances from imported data.
        """
        csv_data = ()

        @override_settings(EXEMPT_VIEW_PERMISSIONS=[])
        def test_import_objects(self):

            # Test GET without permission
            with disable_warnings('django.request'):
                self.assertHttpStatus(self.client.get(self._get_url('import')), 403)

            # Test GET with permission
            self.add_permissions(
                '{}.view_{}'.format(self.model._meta.app_label, self.model._meta.model_name),
                '{}.add_{}'.format(self.model._meta.app_label, self.model._meta.model_name)
            )
            response = self.client.get(self._get_url('import'))
            self.assertHttpStatus(response, 200)

            # Test POST with permission
            initial_count = self.model.objects.count()
            request = {
                'path': self._get_url('import'),
                'data': {
                    'csv': '\n'.join(self.csv_data)
                }
            }
            response = self.client.post(**request)
            self.assertHttpStatus(response, 200)

            # Validate import of new objects
            self.assertEqual(self.model.objects.count(), initial_count + len(self.csv_data) - 1)

    class BulkEditObjectsViewTestCase(ModelViewTestCase):
        """
        Edit multiple instances.
        """
        bulk_edit_data = {}

        @override_settings(EXEMPT_VIEW_PERMISSIONS=[])
        def test_bulk_edit_objects(self):
            # Bulk edit the first three objects only
            pk_list = self.model.objects.values_list('pk', flat=True)[:3]

            request = {
                'path': self._get_url('bulk_edit'),
                'data': {
                    'pk': pk_list,
                    '_apply': True,  # Form button
                },
                'follow': False,  # Do not follow 302 redirects
            }

            # Append the form data to the request
            request['data'].update(post_data(self.bulk_edit_data))

            # Attempt to make the request without required permissions
            with disable_warnings('django.request'):
                self.assertHttpStatus(self.client.post(**request), 403)

            # Assign the required permission and submit again
            self.add_permissions(
                '{}.change_{}'.format(self.model._meta.app_label, self.model._meta.model_name)
            )
            response = self.client.post(**request)
            self.assertHttpStatus(response, 302)

            for i, instance in enumerate(self.model.objects.filter(pk__in=pk_list)):
                self.assertInstanceEqual(instance, self.bulk_edit_data)

    class BulkDeleteObjectsViewTestCase(ModelViewTestCase):
        """
        Delete multiple instances.
        """
        @override_settings(EXEMPT_VIEW_PERMISSIONS=[])
        def test_bulk_delete_objects(self):
            pk_list = self.model.objects.values_list('pk', flat=True)

            request = {
                'path': self._get_url('bulk_delete'),
                'data': {
                    'pk': pk_list,
                    'confirm': True,
                    '_confirm': True,  # Form button
                },
                'follow': False,  # Do not follow 302 redirects
            }

            # Attempt to make the request without required permissions
            with disable_warnings('django.request'):
                self.assertHttpStatus(self.client.post(**request), 403)

            # Assign the required permission and submit again
            self.add_permissions(
                '{}.delete_{}'.format(self.model._meta.app_label, self.model._meta.model_name)
            )
            response = self.client.post(**request)
            self.assertHttpStatus(response, 302)

            # Check that all objects were deleted
            self.assertEqual(self.model.objects.count(), 0)

    class PrimaryObjectViewTestCase(
        GetObjectViewTestCase,
        CreateObjectViewTestCase,
        EditObjectViewTestCase,
        DeleteObjectViewTestCase,
        ListObjectsViewTestCase,
        ImportObjectsViewTestCase,
        BulkEditObjectsViewTestCase,
        BulkDeleteObjectsViewTestCase,
    ):
        """
        TestCase suitable for testing all standard View functions for primary objects
        """
        maxDiff = None

    class OrganizationalObjectViewTestCase(
        CreateObjectViewTestCase,
        EditObjectViewTestCase,
        ListObjectsViewTestCase,
        ImportObjectsViewTestCase,
        BulkDeleteObjectsViewTestCase,
    ):
        """
        TestCase suitable for all organizational objects
        """
        maxDiff = None

    class DeviceComponentTemplateViewTestCase(
        EditObjectViewTestCase,
        DeleteObjectViewTestCase,
        BulkCreateObjectsViewTestCase,
        BulkEditObjectsViewTestCase,
        BulkDeleteObjectsViewTestCase,
    ):
        """
        TestCase suitable for testing device component template models (ConsolePortTemplates, InterfaceTemplates, etc.)
        """
        maxDiff = None

    class DeviceComponentViewTestCase(
        EditObjectViewTestCase,
        DeleteObjectViewTestCase,
        ListObjectsViewTestCase,
        BulkCreateObjectsViewTestCase,
        ImportObjectsViewTestCase,
        BulkEditObjectsViewTestCase,
        BulkDeleteObjectsViewTestCase,
    ):
        """
        TestCase suitable for testing device component models (ConsolePorts, Interfaces, etc.)
        """
        maxDiff = None
