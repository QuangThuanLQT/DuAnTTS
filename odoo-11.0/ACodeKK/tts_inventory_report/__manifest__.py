# -*- coding: utf-8 -*-
{
    'name': "tts_inventory_report",

    'summary': """
        tts_inventory_report
    """,

    'description': """
        tts_inventory_report
    """,

    'author': "VietERP / Vu",
    'website': "http://www.vieterp.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'VietERP',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': [
        'stock',
        'tuanhuy_stock',
        'tts_internal_transfer',
        'tts_modifier_purchase',
        'stock_report',
        'tts_modifier_product',
        'tts_modifier_sale_return'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/stock_report_popup.xml',
        'views/stock_inventory_detail.xml',
        'views/template.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
