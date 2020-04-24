# -*- coding: utf-8 -*-
{
    'name': "vieterp_bom_approval",

    'summary': """
        VietERP BOM Approval
    """,

    'description': """
        VietERP BOM Approval
    """,

    'author': "VietERP / Sang",
    'website': "http://www.vieterp.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'mrp',
        'mail',
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/mrp_bom_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}