# -*- coding: utf-8 -*-
{
    'name': "tuanhuy_stock_check_product",

    'summary': """
        tuanhuy_stock_check_product
    """,

    'description': """
        tuanhuy_stock_check_product
    """,

    'author': "VietERP / Vu",
    'website': "http://www.vieterp.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'VietERP',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base'
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}