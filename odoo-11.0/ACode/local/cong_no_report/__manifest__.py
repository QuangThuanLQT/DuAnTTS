# -*- coding: utf-8 -*-
{
    'name': "cong_no_report",

    'summary': """
        cong_no_report
    """,

    'description': """
        cong_no_report
    """,

    'author': "VietERP / Sang",
    'website': "http://www.vieterp.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'account',
        'sale',
        'purchase',
        'l10n_vn',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'views/views.xml',
        'views/cong_no_report.xml',
        # 'views/cong_no_detail_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}