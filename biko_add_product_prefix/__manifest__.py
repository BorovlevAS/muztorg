# -*- coding: utf-8 -*-
{
    "name": "BIKO: Добавляет префикс в категорию и в продукт",
    "version": "14.0.1.1.1",
    "author": "Borovlev A.S.",
    "company": "BIKO Solutions",
    "depends": ["biko_base_module", "pim", "product"],
    "data": [
        'views/product_prefix_views.xml',
        'views/biko_prifix_menus.xml',
        'views/product_views.xml',
        
        'security/ir_access_roles.xml',
        'security/ir.model.access.csv',
    ],
    "license": "LGPL-3",
    "installable": True,
    "application": True,
    "auto_install": False,
}
