# -*- coding: utf-8 -*-
{
    'name': "account_bank_voucher",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        UNC, UNT modifier account.voucher
    """,

    'author': "Vieterp /Luc",
    'website': "http://www.vieterp.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'account_voucher',
        'tuanhuy_account_voucher',
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',

        'views/template.xml',
        'report/account_voucher.xml',
        'views/unc_view.xml',
        'views/unt_view.xml',
        'views/res_partner.xml',

    ],
}