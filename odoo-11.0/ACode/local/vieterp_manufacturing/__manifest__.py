# -*- coding: utf-8 -*-
{
    'name': "vieterp_manufacturing",

    'summary': """
        Manufacturing Module
    """,

    'description': """
        Manufacturing Module
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
        'sale',
        'mrp',
        'vieterp_bom_approval',
        'vieterp_order',
        'vieterp_mrp_base',
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/data.xml',
        'views/sale_views.xml',
        'views/mrp_production_views.xml',
        'views/mrp_workorder_views.xml',
        'views/mail_templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}