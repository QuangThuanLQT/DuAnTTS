# -*- coding: utf-8 -*-
{
    "name": "Purchase Request to Call for Bids",
    "author": "HashMicro/Axcensa",
    "version": "10.0.1.0",
    "website": "www.hashmicro.com",
    "category": "Purchase Management",
    "depends": [
        "purchase_request_procurement",
        "purchase_requisition",
        "purchase_request_to_rfq",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/purchase_request_line_make_purchase_requisition_view.xml",
        "views/purchase_request_view.xml",
        "views/purchase_requisition_view.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
}
