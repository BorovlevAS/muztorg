# -*- coding: utf-8 -*-
{
    "name": "BIKO: Добавить класс товара",
    "version": "14.0.1.1.3",
    "author": "Borovlev A.S.",
    "company": "BIKO Solutions",
    "depends": ["pim", "product"],
    "data": [
        'views/product_class_views.xml',
        'views/product_model_views.xml',
        'views/biko_pim_menus.xml',
        'views/product_template_views.xml',
        
        'security/ir_access_roles.xml',
        'security/ir.model.access.csv',
    ],
    "license": "LGPL-3",
    "installable": True,
    "application": True,
    "auto_install": False,
}