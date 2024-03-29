{
    "name": "BIKO: Добавляет контроль заполнения поля 'Контакт клиента', контроль дублей по ЕДРПОУ",
    "version": "14.0.1.1.7",
    "author": "Borovlev A.S.",
    "company": "BIKO Solutions",
    "depends": [
        "contacts",
        "kw_account_partner_requisites",
        "sale",
        "sale_stock",
        "biko_base_module",
    ],
    "data": [
        "views/res_partner_views.xml",
        "views/sale_order_views.xml",
    ],
    "license": "LGPL-3",
    "installable": True,
    "application": True,
    "auto_install": False,
}
