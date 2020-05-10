# -*- coding: utf-8 -*-

from odoo import models, fields, api,_

class project_task_type(models.Model):
    _inherit = 'project.task.type'

    stage_start = fields.Boolean(string="Trạng thái bắt đầu")
    stage_end = fields.Boolean(string="Trạng thái kết thúc")

    @api.onchange('stage_start')
    def onchange_stage_start(self):
        if self.stage_start:
            self.stage_end

    @api.onchange('stage_end')
    def onchange_stage_end(self):
        if self.stage_end:
            self.stage_start