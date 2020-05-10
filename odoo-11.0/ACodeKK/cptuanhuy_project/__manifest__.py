# -*- coding: utf-8 -*-
{
    'name': "cptuanhuy_project",

    'summary': """
        cptuanhuy_project
    """,

    'description': """
        cptuanhuy_project
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
        'odoo_job_costing_management',
        'project',
        'job_quotaion',
        'project_issue',
        'hr_timesheet',
        'stable_account_analytic_analysis',
        'tuanhuy_product',
    ],

    # always loaded
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'views/task_view.xml',
        'views/project_view.xml',
        'views/ir_attachment_view.xml',
        'views/menu_modifier.xml',
        'views/contract_view.xml',
        'views/hide_menu.xml',
        'views/project_task_type_view.xml',
        'views/job_quotation_view.xml',
        'views/job_costing_view.xml',
        'views/product_view.xml',
        'views/project_planning_view.xml',
        'views/account_guarantee.xml',
        'views/update_price_job_costing_view.xml',
        'views/job_quotaion_type.xml',
    ],
    # only loaded in demonstration mode
}