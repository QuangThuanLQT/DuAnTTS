# -*- coding: utf-8 -*-
{
    'name': "cptuanhuy_stock_account",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
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
        'stock',
        'account',
        'stock_account',
        'cptuanhuy_mrp',
        'product',
        'cptuanhuy_accounting',
        # 'simple_assemble_disassemble',
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/stock_move_views.xml',
        'views/product_template_views.xml',
        'views/product_product_views.xml',
        'views/stock_picking_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}