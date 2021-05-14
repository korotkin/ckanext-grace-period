from ckan.common import _
from ckan.plugins.toolkit import Invalid
from ckanext.grace_period.auth import _try_parse


def date_only_validator(value):
    try:
        bool(value) and _try_parse(value)
    except ValueError as e:
        raise Invalid(
            _('Wrong date format. Please use either "YYYY.mm.dd", "YYYY mm dd" or" YYYY-mm-dd".')
        )
    return value
