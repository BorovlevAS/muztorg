# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.

{
    'name': 'Stock Reservation on Sales Flow',
    'version': '4.2.19',
    'category': 'Inventory/Inventory',
    'license': 'Other proprietary',
    'price': 19.0,
    'currency': 'EUR',
    'summary': """This app allow you to manage stock reservation from your Quote/Sales.""",
    'description': """
stock Reservation
product Reservation
item Reservation
warehouse
sale Reservation
sales Reservation
odoo_stock_reservation
stock_reservation
sale order Reservation
sales order Reservation
quote Reservation
quotation Reservation
my Reservation
stock item Reservation
lot Reservation
Stock Reservation
stock reservations on products
stock reservations
reserved products
reservation
Sales Stock Reservation
Product Booking
Stock Booking
reserved quantity
reserved stock
forcasted stock
Reservation quantity
Forcasted quantity
Reservation
reservation availability
stock reservation in sales order
stock reservation in quotation
stock reservation in sales
stock reservation at quotation
stock reservation at quote
stock reservation quote
stock reservation sales
stock reservation sale
stock reservation quotation
Reserve Stock
Stock Reservation at Quotation
ecommerce Reservation
shop Reservation
customer Reservation
client Reservation
odoo Reservation
odoo stock
stock module
item

    """,
    'author': 'Probuse Consulting Service Pvt. Ltd.',
    'website': 'http://www.probuse.com',
    'support': 'contact@probuse.com',
    # 'live_test_url': 'https://www.youtube.com/watch?v=fAhnDXEVfqg',
    'live_test_url': 'https://probuseappdemo.com/probuse_apps/odoo_stock_reservation/6',
    # 'https://youtu.be/4Hz0R0lr-SY',
    'images': ['static/description/sst.jpg'],
    'depends': [
        'sale_stock', 'sale_management','sale'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/stock_move_data.xml',
        'data/stock_reservation_mail.xml',
        'data/ir_cron.xml',
        'wizard/stock_reservation_wiz_view.xml',
        'views/sale_order_view.xml',
        'views/stock_reservation_view.xml',
        'views/res_conf.xml',
        #        'views/stock_move_view.xml',
    ],
    'installable': True,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
