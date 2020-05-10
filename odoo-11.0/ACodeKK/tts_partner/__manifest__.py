# -*- coding: utf-8 -*-
{
    'name': "tts_partner",

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
    'depends': ['base', 'sale_purchase_returns', 'account', 'tuanhuy_sale','website_crm_partner_assign','tuanhuy_modifier_partner',
                'feosco_base','purchase'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/partner.xml',
        'views/templates.xml',
        'views/import_partner.xml',
        'views/loai_hinh_kinh_doanh_view.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
    'installable': True,
}
