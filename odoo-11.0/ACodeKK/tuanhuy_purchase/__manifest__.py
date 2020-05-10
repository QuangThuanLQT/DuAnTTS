# -*- coding: utf-8 -*-
{
    'name': "tuanhuy_purchase",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
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
        'base',
        'purchase',
        'tuanhuy_check_report_file',
        'tuanhuy_purchase_discount_total',
        'modifier_product',
        'tuanhuy_product',
        'sale_purchase_returns',
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/purchase_views.xml',
        'views/purchase_order_line.xml',
        'reports/purchase_report.xml',
        'reports/purchase_report_a4.xml',
        'security/cron.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'qweb': [
        'static/src/xml/print_excel_template.xml',
    ],
}