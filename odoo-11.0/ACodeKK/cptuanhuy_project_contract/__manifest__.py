# -*- coding: utf-8 -*-
{
    'name': "cptuanhuy_project_contract",

    'summary': """
        cptuanhuy_project_contract
    """,

    'description': """
        cptuanhuy_project_contract
    """,

    'author': "VietERP / Luc",
    'website': "http://www.vieterp.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'VietERP',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'cptuanhuy_job_costing_management',
        'account_budget',
        'stable_account_analytic_analysis',
        'analytic',
        'account_guarantee',
        'cptuanhuy_project',
        'sale',
        'mrp',
        'maintenance',
        'sales_team',
        'account_bank_voucher',
    ],

    # always loaded
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'views/account_guarantee_view.xml',
        'views/job_costing_view.xml',
        'views/account_analytic_account_view.xml',
        'views/sale_order_type_view.xml',
        'views/sale_order_view.xml',
    ],
}