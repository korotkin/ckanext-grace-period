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
    res = data_dict.get('resource', context.get('resource', {}))
    pkg = res.package

    # Basic check:
    # Ensure user who can edit the package can see the resource
    resource = data_dict.get('resource', context.get('resource', {}))
    if not resource:
        resource = logic_auth.get_resource_object(context, data_dict)
    if type(resource) is not dict:
        resource = resource.as_dict()

    if authz.is_authorized(
        'package_update', context,
        {'id': resource.get('package_id')}).get('success'):
        return {'success': True}

    auth = authz.is_authorized('package_show', context, {'id': resource.get('package_id')})
    if not auth.get('success', False):
        return {
            'success': False,
            'msg': _('User {} not authorized to read resource {}').format(g.user, res.id)
        }

    # Grace period check
    if is_allowed_by_grace_period(res.__dict__):
        return {'success': True}

    # Check collaborators if authenticated
    # https://docs.ckan.org/en/2.9/maintaining/authorization.html#dataset-collaborators

    if g.userobj and \
            authz.check_config_permission('allow_dataset_collaborators') and \
            authz.user_is_collaborator_on_dataset(g.userobj.id, pkg.id):
        return {'success': True}

    return {
        'success': False,
        'msg': _('User {} not authorized to read resource {} in its grace period').format(
            g.userobj.name if g.userobj else '-Anonymous-', res.id
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
