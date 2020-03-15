from django import template
from django.urls import reverse

from extras.models import ExportTemplate
from utilities.utils import prepare_cloned_fields

register = template.Library()


def _get_viewname(instance, action):
    """
    Return the appropriate viewname for adding, editing, or deleting an instance.
    """

    # Validate action
    assert action in ('add', 'edit', 'delete')
    viewname = "{}:{}_{}".format(
        instance._meta.app_label, instance._meta.model_name, action
    )

    return viewname


#
# Instance buttons
#

@register.inclusion_tag('buttons/clone.html')
def clone_button(instance):
    viewname = _get_viewname(instance, 'add')

    # Populate cloned field values
    param_string = prepare_cloned_fields(instance)
    if param_string:
        url = '{}?{}'.format(reverse(viewname), param_string)

    return {
        'url': url,
    }


@register.inclusion_tag('buttons/edit.html')
def edit_button(instance, use_pk=False):
    viewname = _get_viewname(instance, 'edit')

    # Assign kwargs
    if hasattr(instance, 'slug') and not use_pk:
        kwargs = {'slug': instance.slug}
    else:
        kwargs = {'pk': instance.pk}

    url = reverse(viewname, kwargs=kwargs)

    return {
        'url': url,
    }


@register.inclusion_tag('buttons/delete.html')
def delete_button(instance, use_pk=False):
    viewname = _get_viewname(instance, 'delete')

    # Assign kwargs
    if hasattr(instance, 'slug') and not use_pk:
        kwargs = {'slug': instance.slug}
    else:
        kwargs = {'pk': instance.pk}

    url = reverse(viewname, kwargs=kwargs)

    return {
        'url': url,
    }


#
# List buttons
#

@register.inclusion_tag('buttons/add.html')
def add_button(url):
    url = reverse(url)

    return {
        'add_url': url,
    }


@register.inclusion_tag('buttons/import.html')
def import_button(url):

    return {
        'import_url': url,
    }


@register.inclusion_tag('buttons/export.html', takes_context=True)
def export_button(context, content_type=None):
    if content_type is not None:
        export_templates = ExportTemplate.objects.filter(content_type=content_type)
    else:
        export_templates = []

    return {
        'url_params': context['request'].GET,
        'export_templates': export_templates,
    }
