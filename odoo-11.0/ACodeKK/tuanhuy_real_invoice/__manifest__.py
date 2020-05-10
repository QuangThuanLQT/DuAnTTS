# -*- coding: utf-8 -*-
{
    'name': "tuanhuy_real_invoice",

    'summary': """
        Add Real Invoice Tab""",

    'description': """
        Add Real Invoice Tab
    """,

    'author': "VietERP / Quy",
    'website': "http://www.vieterp.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'VietERP',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': [
        'cptuanhuy_accounting',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/account_invoice_view.xml',
    ],
}