# -*- coding: utf-8 -*-
{
    'name': "telering_stock_pulsa",

    'summary': """
        telering_stock_pulsa""",

    'description': "maintain purchase and sell pulsa",

    'author': "VietERP / Viet",
    'website': "www.vieterp.net",
    'category': 'base',
    'version': '1.0',

    'depends': [
        'base',
        'product',
        'stock',
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/views.xml'
    ],
    'qweb': [
	# 'static/src/xml/*.xml',
    ],
}