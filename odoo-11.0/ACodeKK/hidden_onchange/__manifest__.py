# -*- coding: utf-8 -*-
{
    'name': "hidden_onchange",

    'summary': """
        hidden_onchange
    """,

    'description': """
        hidden_onchange
    """,

    'author': "VietERP / Quy",
    'website': "http://www.vieterp.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'VietERP',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': [
        'purchase',
        'web'
    ],

    # always loaded
    'data': [
        'static/src/xml/template.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'qweb': [
        # 'static/src/xml/*.xml',
    ],
}
