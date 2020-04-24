# -*- coding: utf-8 -*-
{
    'name': "prinizi_sale_order",

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
        'tuanhuy_sale',
        'sale_barcode',
        'tts_modifier_sale',
        'prinizi_sale_config_product_print',
        'prinizi_sale_product_print',
        'rowno_in_tree',
        'prinizi_sales_config_print_attribute',
        'tts_modifier_sale_return',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/thong_tin_its_image_view.xml',
        'views/sale_order_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
}