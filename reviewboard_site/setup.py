from setuptools import setup, find_packages

setup_args = {
    "name": "reviewboard_paas",
    "version": "0.1",
    "packages": find_packages(),
    "install_requires": [
        "ReviewBoard==1.7.13",
    ],
    "entry_points": {
        'console_scripts': [
            'install_rb = reviewboard_paas.scripts:install',
            'create_uwsgi_config = reviewboard_paas.scripts:create_uwsgi_config',
            'upgrade_rb = reviewboard_paas.scripts:rb_site_upgrade',
            'manage_rb = reviewboard_paas.scripts:rb_site_manage',
        ],
    },
}

setup(**setup_args)
