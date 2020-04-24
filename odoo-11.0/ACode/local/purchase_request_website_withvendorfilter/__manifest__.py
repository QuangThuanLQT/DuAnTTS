# -*- coding: utf-8 -*-

{
    'name': 'Purchase Request Website',
    'author': 'HashMicro / Dhaval Suthar/ Purvi',
    'category': 'Website',
    'description': 'Purchase Products Online',
    'version': '1.0',
    'depends': ['purchase_request', 'website'],
    'data': [
        'security/ir.model.access.csv',
        'data/purchase_request_data.xml',
        'data/ordering_time_data.xml',
        'views/templates.xml',
        'views/purchase_request_template.xml',
        'views/ordering_time_view.xml',
    ],
    "installable": True,
    "auto_install": False,
}
