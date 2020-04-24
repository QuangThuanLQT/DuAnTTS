# -*- coding: utf-8 -*-
{
    'name': 'FEOSCO Base Module',
    'version': '1.1',
    'author': 'Feosco',
    'category': 'Feosco',
    'website': 'http://www.feosco.com',
    'description': """
        Feosco Base Module: This module contain all data, base function that used in feosco modules
    """,
    'author': 'Feosco',
    'website': 'http://www.openerp.com',
    'images': [
    ],
    'depends': [
        'base',
        'fetchmail',
    ],
    'data': [
         'security/res.groups.csv',
         'view/menu.xml',
         'view/master_data_view.xml',
         'view/res_partner_view.xml',
         'view/res_bank_view.xml',
         'view/res_company_view.xml',
         'view/city_view.xml',
         'view/district_view.xml',
         'view/ward_view.xml',
         # 'view/res_users_view.xml',
         'view/ir_attachment_view.xml',
         'security/ir.model.access.csv',
         # 'security/ir_rule.xml',
        'view/templates.xml',
         'data/data.xml',
    ],
}
