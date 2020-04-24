# -*- coding: utf-8 -*-
{
    'name': "tts_modifier_purchase_return",

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
    'depends': ['base', 'stock', 'tts_modifier_purchase', 'sale_purchase_returns', 'tts_modifier_sale_return',
                'tts_internal_transfer'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_cancel_popup.xml',
        'views/purchase_order.xml',
        'views/stock_picking.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
