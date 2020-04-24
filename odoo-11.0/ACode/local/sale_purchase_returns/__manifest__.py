# -*- coding: utf-8 -*-
{
    'name': "sale_purchase_returns",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Vieterp / Luc",
    'website': "http://www.vieterp.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','purchase','sales_team','delivery','tuanhuy_sale_modifier'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'demo/demo.xml',
        'views/data.xml',
        'views/warning_return_picking_view.xml',
        'views/sale_purchase_return_view.xml',
        'views/sale_view.xml',
        'views/purchase_view.xml',
        'views/res_user_view.xml',
        'views/apply_by_pin_code_view.xml',
        'views/sale_config_setting_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable' : True,
}