# -*- coding: utf-8 -*-
{
    'name': "cptuanhuy_mrp",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        - Tạo yêu cầu đề xuất nguyên vật liệu thêm, trả, hao hụt
    """,

    'author': "VietERP / Luc",
    'website': "http://www.vieterp.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'VietERP',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'mrp',
        'stock',
        'sale',
        'mrp_workorder',
        'cptuanhuy_stock',
        'procurement',
        'purchase',
        'l10n_vn',
    ],

    # always loaded
    'data': [
        'data/data.xml',
        'data/cron.xml',
        'security/ir.model.access.csv',
        'views/mrp_routing.xml',
        'views/mrp_workorder_view.xml',
        'views/stock_view.xml',
        'views/sale_order_view.xml',
        'views/stock_picking.xml',
        'views/mrp_production_views.xml',
    ],
    # only loaded in demonstration mode
}