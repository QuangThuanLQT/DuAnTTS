# -*- coding: utf-8 -*-
{
    'name': "cptuanhuy_job_costing_management",

    'summary': """
        cptuanhuy_job_costing_management
    """,

    'description': """
        cptuanhuy_job_costing_management
    """,

    'author': "Vieterp / Luc",
    'website': "http://www.vieterp.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'VietERP',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'odoo_job_costing_management'
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/job_costing_view.xml',
        'views/stock_picking.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}