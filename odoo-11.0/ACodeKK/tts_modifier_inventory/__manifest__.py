# -*- coding: utf-8 -*-
{
    'name': "tts_modifier_inventory",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Vieterp / Luc",
    'website': "http://www.vieterp.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'stock', 'tuanhuy_stock', 'product', 'tts_api', 'tts_modifier_product', 'delivery_modifier',
        'tuanhuy_cancel_function', 'sale_attachment', 'delivery_modifier'

    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/stock_picking_view.xml',
        'views/stock_picking_type.xml',
        'views/pick_printout.xml',
        'views/product_product_view.xml',
        'views/location_save_product_view.xml',
        'views/inventory_history_view.xml',
        'views/stock_inventory.xml',
        'views/template.xml',
        'views/scrap.xml',
        'views/package_size.xml',
        'views/stock_location.xml',
        'views/not_sellable_product.xml',
        'views/pack_printout.xml',
        'views/receipt_printout.xml',
        'views/stock_inventory_printout.xml',
        'views/stock_move.xml'
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
    # only loaded in demonstration mode
}
