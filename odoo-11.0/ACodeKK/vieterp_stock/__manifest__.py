# -*- coding: utf-8 -*-
{
    'name': "vieterp_stock",

    'summary': """
        vieterp_stock
    """,

    'description': """
        vieterp_stock
    """,

    'author': "VietERP / Sang",
    'website': "http://www.vieterp.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'stock',
        'hr',
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/stock_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}