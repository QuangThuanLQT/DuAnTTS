# -*- coding: utf-8 -*-
{
    'name': "cptuanhuy_stock",

    'summary': """
        cptuanhuy_stock    
    """,

    'description': """
        cptuanhuy_stock
    """,

    'author': "VietERP / Luc",
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
        'purchase',
        'sale',
        'tuanhuy_stock',
        'purchase_request'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/cron_job.xml',
        'views/stock_picking_type.xml',
        'views/import_product_template.xml',
        'views/import_stock_in.xml',
        'views/stock_picking_views.xml',
        'data/data.xml',
        'views/stock_inventory.xml',
        'views/stock_internal_type.xml',
        'views/stock_picking_report_view.xml',
        'views/product_template.xml',
        'views/purchase_request.xml',
    ],
    # only loaded in demonstration mode
}