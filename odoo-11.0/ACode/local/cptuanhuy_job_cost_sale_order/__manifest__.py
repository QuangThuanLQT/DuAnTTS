# -*- coding: utf-8 -*-
{
    'name': "cptuanhuy_job_cost_sale_order",

    'summary': """
        cptuanhuy_job_cost_sale_order
    """,

    'description': """
        cptuanhuy_job_cost_sale_order
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
        'cptuanhuy_project',
        'cptuanhuy_project_contract',
        'odoo_job_costing_management',
        'sales_team',
    ],

    # always loaded
    'data': [
        'views/job_costing_view.xml',
        'views/crm_team_view.xml',
    ],
    # only loaded in demonstration mode
}