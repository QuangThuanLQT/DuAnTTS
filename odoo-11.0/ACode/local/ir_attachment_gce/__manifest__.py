# -*- coding: utf-8 -*-
{
    'name': "ir_attachment_gce",

    'summary': """
        ir_attachment_gce
    """,

    'description': """
        ir_attachment_gce
    """,

    'author': "VietERP / Sang",
    'website': "http://www.vieterp.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'VietERP',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'ir_attachment_url',
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/cron.xml',
        'views/gce_config_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'auto_install': True,
}