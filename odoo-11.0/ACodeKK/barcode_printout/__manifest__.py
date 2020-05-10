# -*- coding: utf-8 -*-
{
    'name': "barcode_printout",

    'summary': """
        barcode_printout""",

    'description': """
        barcode_printout
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
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/barcode_views.xml',
        'views/product_barcode_generator_views.xml',
        'data/data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}