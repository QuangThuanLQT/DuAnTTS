# -*- coding: utf-8 -*-
{
    'name': "tuanhuy_stock_report",

    'summary': """
        tuanhuy_stock_report
    """,

    'description': """
        tuanhuy_stock_report
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
        'tuanhuy_stock',
        'tuanhuy_product',
        'modifier_product',
        'stock_report'

    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/stock_report_popup.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}