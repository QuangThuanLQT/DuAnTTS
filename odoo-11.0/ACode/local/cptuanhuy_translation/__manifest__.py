# -*- coding: utf-8 -*-
{
    'name': "CP tuanhuy Translation",

    'summary': """
        Translate CP tuanhuy""",

    'description': """
        Translate CP tuanhuy.
    """,

    'author': "VietERP / Luc",
    'website': "https://www.vieterp.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'VietERP',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
}
