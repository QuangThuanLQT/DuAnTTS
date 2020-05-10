# -*- coding: utf-8 -*-
{
    'name': "VietERP - account_bank_base",

    'summary': """
        VietERP - account_bank_base
    """,

    'description': """
        VietERP - account_bank_base
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
        'account_asset',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/bank_views.xml',
        'views/res_partner_views.xml',
        'views/bank_estimate_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}