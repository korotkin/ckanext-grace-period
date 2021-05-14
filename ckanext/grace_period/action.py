from __future__ import unicode_literals

from logging import getLogger

import ckan.logic
from ckan.logic.action.get import resource_view_list
from ckanext.grace_period import auth

log = getLogger(__name__)

_get_or_bust = ckan.logic.get_or_bust
NotFound = ckan.logic.NotFound


def grace_period_restricted_resource_view_list(context, data_dict):
    model = context['model']
    id = _get_or_bust(data_dict, 'id')
    resource = model.Resource.get(id)
    if not resource:
        raise NotFound
    authorized = auth.auth_resource_show(
        context, {'id': resource.get('id'), 'resource': resource}).get('success', False)
    if not authorized:
        return []
    else:
        return resource_view_list(context, data_dict)
