# -*- coding: utf-8 -*-
{
    'name': "product_multi_barcode",

    'summary': """
        product_multi_barcode
    """,

    'description': """
        product_multi_barcode
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
        'product',
        'sales_team',
        'modifier_product',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/product_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}