# -*- coding: utf-8 -*-
{
    'name': "modifier_product",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com
    """,

    'description': """
        Long description of module's purpose
    """,

    'author': "VietERP",
    'website': "http://www.vieterp.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'purchase',
        'stock',
        'barcode_printout',
        'tuanhuy_check_report_file',
        'sale',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/vendors.xml',
        'views/product_vendor.xml',
        'views/product_vendor_file.xml',
        'views/product_template_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}