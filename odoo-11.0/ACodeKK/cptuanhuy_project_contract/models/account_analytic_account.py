# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime

class account_analytic_account_inherit(models.Model):
    _inherit = 'account.analytic.account'

    contract_history        = fields.One2many('account.analytic.account.history', 'account_analytic_id', string="Lịch sử hợp đồng")
    account_guarantee_ids   = fields.Many2many('account.guarantee', compute="get_account_guarantee")
    account_guarantee_count = fields.Integer(compute="get_account_guarantee")
    job_costing_ids         = fields.Many2many('job.costing', compute="get_job_costing")
    project_id              = fields.Many2one('project.project',string='Dự án')
    sale_order_ids          = fields.Many2many('sale.order', string="Đơn bán hàng", compute="_get_sale_order")
    sale_order_count        = fields.Integer(compute="_get_sale_order")
    project_manager_id      = fields.Many2one('res.users', string="Quản lý dự án")
    user_email              = fields.Char(string="Email")
    user_phone              = fields.Char(string="Điện thoại")
    maintenance_ids         = fields.Many2many('maintenance.request', string='Phụ Lục')
    state                   = fields.Selection([
        ('draft', 'Soạn thảo'),
        ('approve', 'Xác nhận'),
        ('open', 'Thực thi'),
        ('done', 'Hoàn thành'),
        ('cancel', 'Huỷ'),
    ], 'Status', readonly=True, default='draft')
    check_payment = fields.Boolean(string="Có thanh toán")
    check_guarantee = fields.Boolean(string="Có bảo lãnh tạm ứng")

    @api.onchange('project_manager_id')
    def onchange_project_manager_id(self):
        if self.project_manager_id:
            self.user_email = self.project_manager_id.partner_id.email
            self.user_phone = self.project_manager_id.partner_id.mobile or self.project_manager_id.partner_id.phone

    @api.onchange('project_id')
    def onchange_project_id(self):
        if self.project_id:
            self.partner_id = self.project_id.partner_id

    def _get_sale_order(self):
        for rec in self:
            sale_order_ids = self.env['sale.order'].search([('contract_id', '=', rec.id)])
            rec.sale_order_ids = sale_order_ids
            rec.sale_order_count = len(sale_order_ids)

    @api.multi
    def action_open_sale_order(self):
        action = self.env.ref('sale.action_orders').read()[0]
        action['domain'] = [('id', 'in', self.sale_order_ids.ids)]
        # action['context'] = {'contract_id': self.id,'partner_id':self.partner_id.id,'sale_from_project':True}
        return action

    @api.multi
    def projects_action(self):
        projects = self.with_context(active_test=False).mapped('project_id')
        result = {
            "type": "ir.actions.act_window",
            "res_model": "project.project",
            "views": [[False, "tree"], [False, "form"]],
            "domain": [["id", "in", projects.ids]],
            "context": {"create": False},
            "name": "Projects",
        }
        if len(projects) == 1:
            result['views'] = [(False, "form")]
            result['res_id'] = projects.id
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

    def _compute_project_count(self):
        for account in self:
            account.project_count = len(account.with_context(active_test=False).project_id)

    def get_job_costing(self):
        for record in self:
            projects = record.with_context(active_test=False).mapped('project_ids')
            if projects:
                job_costing_ids = self.env['job.costing'].search([('project_id','in', projects.ids)])
                record.job_costing_ids = job_costing_ids

    @api.multi
    def action_approve(self):
        self.write({'state': 'approve'})

    @api.multi
    def action_open(self):
        self.write({'state': 'open'})

    @api.multi
    def action_done(self):
        self.write({'state': 'done'})

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})

    @api.multi
    def set_to_draft(self):
        self.write({'state': 'draft'})

    def get_account_guarantee(self):
        for record in self:
            account_guarantee_ids = self.env['account.guarantee'].search([('account_analytic_account_id','=',record.id)])
            record.account_guarantee_ids = account_guarantee_ids
            record.account_guarantee_count = len(account_guarantee_ids)

    @api.multi
    def action_open_account_guarantee(self):
        action = self.env.ref('account_guarantee.account_guarantee_action').read()[0]
        action['domain'] = [('id', 'in', self.account_guarantee_ids.ids)]
        action['context'] = {'account_analytic_account_id':self.id}
        return action

    @api.multi
    def write(self, vals):

        for record in self:
            description = ""
            date = datetime.now()
            history = []
            for val in vals:
                if val == 'amount_max':
                    key = vals.get(val, '')
                    old_data = record.mapped(val)[0] or ''
                    new_date = str(key) or 0
                    description_price = "<ul><li><p><strong>%s:</strong> %s -&gt; %s</p></li></ul>" % (
                        "Giá cố định", old_data, new_date)
                    history.append((0,0,{
                        'date': date,
                        'description': description_price,
                        'user_id': self._uid,
                    }))
                    continue
                if val in ('contract_history'):
                    continue
                key = vals.get(val,'')
                field = self.env['ir.model.fields'].search([('model', '=', record._name), ('name', '=', val)])
                old_data = ''
                new_date = ''
                if field.ttype not in ('many2one','many2many','one2many'):
                    old_data = record.mapped(val)[0] or ''
                    new_date = str(key) or ''
                elif field.ttype == 'many2one':
                    key = self.env[field.relation].browse(key)
                    old_data = record.mapped(val).display_name or ''
                    new_date = key.display_name or ''
                elif field.ttype == 'many2many':
                    try:
                        key = self.env[field.relation].browse(key[0][2])
                        old_data = ''
                        for name in record.mapped(val).mapped('display_name'):
                            old_data += name + ", "
                        old_data = old_data[:-2] or ''
                        new_date = ''
                        for name in key.mapped('display_name'):
                            new_date += name + ", "
                        new_date = new_date[:-2] or ''
                    except:
                        pass
                if old_data:
                    description += "<ul><li><p><strong>%s:</strong> %s -&gt; %s</p></li></ul>"%(field.field_description,old_data,new_date)
                else:
                    description += "<ul><li><p><strong>%s:</strong> %s</p></li></ul>" % (field.field_description, new_date)

            if description:
                history += [(0,0,{
                    'date' : date,
                    'description' : description,
                    'user_id' : self._uid,
                })]
            if history:
                vals.update({
                    'contract_history' : history,
                })
        return super(account_analytic_account_inherit, self).write(vals)

class account_analytic_account_history(models.Model):
    _name = 'account.analytic.account.history'

    date = fields.Datetime('Ngày thay đổi')
    name = fields.Char('Nội dung thay đổi')
    old_data = fields.Char(string="Nội dung cũ")
    new_date = fields.Char(string="Nội dung mới")
    user_id = fields.Many2one('res.users',string='Người thay đổi')
    description = fields.Html('Nội dung thay đổi')
    account_analytic_id = fields.Many2one('account.analytic.account')