# ckanext-grace-period

This extension allow resources to be protected by a **grace period**, i.e. the dataset owner can set a date before which the resource data will not be available to the public.

Within the grace period, data will only be accessible to: 
- dataset owner, 
- dataset's organization admins, 
- [dataset collaborators](https://docs.ckan.org/en/2.9/maintaining/authorization.html#dataset-collaborators)
- superuser

Resource data will not be available neither by direct download nor through the datastore API.


## Requires

 * CKAN 2.9+

## Required plugins

    datastore datapusher


## Configuration


Supports  [Dataset collaborators](https://docs.ckan.org/en/2.9/maintaining/authorization.html#dataset-collaborators) feature:

    ckan.auth.allow_dataset_collaborators = true

