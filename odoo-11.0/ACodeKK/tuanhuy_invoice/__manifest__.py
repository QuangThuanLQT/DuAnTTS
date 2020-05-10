# -*- coding: utf-8 -*-
{
    'name': "VietERP - tuanhuy_invoice",

    'summary': """
        VietERP - tuanhuy_invoice
    """,

    'description': """
        VietERP - tuanhuy_invoice
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
        'purchase',
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/account_invoice_views.xml',
        # 'wizard/report_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}