# -*- coding: utf-8 -*-
{
    'name': "Nova Poshta Data",

    'summary': """
        Integration with Nova Poshta services
        """,

    'description': """
        Integration with Nova Poshta services.
    """,

    'author': "Pechurin Evgen, LBS Company",
    'website': "https://lbs.company",
    'images': [

    ],
    'license': 'LGPL-3',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.2',

    # any module necessary for this one to work correctly
    'depends': ['product'],
    'external_dependencies': {'python': []},

    # always loaded
    'data': [
        'data/delivery_data.xml',
    ],
}
