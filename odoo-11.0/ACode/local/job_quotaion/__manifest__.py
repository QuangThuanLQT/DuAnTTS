# -*- coding: utf-8 -*-
{
    'name': "job_quotation",

    'summary': """
        job_quotation
    """,

    'description': """
        job_quotation
    """,

    'author': "VietERP / Luc",
    'website': "http://www.vieterp.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'VietERP',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'product',
        'odoo_job_costing_management',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/update_quotation_product_view.xml',
        'views/job_quotaion_view.xml',
        'views/product.xml',
        'views/multi_import_job_quotation_view.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}