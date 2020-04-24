# -*- coding: utf-8 -*-
{
    "name": "Purchase Request",
    "author": "HashMicro/Axcensa",
    "version": "10.0.1.0",
    "website": "www.hashmicro.com",
    "category": "Purchase Management",
    "depends": ["purchase", "product"],
    "data": [
        "security/purchase_request.xml",
        "security/ir.model.access.csv",
        "data/purchase_request_sequence.xml",
        "data/purchase_request_data.xml",
        "views/purchase_request_view.xml",
        "reports/report_purchaserequests.xml",
        "views/purchase_request_report.xml",
    ],
    'demo': [
        "demo/purchase_request_demo.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
}
