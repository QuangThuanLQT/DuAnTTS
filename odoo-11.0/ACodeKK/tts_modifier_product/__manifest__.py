# -*- coding: utf-8 -*-
{
    'name': "tts_modifier_product",

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
        'product',
        'stock',
        'tuanhuy_product',
        'modifier_product',
        'tuanhuy_stock',
        'stock_account'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/product_product_view.xml',
        'views/product_supplierinfo_view.xml',
        'views/import_vendor_pricelist.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
}
