{
    "name": "BIKO: Reconciliation improvement for MUZTORG",
    "version": "14.0.2.0.0",
    "author": "Borovlev A.S.",
    "company": "BIKO Solutions",
    "depends": [
        "base_accounting_kit",
        "muztorg_sale_order_customization",
    ],
    "data": [
        "views/assets.xml",
    ],
    "qweb": ["static/src/xml/payment_matching.xml"],
    "license": "LGPL-3",
    "installable": True,
    "application": True,
    "auto_install": False,
}
