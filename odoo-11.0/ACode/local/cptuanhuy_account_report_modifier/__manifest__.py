# -*- coding: utf-8 -*-
{
    'name': "cptuanhuy_account_report_modifier",

    'summary': """
        cptuanhuy_account_report_modifier
    """,

    'description': """
        cptuanhuy_account_report_modifier
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
        'tuanhuy_account_reports'
    ],

    # always loaded
    'data': [
        'views/account_report_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
}
