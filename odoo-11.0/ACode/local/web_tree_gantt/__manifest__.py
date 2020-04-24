# -*- coding: utf-8 -*-
{
    'name': "web_tree_gantt",

    'summary': """
        web_tree_gantt
    """,

    'description': """
        how to use:\n
        <field name="field_One2many" class="tree_gantt_view" start_date="date_start" end_date="date_end" progress="progress" column_label="Thời gian bắt đầu,Thời gian,Tiến trình" column_value="start_date,duration,progress">\n
        attributes mandatory:\n
        start_date(string),duration(code (example: item.doing_forecast - item.start_forecast)) or end_date(string)
        attributes option:\n
        column_label(string),column_value(string),progress(string),duration_unit(string),readonly(boolean),open(boolean)
    """,
    'author': "VietERP / Loc",
    'website': "http://www.vieterp.net",
    'category': 'VietERP',
    'version': '1.0',
    'depends': [
        'web',
    ],
    'data': [
        'views/register.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
}