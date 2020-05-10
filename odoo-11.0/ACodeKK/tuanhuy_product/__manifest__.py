# -*- coding: utf-8 -*-
{
    'name': "tuanhuy_product",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "vieterp /Sang",
    'website': "http://www.vieterp.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','product','sales_team','stock','web','purchase', 'product_multi_barcode'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/product_group_sale.xml',
        'views/product_view.xml',
        'views/print_barcode_modifier.xml',
        'views/print_barcode_have_name.xml',
    ],

    'qweb': [
        'static/src/xml/*.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}