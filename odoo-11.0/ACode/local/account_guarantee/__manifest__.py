# -*- coding: utf-8 -*-
{
    'name': "VietERP - account_guarantees",

    'summary': """
        VietERP - account_guarantees
    """,

    'description': """
        VietERP - account_guarantees
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
        'account_bank_base',
        'account_asset',
        'odoo_job_costing_management',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
        'views/account_guarantee_views.xml',
        'data/ir_sequence_data.xml',
        'data/data.xml',
        'views/guarantee_notification_settings.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}