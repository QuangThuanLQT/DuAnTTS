# -*- coding: utf-8 -*-
{
    'name': "cptuanhuy sale report",

    'summary': """
        cptuanhuy sale report    
    """,

    'description': """
        cptuanhuy sale report
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
        'cptuanhuy_modifier_sale_purchase',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/sale_report_action.xml'
    ],
    # only loaded in demonstration mode
}