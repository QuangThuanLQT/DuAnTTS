# -*- coding: utf-8 -*-
{
    'name': "Payment Follow-up Management",

    'summary': """
        Module to automate letters for unpaid invoices, with multi-level recalls.""",

    'description': """
Module to automate letters for unpaid invoices, with multi-level recalls.
=========================================================================

You can define your multiple levels of recall through the menu:
---------------------------------------------------------------
    Configuration / Follow-up / Follow-up Levels

Once it is defined, you can automatically print recalls every day through simply clicking on the menu:
------------------------------------------------------------------------------------------------------
    Payment Follow-Up / Send Email and letters

It will generate a PDF / send emails / set manual actions according to the the different levels
of recall defined. You can define different policies for different companies.

Note that if you want to check the follow-up level for a given partner/account entry, you can do from in the menu:
------------------------------------------------------------------------------------------------------------------
    Reporting / Accounting / **Follow-ups Analysis

    """,

    'author': "HashMicro / Vu",
    'website': "http://www.hashmicro.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Accounting & Finance',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': [
        'account_accountant',
        'mail',
        'sales_team',
        'sale',
    ],

    # always loaded
    'data': [
        'security/account_followup_security.xml',
        'security/ir.model.access.csv',
        'report/account_followup_report.xml',
        'data/account_followup_data.xml',
        'wizard/account_followup_print_view.xml',
        'views/account_followup_view.xml',
        'views/account_followup_customers.xml',
        'views/res_config_view.xml',
        'views/account_followup_reports.xml',
        'views/menu_product_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/account_followup_demo.xml',
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: