# -*- coding: utf-8 -*-
{
    "name": "Merge Purchase orders",
    "summary": "Merge Purchase orders that are confirmed, invoiced or delivered",
    "version": "1.0",
    "category": "Purchase Management",
    "website": "www.hashmicro.com",
    "author": "HashMicro / MP technolabs / Monali",
    "depends": [
        "purchase","purchase_requisition",
    ],
    "data": [
	"views/purchase_order.xml",
        "wizard/purchase_order_merge_view.xml",
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
