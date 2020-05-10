# -*- coding: utf-8 -*-
{
    "name": "Purchase Request Procurement",
    "author": "HashMicro/Axcensa",
    "version": "10.0.1.0",
    "website": "www.hashmicro.com",
    "category": "Purchase Management",
    "depends": ["purchase_request", "procurement"],
    "data": [
        "views/product_view.xml",
        "views/procurement_view.xml",
    ],
    'demo': [],
    'test': [
        "test/purchase_request_from_procurement.yml",
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
}