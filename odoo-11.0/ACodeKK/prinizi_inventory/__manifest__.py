# -*- coding: utf-8 -*-
{
    'name': "prinizi_inventory",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'stock',
        'tts_modifier_inventory',
        'prinizi_sale_order',
        'tts_internal_transfer',
        'tts_modifier_sale_return',
    ],
    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/stock_picking_view.xml',
        'views/pack_prinizi_printout.xml',
        'views/pick_prinizi_printout.xml',
        'views/stock_inventory.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}