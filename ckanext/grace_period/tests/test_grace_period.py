import pytest

import ckan.tests.factories as factories
from ckan import logic, model
from ckan.common import g
from ckan.lib import authenticator
from ckan.lib.create_test_data import CreateTestData
from ckan.lib.helpers import url_for
from ckan.tests import helpers


@pytest.mark.usefixtures('clean_db', 'with_request_context')
@pytest.mark.usefixtures('with_plugins')
class TestDatasetSearch(object):

    def authenticated_user(self):
        password = 'somepass'
        user = CreateTestData.create_user('a_user', **{'password': password})
        environ = {}
        identity = {'login': user.name, 'password': password}
        auth = authenticator.UsernamePasswordAuthenticator()
        g.user = auth.authenticate(environ, identity)
        g.userobj = user
        return user

    def test_grace_period_notification(self, app):
        user = factories.User()
        org = factories.Organization(
            users=[{'name': user['name'], 'capacity': 'member'}]
        )
        dataset = factories.Dataset(
            private=False,
            owner_org=org[u'id'],
        )

        resource = factories.Resource(
            owner_org=org[u'id'],
            package_id=dataset[u'id'],
            available_since='2400.01.01',
        )
        url = url_for(
            '{}.read'.format(dataset['type']),
            id=dataset['id']
        )
        response = app.get(url=url, status=200)
        assert 'Available since' in response.body

        resource_url = url_for(
            '{}_resource.read'.format(dataset['type']),
            id=dataset['id'], resource_id=resource['id']
        )
        app.get(url=f'{resource_url}/download', status=404)

    @pytest.mark.parametrize('params', [
        ('member', True),
        ('editor', False),
        ('admin', False),
    ])
    @pytest.mark.ckan_config('ckan.auth.allow_admin_collaborators', True)
    def test_grace_period_org_user_access(self, app, params):
        capacity, raises_not_authotized = params
        user = factories.User()
        collaborator_user = self.authenticated_user()
        org = factories.Organization(
            users=[
                {'name': user['name'], 'capacity': 'admin'},
                {'name': collaborator_user.name, 'capacity': capacity}
            ]
        )
        dataset = factories.Dataset(
            private=False,
            creator_user_id=user['id'],
            owner_org=org[u'id'],
        )
        resource = factories.Resource(
            owner_org=org[u'id'],
            package_id=dataset[u'id'],
            available_since='2400.01.01',
        )

        context = {
            'user': collaborator_user.name,
            'ignore_auth': False,
            'model': model,
        }
        if raises_not_authotized is True:
            with pytest.raises(logic.NotAuthorized):
                helpers.call_auth(
                    'resource_view_list',
                    context=context, id=resource['id']
                )
        else:
            res = helpers.call_auth(
                'resource_view_list',
                context=context, id=resource['id']
            )
            assert res is True

    def test_grace_period_open_by_the_other_user(self):
        org1 = factories.Organization()
        dataset = factories.Dataset(owner_org=org1['id'])
        resource = factories.Resource(
            package_id=dataset['id'],
            available_since='2400.01.01',
        )

        user = self.authenticated_user()
        context = {
            'user': user.name,
            'ignore_auth': False,
            'model': model,
        }

        with pytest.raises(logic.NotAuthorized):
            helpers.call_auth(
                'resource_view_list',
                context=context, id=resource['id']
            )
