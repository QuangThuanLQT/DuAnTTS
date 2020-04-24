# -*- coding: utf-8 -*-
{
    'name': "th_modifier_sale",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Vieterp /Hoa",
    'website': "http://www.vieterp.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'sale',
        'tuanhuy_sale'
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/botton_click_sale_older.xml'
    ],
    # only loaded in demonstration mode

}