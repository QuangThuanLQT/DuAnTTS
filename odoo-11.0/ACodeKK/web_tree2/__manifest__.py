# -*- coding: utf-8 -*-
{
    'name': "web_tree2",

    'summary': """
        web_tree2
    """,

    'description': """
        web_tree2
    """,

    'author': "VietERP / Sang",
    'website': "http://www.vieterp.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'VietERP',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': [
        'web',
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/web_tree2_templates.xml',
    ],
    # only loaded in demonstration mode
    'qweb': [
        'static/src/xml/*.xml',
    ],
}