# -*- coding: utf-8 -*-
{
    'name': 'Access Rights Group',
    'version': '1.0',
    'category': 'Access Rights',
    'sequence': 7,
    'summary': 'setup for access rights based on groups',
    'description': "This module includes setup for access rights based on groups during user creation",
    'website': 'http://www.axcensa.com/',
    'author': 'Axcensa',
    'depends': [
        'base','mail'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/access_rights_group_view.xml',
        'views/res_users_view.xml',
    ],
    'installable': True,
    'auto_install': True,
    'application': True,
}