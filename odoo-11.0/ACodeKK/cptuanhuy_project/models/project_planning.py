# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT


class project_planning(models.Model):
    _name = 'project.planning'

    project_id = fields.Many2one('project.project', string="Project")
    # task_id               = fields.Many2one('project.task',"Task")
    start_forecast = fields.Integer(string="(Dự kiến)Bắt đầu triển khai")
    doing_forecast = fields.Integer(string="(Dự kiến)Thời gian triển khai")
    name = fields.Char('Hạng mục')
    start_actual = fields.Integer("(Thực tế)Bắt đầu triển khai")
    doing_actual = fields.Integer("(Thực tế)Thời gian triển khai")
    progress = fields.Float("Tiến Độ Triển Khai")
    date_start = fields.Datetime("Ngày bắt đầu", compute='get_start_end_date')
    date_end = fields.Datetime("Ngày kết thúc", compute='get_start_end_date')
    status = fields.Char('Status', compute='get_start_end_date')

    @api.depends('project_id')
    def get_start_end_date(self):
        for record in self:
            if record.project_id:
                if record.project_id.date_start and record.project_id.start_date_unit:
                    start_date = datetime.strptime(record.project_id.date_start, DEFAULT_SERVER_DATE_FORMAT)
                    count = 1 if record.project_id.start_date_unit == 'daily' else 7
                    start_plan = start_date + relativedelta(days=(record.start_forecast * count - 1 * count))
                    record.date_start = start_plan
                    end_plan = start_date + relativedelta(
                        days=(record.start_forecast * count - 1 * count)) + relativedelta(
                        days=(record.doing_forecast * count - 1 * count))
                    record.date_end = end_plan
                    today = datetime.today().date()
                    if today > end_plan.date() and record.progress < 100:
                        record.status = 'Trễ'
                    else:
                        record.status = 'Không trễ'

    # @api.onchange('date_start')
    # def change_start_week_number(self):
    #     if self.date_start:
    #         date_start = datetime.strptime(self.date_start,DEFAULT_SERVER_DATETIME_FORMAT)
    #         self.start_forecast = date_start.isocalendar()[1]
    #
    # @api.onchange('date_end')
    # def change_done_week_number(self):
    #     if self.date_end:
    #         date_end = datetime.strptime(self.date_end, DEFAULT_SERVER_DATETIME_FORMAT)
    #         self.doing_forecast = date_end.isocalendar()[1]
