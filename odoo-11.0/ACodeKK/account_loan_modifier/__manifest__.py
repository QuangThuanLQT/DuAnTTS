# -*- coding: utf-8 -*-
{
    'name': "account_loan_modifier",

    'summary': """
        account_loan_modifier
    """,

    'description': """
        account_loan_modifier
    """,

    'author': "VietERP / Cuong",
    'website': "http://www.vieterp.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'VietERP',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'account_loan',
        'account_asset',
        'account_guarantee',
        'account_bank_base',
        'account',

    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/account_loan_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}