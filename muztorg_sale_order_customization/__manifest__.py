{
    "name": "BIKO: Sale Order Customization (MUZTORG)",
    "version": "14.0.3.0.0",
    "author": "Borovlev A.S.",
    "company": "BIKO Solutions",
    "depends": [
        "sale",
        "sale_stock",
        "biko_base_module",
        "account",
    ],
    "data": [
        "views/sale_order_views.xml",
        "views/so_payment_type_views.xml",
        "security/ir.model.access.csv",
        "data/so_payment_types.xml",
    ],
    "license": "LGPL-3",
    "installable": True,
    "application": True,
    "auto_install": False,
}
