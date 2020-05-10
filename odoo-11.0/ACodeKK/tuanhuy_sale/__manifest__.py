# -*- coding: utf-8 -*-
{
    'name': "tuanhuy_sale",

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
        'sale',
        'sale_discount_total',
        'account',
        'delivery',
        'stock_report',
        'modifier_product',
        'tuanhuy_product',
        'sale_purchase_returns',
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/data.xml',
        'views/sale_views.xml',
        'reports/sale_report.xml',
        'reports/sale_report_a4.xml',
        'views/sale_order_line.xml',
        'data/cron.xml',
        'reports/order_line_report.xml',
        'reports/so_ban_hang_report.xml',
        # 'views/sale_order_report.xml',
        'views/sale_order_filter.xml',
    ],
}