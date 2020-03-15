from utilities.choices import ChoiceSet


#
# CustomFields
#

class CustomFieldTypeChoices(ChoiceSet):

    TYPE_TEXT = 'text'
    TYPE_INTEGER = 'integer'
    TYPE_BOOLEAN = 'boolean'
    TYPE_DATE = 'date'
    TYPE_URL = 'url'
    TYPE_SELECT = 'select'

    CHOICES = (
        (TYPE_TEXT, 'Text'),
        (TYPE_INTEGER, 'Integer'),
        (TYPE_BOOLEAN, 'Boolean (true/false)'),
        (TYPE_DATE, 'Date'),
        (TYPE_URL, 'URL'),
        (TYPE_SELECT, 'Selection'),
    )

    LEGACY_MAP = {
        TYPE_TEXT: 100,
        TYPE_INTEGER: 200,
        TYPE_BOOLEAN: 300,
        TYPE_DATE: 400,
        TYPE_URL: 500,
        TYPE_SELECT: 600,
    }


class CustomFieldFilterLogicChoices(ChoiceSet):

    FILTER_DISABLED = 'disabled'
    FILTER_LOOSE = 'loose'
    FILTER_EXACT = 'exact'

    CHOICES = (
        (FILTER_DISABLED, 'Disabled'),
        (FILTER_LOOSE, 'Loose'),
        (FILTER_EXACT, 'Exact'),
    )

    LEGACY_MAP = {
        FILTER_DISABLED: 0,
        FILTER_LOOSE: 1,
        FILTER_EXACT: 2,
    }


#
# CustomLinks
#

class CustomLinkButtonClassChoices(ChoiceSet):

    CLASS_DEFAULT = 'default'
    CLASS_PRIMARY = 'primary'
    CLASS_SUCCESS = 'success'
    CLASS_INFO = 'info'
    CLASS_WARNING = 'warning'
    CLASS_DANGER = 'danger'
    CLASS_LINK = 'link'

    CHOICES = (
        (CLASS_DEFAULT, 'Default'),
        (CLASS_PRIMARY, 'Primary (blue)'),
        (CLASS_SUCCESS, 'Success (green)'),
        (CLASS_INFO, 'Info (aqua)'),
        (CLASS_WARNING, 'Warning (orange)'),
        (CLASS_DANGER, 'Danger (red)'),
        (CLASS_LINK, 'None (link)'),
    )


#
# ObjectChanges
#

class ObjectChangeActionChoices(ChoiceSet):

    ACTION_CREATE = 'create'
    ACTION_UPDATE = 'update'
    ACTION_DELETE = 'delete'

    CHOICES = (
        (ACTION_CREATE, 'Created'),
        (ACTION_UPDATE, 'Updated'),
        (ACTION_DELETE, 'Deleted'),
    )

    LEGACY_MAP = {
        ACTION_CREATE: 1,
        ACTION_UPDATE: 2,
        ACTION_DELETE: 3,
    }


#
# ExportTemplates
#

class TemplateLanguageChoices(ChoiceSet):

    LANGUAGE_DJANGO = 'django'
    LANGUAGE_JINJA2 = 'jinja2'

    CHOICES = (
        (LANGUAGE_DJANGO, 'Django'),
        (LANGUAGE_JINJA2, 'Jinja2'),
    )

    LEGACY_MAP = {
        LANGUAGE_DJANGO: 10,
        LANGUAGE_JINJA2: 20,
    }


#
# Webhooks
#

class WebhookHttpMethodChoices(ChoiceSet):

    METHOD_GET = 'GET'
    METHOD_POST = 'POST'
    METHOD_PUT = 'PUT'
    METHOD_PATCH = 'PATCH'
    METHOD_DELETE = 'DELETE'

    CHOICES = (
        (METHOD_GET, 'GET'),
        (METHOD_POST, 'POST'),
        (METHOD_PUT, 'PUT'),
        (METHOD_PATCH, 'PATCH'),
        (METHOD_DELETE, 'DELETE'),
    )
