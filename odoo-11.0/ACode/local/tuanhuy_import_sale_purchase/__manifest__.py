# -*- coding: utf-8 -*-
{
    'name': "tuanhuy_import_sale_purchase",

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
    'depends': ['base','sales_team','purchase','barcode_printout','stock','tuanhuy_product'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/import_purchase_order.xml',
        'views/import_sale_order_view.xml',
        'views/import_warning_view.xml',
        'views/import_product_view.xml',
        'views/stock_inventory_view.xml',
        'views/import_cong_no_view.xml',
        'views/import_sale_group.xml',
        'views/check_sale_purchase.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}