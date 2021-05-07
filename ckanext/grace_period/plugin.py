import logging
from datetime import datetime

import ckan.logic.auth as logic_auth
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan import authz, logic
from ckan.common import _, g

log = logging.getLogger(__name__)


class GracePeriodPlugin(plugins.SingletonPlugin, toolkit.DefaultDatasetForm):
    '''
    Add grace period into CKAN resources
    '''
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IDatasetForm)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)

    def update_config(self, config):
        # Add this plugin's templates dir to CKAN's extra_template_paths, so
        # that CKAN will use this plugin's custom templates.
        toolkit.add_template_directory(config, u'templates')

    def get_helpers(self):
        return {
            'is_resource_available': self._is_allowed_by_grace_period,
        }

    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        # package types not handled by any other IDatasetForm plugin.
        return True

    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []

    def package_form(self):
        return super().package_form()

    def _is_allowed_by_grace_period(self, pkg, res):
        if 'extras' in res:
            available_since = res['extras'].get('available_since', None)
            if available_since:
                try:
                    return self._try_parse(available_since) < datetime.now()
                except ValueError as e:
                    log.warning(e)
                    return False
        return True

    def _try_parse(self, s):
        for date_fmt in ('%Y.%m.%d', '%Y-%m-%d', '%Y %m %d'):
            try:
                return datetime.strptime(s, date_fmt)
            except ValueError:
                pass
        raise ValueError(f'Could not parse grace period end "{s}"')

    def _modify_package_schema(self, schema):
        schema['extras'].update({
            'available_since': [
                toolkit.get_validator('ignore_missing'),
                toolkit.get_converter('convert_from_extras'),
            ]
        })
        return schema

    def create_package_schema(self):
        schema = super().create_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self):
        schema = super().update_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def show_package_schema(self):
        schema = super().show_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def get_auth_functions(self):
        return {
            'resource_show': self.auth_resource_show,
            'resource_read': self.auth_resource_show,
        }

    @logic.auth_allow_anonymous_access
    def auth_resource_show(self, context, data_dict):
        """
        if the grace period is set and the user does not belong to collaborators
         --> do not allow access
        :return:
        """
        res = context['resource']
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
        if self._is_allowed_by_grace_period(pkg.__dict__, res.__dict__):
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
