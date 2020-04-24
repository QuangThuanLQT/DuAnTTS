# -*- coding: utf-8 -*-
{
    'name': "tts_internal_transfer",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Vieterp /Luc",
    'website': "http://www.vieterp.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['stock', 'search_by_range', 'tuanhuy_stock', 'tts_modifier_inventory', 'purchase'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/internal_transfer_view.xml',
        'views/receipt_history.xml',
        'views/income_delivery.xml',
        'views/exported_history.xml',
        'views/data.xml',
    ],
    # only loaded in demonstration mode
    'qweb': [
        'static/src/xml/*.xml',
    ],
}
