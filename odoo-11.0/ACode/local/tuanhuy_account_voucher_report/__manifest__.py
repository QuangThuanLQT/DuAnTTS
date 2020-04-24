# -*- coding: utf-8 -*-
{
    'name': "tuanhuy_account_voucher_report",

    'summary': """
        tuanhuy_account_voucher_report
    """,

    'description': """
        tuanhuy_account_voucher_report
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
        'account_bank_voucher',
        'account_voucher',
        'tuanhuy_account_voucher',
        'cptuanhuy_accounting'
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/voucher_report.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}