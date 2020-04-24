# -*- coding: utf-8 -*-
{
    'name': "vieterp_hello",

    'summary': """
        vieterp_hello
    """,

    'description': """
        vieterp_hello
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
        # 'views/views.xml',
        # 'views/templates.xml',
    ],
    'installable': True,
    'auto_install': True,
}