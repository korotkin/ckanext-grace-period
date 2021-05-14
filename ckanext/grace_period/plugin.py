import logging

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.grace_period.action as action
import ckanext.grace_period.auth as auth
from ckanext.grace_period.validators import date_only_validator

log = logging.getLogger(__name__)


class GracePeriodPlugin(plugins.SingletonPlugin, toolkit.DefaultDatasetForm):
    '''
    Add grace period into CKAN resources
    '''

    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IDatasetForm)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)

    # IConfigurer
    def update_config(self, config):
        # Add this plugin's templates dir to CKAN's extra_template_paths, so
        # that CKAN will use this plugin's custom templates.
        toolkit.add_template_directory(config, u'templates')

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'is_resource_available': auth.is_allowed_by_grace_period,
        }

    # IValidators
    def get_validators(self):
        return {
            'date_only': date_only_validator,
        }

    # IDatasetForm
    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        # package types not handled by any other IDatasetForm plugin.
        return True

    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []

    def _modify_package_schema(self, schema):
        schema['resources'].update({
            'available_since': [
                toolkit.get_validator('ignore_missing'),
                toolkit.get_validator('date_only'),
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

    # IAuthFunctions
    def get_auth_functions(self):
        return {
            'resource_show': auth.auth_resource_show,
            'resource_view_show': auth.auth_resource_show,
        }

    # IActions
    def get_actions(self):
        return {
            'resource_view_list': action.grace_period_restricted_resource_view_list,
        }
