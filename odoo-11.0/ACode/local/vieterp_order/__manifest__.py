# -*- coding: utf-8 -*-
{
    'name': "vieterp_order",

    'summary': """
        VietERP Order""",

    'description': """
        VietERP Order
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
        'vieterp_mrp_base',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizard/report_cost.xml',
        'views/sale_order_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}