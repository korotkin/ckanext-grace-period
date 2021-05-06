from setuptools import find_packages, setup


setup(
    name='ckanext-grace-period',
    version='0.0.1',
    description='Resource data should be available after the dataset is created and made public.',
    long_description="""""",
    # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[],
    keywords='',
    author='https://github.com/geosolutions-it/ckanext-grace-period/graphs/contributors',
    author_email='info@geo-solutions.it',
    url='https://github.com/geosolutions-it/ckanext-grace-period',
    packages=find_packages(exclude=['ez_setup', 'tests']),
    install_requires=[
        'ckan>=2.9'
    ],
    namespace_packages=['ckanext', 'ckanext.grace_period'],
    include_package_data=True,
    zip_safe=False,
    entry_points="""
        [ckan.plugins]
        grace_period=ckanext.grace_period.plugin:GracePeriodPlugin
    """,
    message_extractors={
        'ckanext': [
            ('**.py', 'python', None),
            ('**.js', 'javascript', None),
            ('**/templates/**.html', 'ckan', None),
        ]
    }
)
