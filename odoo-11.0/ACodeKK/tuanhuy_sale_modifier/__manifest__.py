
# -*- coding: utf-8 -*-
{
    'name': "tuanhuy_sale_modifier",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "VietERP Team",
    'website': "http://www.vieterp.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'VietERP',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': [
        'sale',
        'tuanhuy_product'
    ],

    # always loaded
    'data': [
        'views/product_date.xml',
        'security/ir.model.access.csv',
        'views/sale_report.xml',
        'views/sale_printout_excel.xml',
        'views/template.xml',
    ],
}