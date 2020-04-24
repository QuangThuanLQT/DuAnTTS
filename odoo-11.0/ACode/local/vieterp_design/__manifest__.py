# -*- coding: utf-8 -*-
{
    'name': "vieterp_design",

    'summary': """
        VietERP Design
    """,

    'description': """
        VietERP Design
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
        'project',
        'project_gantt',
        'sale',
        'vieterp_mrp_base',
        'mrp',
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/data.xml',
        'views/project_task_views.xml',
        'views/sale_order_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}