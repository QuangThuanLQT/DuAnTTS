# -*- coding: utf-8 -*-
{
    'name': "ton_kho_report",

    'summary': """
        ton_kho_report
    """,

    'description': """
        ton_kho_report
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
        'procurement',
        'product',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/ton_kho_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}