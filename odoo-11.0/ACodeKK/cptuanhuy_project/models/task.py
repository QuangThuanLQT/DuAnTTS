# -*- coding: utf-8 -*-

from odoo import models, fields, api,_

class project_task_priority(models.Model):
    _name = 'project.task.priority'

    name = fields.Char('Tên', required=True)
    code = fields.Char('Mã')

class task_inherit(models.Model):
    _inherit = 'project.task'

    # state = fields.Selection([
    #     ('draft', 'Ý Tưởng'),
    #     ('required', 'Cần Làm'),
    #     ('working', 'Đang Làm'),
    #     ('checking', 'Kiểm Tra'),
    #     ('done', 'Hoàn Thành'),
    #     ('waiting', 'Chờ'),
    # ], 'Status', readonly=True, default='draft')
    @api.model
    def get_default_priority_id(self):
        priority_id = self.env['project.task.priority'].search([('name', '=', 'Vừa')], limit=1)
        return priority_id

    job_quotaion_count = fields.Integer(
        compute='_compute_job_quotaion_count'
    )
    doc_count = fields.Integer(compute='_compute_attached_docs_count', string="Number of documents attached")
    priority_id = fields.Many2one('project.task.priority', 'Priority', default=get_default_priority_id)
    next_task = fields.Many2one('project.task',string="Nhiệm vụ trước")

    contract_count = fields.Integer(string="Hợp đồng", compute="_get_contract_count")
    actual_date_start   = fields.Datetime('Ngày thực tế bắt đầu')
    actual_date_end     = fields.Datetime('Ngày thực tế kết thúc')

    def _get_contract_count(self):
        for record in self:
            contract_ids = record.project_id.analytic_account_id.filtered(lambda ct: ct.is_project == True)
            record.contract_count = len(contract_ids)

    @api.multi
    def action_open_contract(self):
        contract_ids = self.project_id.analytic_account_id.filtered(lambda ct: ct.is_project == True)
        action = self.env.ref('stable_account_analytic_analysis.action_account_analytic_overdue_all').read()[0]
        action['domain'] = [('id', 'in', contract_ids.ids)]
        return action

    @api.multi
    def write(self,vals):
        res = super(task_inherit, self).write(vals)
        if 'stage_id' in vals:
            for record in self:
                if record.stage_id and record.stage_id.stage_end and record.stage_id.stage_start:
                    continue
                if record.stage_id and record.stage_id.stage_end:
                    next_task_ids = self.env['project.task'].search([('next_task','=',record.id)])
                    if next_task_ids:
                        stage_start = self.env['project.task.type'].search([('stage_start', '=', True)]).filtered(
                            lambda ptt: record.project_id.id in ptt.project_ids.ids)
                        for next_task in next_task_ids:
                            next_task.stage_id = stage_start
        return res

    # @api.multi
    # @api.onchange('stage_id')
    # def _task_onchange_stage_id(self):
    #     a = 1
    #     if self.stage_id and self.stage_id.stage_end:
    #         # self.env['project.task'].search(
    #         #     [('project_id', '=', record.project_id.id), ('next_task', '=', record.id)])
    #         next_task = self.next_task
    #         stage_start = self.env['project.task.type'].search([('stage_start','=',True)]).filltered(lambda ptt: self.project_id.id in ptt.project_ids.ids)
    #         next_task.stage_id = stage_start

    @api.multi
    def _compute_job_quotaion_count(self):
        for record in self:
            job_cost = record.mapped('job_cost_ids')
            job_quotaion_ids = self.env['job.quotaion'].search(['|',('job_costing_id','in',job_cost.ids), ('project_id', '=', record.project_id.id)])
            record.job_quotaion_count = len(job_quotaion_ids)


    @api.multi
    def project_to_job_quotaion_action(self):
        job_cost = self.project_id.mapped('job_cost_ids')
        job_quotaion_ids = self.env['job.quotaion'].search(
            ['|',('job_costing_id', 'in', job_cost.ids), ('project_id', '=', self.project_id.id)])
        action = self.env.ref('job_quotaion.job_quotaion_action').read()[0]
        action['domain'] = [('id', 'in', job_quotaion_ids.ids)]
        return action

    @api.multi
    def _compute_jobcost_count(self):
        for record in self:
            jobcost = self.env['job.costing']
            job_cost_ids = record.project_id.mapped('job_cost_ids')
            for task in record:
                task.job_cost_count = jobcost.search_count([('id', 'in', job_cost_ids.ids)])

    @api.multi
    def task_to_jobcost_action(self):
        job_cost = self.project_id.mapped('job_cost_ids')
        action = self.env.ref('odoo_job_costing_management.action_job_costing').read()[0]
        action['domain'] = [('id', 'in', job_cost.ids)]
        action['context'] = {'default_task_id': self.id, 'default_project_id': self.project_id.id,
                             'default_analytic_id': self.project_id.analytic_account_id.id,
                             'default_user_id': self.user_id.id}
        return action

    @api.multi
    def attachment_tree_view(self):
        self.ensure_one()
        domain = [
            '|',
            '&', ('res_model', '=', 'project.project'), ('res_id', 'in', self.project_id.ids),
            '&', ('res_model', '=', 'project.task'), ('res_id', 'in', self.project_id.task_ids.ids)]
        return {
            'name': _('Attachments'),
            'domain': domain,
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                            Documents are attached to the tasks and issues of your project.</p><p>
                            Send messages or log internal notes with attachments to link
                            documents to your project.
                        </p>'''),
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d}" % (self._name, self.id)
        }

    def _compute_attached_docs_count(self):
        Attachment = self.env['ir.attachment']
        for task in self:
            task.doc_count = Attachment.search_count([
                '|',
                '&',
                ('res_model', '=', 'project.project'), ('res_id', '=', task.project_id.id),
                '&',
                ('res_model', '=', 'project.task'), ('res_id', 'in', task.project_id.task_ids.ids)
            ])