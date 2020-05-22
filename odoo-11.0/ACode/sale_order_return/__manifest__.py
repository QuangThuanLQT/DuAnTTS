# -*- coding: utf-8 -*-
{
    'name': "sale_order_return",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/sale_order_return.xml',
        'views/thong_tin_its_image.xml',
        'views/thong_tin_khac.xml',
        'views/nhat_ky_lich_su.xml',
        'views/MaDonTra.xml',
        'report/sale_return_report.xml',
        'report/phieu_tra_hang.xml',
        'report/phieu_chi.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}