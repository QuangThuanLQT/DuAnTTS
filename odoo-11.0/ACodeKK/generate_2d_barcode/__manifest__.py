# -*- coding: utf-8 -*-
{
    'name': "generate_2d_barcode",

    'summary': """
            Use Product SKU, Lot Number and Best Before Date to generate a 2D barcode
        """,

    'description': """
        Use Product SKU, Lot Number and Best Before Date to generate a 2D barcode
        Generate the printout for the 2D barcode
    """,

    'author': "HashMicro/Sang",
    'website': "http://www.hashmicro.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'report', 'product'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/qr_code_label.xml',
        'views/product_template_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}