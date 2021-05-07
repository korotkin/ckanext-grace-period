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
            'is_resource_available': self._is_resource_available,
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

    def _is_resource_available(self, pkg, res):
        if 'extras' in res and 'available_since' in res['extras']:
            try:
                available_since = res['extras']['available_since']
                dt = datetime.strptime(available_since, '%Y.%m.%d')
            except ValueError:
                is_available = False
            else:
                is_available = dt < datetime.now()
        else:
            is_available = True
        return is_available

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
        is_authorized = authz.is_authorized(
            'package_show', context, {'id': resource.get('package_id')}
        ).get('success', False)

        # Grace period check
        if is_authorized:
            is_resource_available = self._is_resource_available(
                pkg.__dict__, res.__dict__
            )
            # Check collaborators if authenticated
            # https://docs.ckan.org/en/2.9/maintaining/authorization.html#dataset-collaborators
            is_collaborator = False
            if g.userobj is not None and authz.check_config_permission(
                'allow_dataset_collaborators'
            ):
                is_collaborator = authz.user_is_collaborator_on_dataset(
                    g.userobj.id, pkg.id
                )

            is_authorized = is_resource_available or is_collaborator

        if is_authorized:
            return {'success': True}
        else:
            return {
                'success': False,
                'msg': _('User {} not authorized to read resource {}').format(
                    g.user, res.id
                )
            }
