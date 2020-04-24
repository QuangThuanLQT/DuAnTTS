# -*- coding: utf-8 -*-
{
    'name': "optimize_picking_update",

    'summary': """
        optimize_picking_update
    """,

    'description': """
        optimize_picking_update
    """,

    'author': "VietERP / Sang",
    'website': "http://www.vieterp.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'VietERP',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'stock',
        'stock_account',
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}