# -*- coding: utf-8 -*-
{
    'name': "todo",

    'summary': """
        todo - react js
    """,

    'description': """
        todo - react js
    """,

    'author': "VietERP / Sang",
    'website': "http://www.vieterp.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
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
        'views/todo_templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}