# -*- coding: utf-8 -*-
{
    'name': "tuanhuy_gia_von",

    'summary': """
        tuanhuy_gia_von
    """,

    'description': """
        tuanhuy_gia_von
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
        'stock'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/tinh_gia_von.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}