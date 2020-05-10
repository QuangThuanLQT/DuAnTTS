# -*- coding: utf-8 -*-
{
    'name': "tts_modifier_access_right",

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

    'depends': [
        'base', 'access_rights_group', 'stock', 'purchase', 'account',
        'tuanhuy_purchase', 'tuanhuy_sale_modifier', 'tuanhuy_product',
        'tts_modifier_inventory', 'tts_transport_delivery', 'tts_sms_to_email',
        'tts_modifier_accounting', 'tts_modifier_sale_return', 'account_asset',
        'delivery', 'tts_api', 'feosco_base', 'tts_inventory_report', 'tts_partner',
        'portal', 'tts_sms_to_email', 'tts_salary_sale_income', 'hr_recruitment',
        'hr_holidays', 'hr', 'hr_expense', 'hr_attendance', 'hr_payroll',
    ],

    # always loaded
    'data': [
        'security/data.xml',
        'security/ir.model.access.csv',
        'views/inventory_view.xml',
        'views/sale_order.xml',
        'views/templates.xml',
        'views/sms_inbox.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
