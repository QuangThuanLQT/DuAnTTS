# -*- coding: utf-8 -*-
{
    'name': "tuanhuy_account_account",

    'summary': """
        tuanhuy_account_account
    """,

    'description': """
        tuanhuy_account_account
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
        'account',
    ],

    # always loaded
    'data': [
        'views/account_move_line_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}