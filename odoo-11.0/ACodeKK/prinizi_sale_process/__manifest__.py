# -*- coding: utf-8 -*-
{
    'name': "prinizi_sale_process",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "VietERP/Vu",
    'website': "http://www.vieterp.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base', 'stock', 'tts_modifier_sale', 'tts_internal_transfer',
        'prinizi_sale_order', 'prinizi_inventory', 'tts_modifier_sale_return',
        'tts_modifier_product',
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/data.xml',
        'views/stock_warehouse.xml',
        'views/stock_picking_type.xml',
        'views/stock_picking.xml',
        'views/sale_order.xml',
        'views/templates.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
}
