# -*- coding: utf-8 -*-
{
    'name': "stock_report",

    'summary': """
    stock_report""",

    'description': """
        VietERP Order
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
        'stock',
        'sale_discount_total',
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'reports/stock_delivery_report.xml',
        'reports/stock_import_report.xml',
        'reports/stock_delivery_report_a4.xml',
        # 'views/views.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}