# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).
{
    "name": "Hide Menu",
    "category": '',
    'summary': 'hide menu using menu item.',
    "description": """
        This modules adds the functionality of auto archiving lot which is inactive for 2 months once its 
        Qty turns to Zero. 
    """,
    "sequence": 1,
    "author": u"Hashmicro/Suraj Patel",
    "website": u"http://hashmicro.com/",
    "version": '1.2',
    "depends": ['base'],
    "data": [
        
        'views/hide_menu_view.xml',
    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": True,
}
