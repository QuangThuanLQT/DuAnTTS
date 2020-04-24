# -*- coding: utf-8 -*-
{
    'name': "tts_transport_delivery",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Vieterp / Luc",
    'website': "http://www.vieterp.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['feosco_base', 'delivery'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/transport_route_view.xml',
        'views/transport_view.xml',
        'views/delivery_sope_view.xml',
        'views/partner.xml',
    ],
    # only loaded in demonstration mode
}
