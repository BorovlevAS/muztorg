{
    "name": "BIKO: Acces right to valuation of products (MUZTORG)",
    "version": "14.0.1.0.0",
    "author": "Borovlev A.S.",
    "company": "BIKO Solutions",
    "depends": [
        "biko_base_module",
        "sale_margin",
        "product",
        "biko_change_product_view",
    ],
    "data": [
        "security/ir_access_roles.xml",
        "views/sale_order_views.xml",
        "views/product_product_views.xml",
        "views/product_template_views.xml",
        "views/stock_quant_vews.xml",
        "views/stock_valuation_layer_views.xml",
    ],
    "license": "LGPL-3",
    "installable": True,
    "application": True,
    "auto_install": False,
}
