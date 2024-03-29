{
    "name": "BIKO: Sale Order POS (Muztorg)",
    "version": "14.0.2.0.0",
    "author": "Borovlev A.S.",
    "company": "BIKO Solutions",
    "depends": [
        "point_of_sale",
        "sale",
        "phone_validation",
        "checkbox_integration_sale_order",
        "muztorg_sale_order_customization",
    ],
    "data": [
        "views/sale_order_pos_menu.xml",
        "views/pos_config_views.xml",
        "views/sale_order_views.xml",
        "views/so_payment_type_views.xml",
        "wizards/sale_order_checkbox_wizard.xml",
        "security/ir.model.access.csv",
    ],
    "license": "LGPL-3",
    "installable": True,
    "application": True,
    "auto_install": False,
}
