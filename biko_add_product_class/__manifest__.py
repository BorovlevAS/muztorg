{
    "name": "BIKO: Добавить класс товара",
    "version": "14.0.1.1.6",
    "author": "Borovlev A.S.",
    "company": "BIKO Solutions",
    "depends": ["biko_base_module", "pim", "product"],
    "data": [
        "views/product_class_views.xml",
        "views/biko_pim_menus.xml",
        "views/product_template_views.xml",
        "views/product_product_views.xml",
        "security/ir_access_roles.xml",
        "security/ir.model.access.csv",
        "views/res_config_settings_views.xml",
        "data/crons.xml",
    ],
    "license": "LGPL-3",
    "installable": True,
    "application": True,
    "auto_install": False,
}
