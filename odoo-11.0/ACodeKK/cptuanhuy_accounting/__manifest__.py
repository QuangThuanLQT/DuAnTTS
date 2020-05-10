# -*- coding: utf-8 -*-
{
    'name': "cptuanhuy_accounting",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "VietERP",
    'website': "http://www.vieterp.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'VietERP',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'tuanhuy_sale',
        'cptuanhuy_mrp',
        'account_guarantee',
        'tuanhuy_account_reports',
        'account_unc',
        'account_gbn',
        'account_voucher',
        'account_bank_voucher',
        'cptuanhuy_project_contract',
        'tuanhuy_invoice',
        'stable_hr_timesheet_invoice',
        'asset_location'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/phan_bo_view.xml',
        'views/account_asset_asset_view.xml',
        'views/mrp_production_view.xml',
        'views/account_move_line_view.xml',
        'views/modifier_menu.xml',
        'views/account_voucher_view.xml',
        'views/account_invoice.xml',
        'views/import_account_voucher_view.xml',
        'views/sale_order_view.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
}