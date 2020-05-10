# -*- coding: utf-8 -*-
{
    'name': "tuanhuy_account_reports",

    'summary': """
        tuanhuy_account_reports
    """,

    'description': """
        tuanhuy_account_reports
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
        'account_reports',
        'tuanhuy_account_account',
        'search_by_range',
        'account_voucher',
        'purchase'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/account_financial_html_report.xml',
        'views/menu.xml',
        'views/account_report_excel.xml',
        'views/sale_report_excel.xml',
        'views/account_move.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
}
