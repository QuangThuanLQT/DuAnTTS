# -*- coding: utf-8 -*-
{
    'name': "tts_sms_to_email",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "VietERP/Vu",
    'website': "http://www.vieterp.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'fetchmail', 'tts_account_voucher', 'tts_partner', 'account', 'tuanhuy_account_voucher'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/templates.xml',
        'views/account_journal.xml',
        'views/tts_email_inbox.xml',
        'views/account_voucher.xml',
        'views/tts_email_outbox.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
}
