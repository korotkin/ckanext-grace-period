import logging
from datetime import datetime

import ckan.logic.auth as logic_auth
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan import authz, logic
from ckan.common import _, g
import ckanext.grace_period.auth as auth

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
            'is_resource_available': auth.is_allowed_by_grace_period,
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
            'resource_show': auth.auth_resource_show,
            # 'resource_read': auth.auth_resource_show,
        }

