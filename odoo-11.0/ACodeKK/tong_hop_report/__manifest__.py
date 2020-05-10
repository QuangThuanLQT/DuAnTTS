# -*- coding: utf-8 -*-
{
    'name': "tong_hop_report",

    'summary': """
        tong_hop_report
    """,

    'description': """
        tong_hop_report
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
        'cong_no_report',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/tong_hop_view.xml',
        # 'views/chi_tiet_report.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}