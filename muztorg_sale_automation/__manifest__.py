{
    "name": "Simbioz Sale Order Automation",
    "summary": "Simbioz Sale Order Automation",
    "version": "14.0.1.0.0",
    "license": "LGPL-3",
    "author": "Borovlev A.S.",
    "company": "BIKO Solutions",
    "depends": [
        "sale",
        "stock",
    ],
    "data": [
        "views/sale_order_views.xml",
        "views/stock_warehouse.xml",
        "wizard/stock_reservation_wiz_view.xml",
        "views/stock_reservation_view.xml",
        "security/ir.model.access.csv",
        "data/stock_move_data.xml",
        "data/ir_sequence_data.xml",
        "data/ir_cron.xml",
    ],
    "demo": [],
    "excludes": [
        "sale_order_automation",
        "odoo_stock_reservation",
    ],
    "installable": True,
}
