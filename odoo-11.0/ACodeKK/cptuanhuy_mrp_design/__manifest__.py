# -*- coding: utf-8 -*-
{
    'name': "cptuanhuy_mrp_design",

    'summary': """
        cptuanhuy_mrp_design
    """,

    'description': """
        cptuanhuy_mrp_design
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
        'mrp',
        'mrp_workorder',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_design_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}