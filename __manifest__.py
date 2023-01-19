# -*- coding: utf-8 -*-
{
    'name': "BIKO: additional fields",
    'description': """Adding fields, changing views""",
    "summary": """
        Добавлены новые поля в контакты и справочники - программы, источники для контактов
        Немного обновил пункты меню для контактов и компаний
    """,
    'version': '14.0.1.1.3',
    'author': 'Borovlev AS',
    'company': 'BIKO',
    "depends": ['base', 'contacts', 'crm'],
    "data": [
        'views/biko_software_views.xml',
        'views/biko_source_views.xml',
        'views/res_partner_views.xml',
        'views/crm_lead_views.xml',
        'views/menu.xml',
        'security/ir.model.access.csv',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
    "sequence": -1,
}