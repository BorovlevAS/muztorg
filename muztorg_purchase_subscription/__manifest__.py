# Copyright 2023 Domatix - Carlos Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Muztorg Subscription management",
    "summary": "Generate recurring bills.",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "Borovlev AS, BIKO Solutions",
    "depends": [
        "purchase",
        "account",
        "product",
        "biko_add_h_product_ux",
    ],
    "data": [
        "views/product_template_views.xml",
        "views/purchase_subscription_views.xml",
        "views/purchase_subscription_stage_views.xml",
        "views/purchase_subscription_tag_views.xml",
        "views/purchase_subscription_template_views.xml",
        "views/purchase_order_views.xml",
        "views/res_partner_views.xml",
        "data/ir_cron.xml",
        "data/purchase_subscription_data.xml",
        "wizard/close_subscription_wizard.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
    "application": True,
}
