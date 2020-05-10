# -*- coding: utf-8 -*-
# Author: Red Lab.
# Copyright: Red Lab.

{
    'name': 'Project Task Templates',
    'images': ['images/main_screenshot.png'],
    'version': '1.1.0',
    'category': 'Project',
    'summary': 'project, task, templates, template, default',
    'author': 'Red Lab',
    'website': 'https://apps.odoo.com/apps/modules/browse?search=REDLAB',
    'price': 15.00,
    'currency': 'EUR',
    'depends': [
        'project'
    ],
    'data': [
        'views/project_task_template_view.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
        'demo/project_template_demo.xml',
    ],
}
