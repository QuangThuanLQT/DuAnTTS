# -*- coding: utf-8 -*-
{
    'name': "cptuanhuy_modifier_sale_purchase",

    'summary': """
        Modifier sale purchase for cptuanhuy""",

    'description': """
        Long description of module's purpose
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
        'tuanhuy_sale',
        'tuanhuy_purchase',
        'cptuanhuy_stock',
        'cptuanhuy_job_cost_sale_order',
        'purchase_barcode',
        'purchase_request_to_rfq',
        'purchase_request_to_requisition'
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/sale_view.xml',
        'views/purchase_view.xml',
        'views/purchase_request.xml',
    ],
}