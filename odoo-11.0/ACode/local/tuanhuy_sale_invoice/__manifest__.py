# -*- coding: utf-8 -*-
{
    'name': "tuanhuy_sale_invoice",

    'summary': """
        tuanhuy_sale_invoice
    """,

    'description': """
        tuanhuy_sale_invoice
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
        'tuanhuy_sale',
        'tuanhuy_purchase',
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}