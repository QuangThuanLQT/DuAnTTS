# -*- coding: utf-8 -*-
{
    'name': "sale_customers",

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
    'depends': ['base', 'sale', 'fetchmail', 'account', 'stock'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/sale_customers.xml',
        'views/PK_DanhMuc_MoHinh.xml',
        'views/MaKH_noibo.xml',
        'views/PrintAttribute.xml',
        'views/PrintAttributeValue.xml',
        'views/ly_do_tra_hang.xml',
        'views/attributes.xml',
        'views/attachment.xml',
        'views/Menu_dia_chi.xml',
        'views/Thong_tin_dia_chi.xml',
        'views/kiem_tra_cong_no.xml',
        'views/kiem_tra_ton_kho.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
