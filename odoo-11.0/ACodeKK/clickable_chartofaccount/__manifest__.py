# -*- coding: utf-8 -*-
{
    'name': 'Clickable Chartofaccount',
    'version': '1.0',
    'category': 'Accounting',
    'sequence': 16,
    'summary': 'Setup to view chart of accounts like in v8',
    'description': "This module includes setup which allows to view chart of accounts like in v8",
    'website': 'http://www.hashmicro.com/',
    'author': 'Hashmicro/Saravana Kumar',
    'depends': [
        'account'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/data_account_type.xml',
        'views/account_view.xml',
        'wizard/coa_wizard_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
