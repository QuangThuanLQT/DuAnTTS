# -*- coding: utf-8 -*-
{
    'name': "vieterp_product",

    'summary': """
        vieterp_product
    """,

    'description': """
        vieterp_product
    """,

    'author': "VietERP / Huy",
    'website': "http://www.vieterp.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'VietERP',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'product',
        'stock'
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/product_product_views.xml',
        'views/product_templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
}