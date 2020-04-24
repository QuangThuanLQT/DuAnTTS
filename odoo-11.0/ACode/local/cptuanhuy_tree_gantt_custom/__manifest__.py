# -*- coding: utf-8 -*-
{
    'name': "cptuanhuy_tree_gantt_custom",

    'summary': """
        cptuanhuy_tree_gantt_custom
    """,

    'description': """
        custom tree_gantt cptuanhuy
    """,
    'author': "VietERP / Loc",
    'website': "http://www.vieterp.net",
    'category': 'VietERP',
    'version': '1.0',
    'depends': [
        'web',
        'web_tree_gantt',
        'cptuanhuy_project'
    ],
    'data': [
        'views/register.xml',
    ],
}