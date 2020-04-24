# -*- coding: utf-8 -*-

from odoo import models, fields, api

class sale_order(models.Model):
    _inherit = 'sale.order'

    @api.depends('task_ids')
    def _compute_task_count(self):
        for record in self:
            record.task_count = len(record.task_ids)

    @api.multi
    def action_view_tasks(self):
        tasks = self.mapped('task_ids')
        action = self.env.ref('project.act_project_project_2_project_task_all').read()[0]
        if len(tasks) >= 1:
            action['domain'] = [('id', 'in', tasks.ids)]
        else:
            action['views'] = [(self.env.ref('project.view_task_form2').id, 'form')]
        design_project = self.env.ref('vieterp_design.project_design')
        action['context'] = '{}'
        return action

    task_count = fields.Float(compute='_compute_task_count', string='Task Count', store=True)
    task_ids = fields.One2many('project.task', 'so_id', string='Tasks')

    @api.multi
    def action_create_task(self):
        task_obj = self.env['project.task']

        self.action_create_bom()

        for record in self:
            for line in record.order_line:
                task = task_obj.search([
                    ('so_line_id', '=', line.id),
                    ('so_id', '=', record.id),
                ], limit=1)

                if task:
                    continue

                task_data = {
                    'project_id': self.env.ref('vieterp_design.project_design').id,
                    'name': 'Design %s' %(line.bom_id and line.bom_id.code or line.name),
                    'so_id': record.id,
                    'so_line_id': line.id,
                    'documentation': '/',
                    'date_deadline': fields.Date.today(),
                    'partner_id': '',
                    'date_start': fields.Date.today(),
                    'bom_id': line.bom_id and line.bom_id.id or False,
                }
                task_obj.create(task_data)

        return self.action_view_tasks()