{
    "name": "Nova Poshta Shipping",
    "summary": """Integration with Nova Poshta services""",
    "author": "Simbioz",
    "website": "https://simbioz.ua",
    "license": "AGPL-3",
    "category": "Uncategorized",
    "version": "14.0.0.1.7",
    "depends": [
        "contacts",
        "product",
        "sale",
        "stock",
        "web_notify",
        "delivery",
        "novaposhta_data",
        "partner_org_chart",
        "queue_job",
    ],
    "external_dependencies": {"python": ["json", "requests", "logging"]},
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/street_list_sync.xml",
        "views/SpreadSheets.xml",
        "views/warehouses.xml",
        "views/res_partner.xml",
        "views/delivery_carrier.xml",
        "views/ttn.xml",
        "views/stock.xml",
        "views/sale_order.xml",
        "views/ttn_sync.xml",
        "views/res_config_settings_views.xml",
        "data/crons.xml",
        "views/menus.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}