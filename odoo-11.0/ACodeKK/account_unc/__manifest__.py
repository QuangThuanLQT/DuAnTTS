# -*- coding: utf-8 -*-
{
    'name': "account_unc",

    'summary': """
        Uy Nhiem Chi
    """,

    'description': """
        Uy Nhiem Chi
    """,

    'author': "VietERP",
    'website': "http://www.vieterp.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'VietERP',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'account',
        'product'
    ],
    # always loaded
    'data': [
        'views/access_right.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/mandate.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}