# -*- coding: utf-8 -*-
{
    'name': "tts_modifier_vendor",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base',
                'purchase',
                'hr',
                'tuanhuy_modifier_partner',
                'tts_partner',
                'product',
                'account',
                ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/res_partner.xml',
        'views/liabilities_time.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}