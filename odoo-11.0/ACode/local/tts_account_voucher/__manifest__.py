# -*- coding: utf-8 -*-
{
    'name': "tts_account_voucher",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Vieterp / Luc",
    'website': "http://www.vieterp.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['sale','tuanhuy_account_voucher'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/account_voucher_views.xml',
        'views/sale_order_view.xml',
        'views/views.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
}