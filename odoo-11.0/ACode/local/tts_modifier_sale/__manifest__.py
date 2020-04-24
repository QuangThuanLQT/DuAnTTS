# -*- coding: utf-8 -*-
{
    'name': "tts_modifier_sale",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "VietERP/Luc",
    'website': "http://www.vieterp.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['sale', 'base', 'product_multi_select_sale',
                'tuanhuy_sale', 'search_by_range',
                'tuanhuy_cancel_function', 'tts_transport_delivery',
                'product_pack', 'sale_barcode', 'mail'
                ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/sale_order_view.xml',
        'views/sale_report.xml',
        'views/setting_queue_server_view.xml',
        'views/sale_config_view.xml'
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],

}
