# -*- coding: utf-8 -*-
{
    'name': "tuanhuy_stock",

    'summary': """
        tuanhuy_stock
    """,

    'description': """
        tuanhuy_stock
    """,

    'author': "VietERP / Sang",
    'website': "http://www.vieterp.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'VietERP',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'stock',
        'tuanhuy_check_report_file',
        'sale_purchase_returns',
        'product_pack',
        'modifier_product',
        'tuanhuy_product',
    ],

    # always loaded
    'data': [
        'data/data.xml',
        'views/stock_inventory_views.xml',
        'views/stock_move.xml',
        'views/update_amount_stock.xml',
        'views/stock_picking_view.xml',
        'views/stock_picking_history_view.xml',
        'views/tuanhuy_update_date.xml',
        'security/ir.model.access.csv',
        'views/do_transfer_warning_view.xml',
        'views/stock_access_right.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}