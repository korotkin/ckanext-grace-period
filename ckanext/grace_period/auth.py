import logging
from datetime import datetime

import ckan.logic.auth as logic_auth
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan import authz, logic
from ckan.common import _, g

log = logging.getLogger(__name__)

DATE_FORMATS = ('%Y.%m.%d', '%Y-%m-%d', '%Y %m %d')


@logic.auth_allow_anonymous_access
def auth_resource_show(context, data_dict):
    """
    if the grace period is set and the user does not belong to collaborators
     --> do not allow access
    :return:
    """
    resource = data_dict.get('resource', context.get('resource', {}))
    if not resource:
        resource = logic_auth.get_resource_object(context, data_dict)
    if type(resource) is not dict:
        resource = resource.as_dict()

    pkg_id = resource.get('package_id')

    # Basic check:
    # Ensure user who can edit the package can see the resource
    if authz.is_authorized(
        'package_update', context,
        {'id': pkg_id}).get('success'):
        return {'success': True}

    # If the user is not authorized, deny access
    auth = authz.is_authorized('package_show', context, {'id': pkg_id})
    if not auth.get('success', False):
        return {
            'success': False,
            'msg': _('User {} not authorized to read resource').format(g.user)
        }

    # The user is authorized so far: now check for grace period
    # If there are not grace period constraints, the resource is allowed
    if is_allowed_by_grace_period(resource):
        return {'success': True}

    # We are within grace period.
    # Owner and admins have already been granted access (because they can update the package)
    # Allow read-only collaborators to access the resource
    if g.userobj and \
            authz.check_config_permission('allow_dataset_collaborators') and \
            authz.user_is_collaborator_on_dataset(g.userobj.id, pkg_id):
        return {'success': True}

    return {
        'success': False,
        'msg': _('User {} not authorized to read resource in its grace period').format(
            g.userobj.name if g.userobj else '-Anonymous-'
        )
    }


def is_allowed_by_grace_period(res):
    if 'extras' in res:
        available_since = res['extras'].get('available_since', None)
    else:
        available_since = res.get('available_since', None)
    if available_since:
        try:
            return _try_parse(available_since) < datetime.now()
        except ValueError as e:
            log.warning(e)
            return False
    return True


def _try_parse(s):
    for date_fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s, date_fmt)
        except ValueError:
            pass
    raise ValueError(f'Could not parse grace period end "{s}"')
