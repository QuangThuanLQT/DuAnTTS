# -*- coding: utf-8 -*-
{
    'name': "prinizi_merge_sale_order",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Vieterp/ Luc",
    'website': "http://www.vieterp.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'prinizi_sale_order',
        'tts_modifier_sale_return',
        'tts_modifier_inventory',
        'prinizi_sale_process',
        'prinizi_inventory'
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/stock_picking_view.xml',
        'views/sale_order_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}