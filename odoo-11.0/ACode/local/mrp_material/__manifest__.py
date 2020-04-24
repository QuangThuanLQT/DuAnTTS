# -*- coding: utf-8 -*-
{
    'name': "mrp_material",

    'summary': """
        mrp_material
    """,

    'description': """
        mrp_material
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
        'mrp'
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/mrp_workorder_views.xml',
        'views/mrp_production_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}