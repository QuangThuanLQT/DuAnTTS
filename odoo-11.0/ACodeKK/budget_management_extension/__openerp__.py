# -*- coding: utf-8 -*-
{
    "name": "Budget Management Extension",
    "category": 'Sale',
    'summary': 'Budget Management Extension',
    "description": """
        Budget Management Extension
    """,
    "sequence": 1,
    "author": u"VietERP / Sang",
    "website": u"www.vieterp.net",
    "version": '1.0',
    "depends": [
        'analytic',
        'hr_expense',
        'account_budget',
        'purchase',
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/account_budget_view_override.xml',
        'views/budget_extension_view.xml',
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
