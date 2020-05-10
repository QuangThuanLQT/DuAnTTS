# -*- coding: utf-8 -*-
{
    'name': "tuanhuy_sale_puchase_total",
    'summary': """
        tuanhuy_sale_puchase_total
    """,
    'description': """
        tuanhuy_sale_puchase_total
    """,
    'author': "VietERP / Quy",
    'website': "http://www.vieterp.net",
    'category': 'VietERP',
    'version': '1.0',
    # any module necessary for this one to work correctly
    'depends': [
        'sale_discount_total',
        'tuanhuy_purchase_discount_total'
    ],
    # always loaded
    'data': [
        'views/sale_order_view.xml',
        'views/purchase_order_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}