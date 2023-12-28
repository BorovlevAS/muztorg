{
    "name": "BIKO: Патч модуля Новой Почты под требования МУЗТОРГ",
    "version": "14.0.1.1.26",
    "author": "Borovlev A.S.",
    "company": "BIKO Solutions",
    "depends": [
        "biko_client_add_mandatory_contact",
        "delivery_novaposhta",
    ],
    "data": [
        "views/stock_views.xml",
        "views/res_partner_views.xml",
        "views/ttn.xml",
        "views/warehouse_np_views.xml",
        "views/sale_order.xml",
        "security/ir.model.access.csv",
    ],
    "license": "LGPL-3",
    "installable": True,
    "application": True,
    "auto_install": False,
}
