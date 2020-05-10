# -*- coding: utf-8 -*-
{
    'name': "tts_modifier_sale_return",

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
    'depends': ['sale', 'sales_team', 'sale_purchase_returns', 'tts_modifier_sale', 'tts_modifier_inventory',
                'tts_internal_transfer'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/sale_order_view.xml',
        'views/sale_cancel_view.xml',
        'views/template.xml',
    ],
    # only loaded in demonstration mode
}
