# -*- coding: utf-8 -*-
{
    'name': "account_bank_voucher_modifier",

    'summary': """Uy Nhiem Chi""",

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
    'depends': [
        'base',
        'sale',
        'purchase',
        'account_bank_voucher',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/account_voucher_unc_view.xml',
    ],
}