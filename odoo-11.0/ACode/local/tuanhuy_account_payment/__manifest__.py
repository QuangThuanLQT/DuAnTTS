# -*- coding: utf-8 -*-
{
    'name': "tuanhuy_account_payment",

    'summary': """
        tuanhuy_account_payment
    """,

    'description': """
        tuanhuy_account_payment
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
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/account_payment_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}