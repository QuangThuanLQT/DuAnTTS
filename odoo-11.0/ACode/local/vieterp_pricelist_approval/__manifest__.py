# -*- coding: utf-8 -*-
{
    'name': "vieterp_pricelist_approval",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "VietERP / Sang",
    'website': "http://www.vieterp.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'sale',
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/product_pricelist_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}