# -*- coding: utf-8 -*-
{
    'name': "cptuanhuy_import_product_child",

    'summary': """
        cptuanhuy_import_product_child""",

    'description': """
        cptuanhuy_import_product_child
    """,

    'author': "Vieterp /Quy",
    'website': "http://www.vieterp.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'product',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'job_quotaion'
    ],

    # always loaded
    'data': [
        'views/import_popup.xml',
        'security/ir.model.access.csv',

    ],
    # only loaded in demonstration mode
}