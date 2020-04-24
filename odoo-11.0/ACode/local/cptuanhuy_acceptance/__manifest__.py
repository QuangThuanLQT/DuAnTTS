# -*- coding: utf-8 -*-
{
    'name': "cptuanhuy_acceptance",

    'summary': """
        cptuanhuy_acceptance
    """,

    'description': """
        cptuanhuy_acceptance
    """,

    'author': "Vieterp / Quy",
    'website': "http://www.vieterp.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'VietERP',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': [
        'cptuanhuy_project_contract',
        'cptuanhuy_stock',
    ],

    # always loaded
    'data': [
        'views/acceptance_view.xml',
        'security/ir.model.access.csv',
        'views/account_analytic_account_view.xml',
        'views/sale_order_view.xml',
    ],
    # only loaded in demonstration mode
}