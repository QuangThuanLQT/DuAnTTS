# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
import json


class update_price_job_costing(models.Model):
    _name = 'update.price.job.costing'

    product_id = fields.Many2one('product.product',readonly=True,string="Sản phẩm")
    price_ihr = fields.Float(string="Chi phí / Đơn vị")
    labor_cost = fields.Float(string="Đơn giá nhân công")
    move_cost = fields.Float(string="Máy Thi Công Vận Chuyển")
    manager_cost = fields.Float(string="Quản Lý Giám Sát TC")
    discount = fields.Float(string="Chiết khấu")
    price_discount = fields.Float(string="Giá trực tiếp")
    verage_cost = fields.Float(string="Chi phí dự kiến")
    job_costing_ids = fields.Many2many('job.costing',string="Báo giá cần cập nhật")
    project_ids = fields.Many2many('project.project',string="Dự án cần cập nhật")
    type = fields.Selection([
        ('job_costing' ,'Báo giá'),
        ('project', 'Dự án')
    ],string='Cập nhật theo',default="job_costing")
    job_costing_line_id = fields.Many2one('job.cost.line')
    tax = fields.Integer(string="Thuế")
    job_costing_id = fields.Many2one('job.costing', string="Báo giá")
    job_quotaion_id = fields.Many2one('job.quotaion', string="Định mức")

    @api.onchange('tax')
    def onchange_tax(self):
        if self.tax not in (0, 5, 10):
            self.tax = 0

    @api.model
    def default_get(self, fields):
        res = super(update_price_job_costing, self).default_get(fields)
        if 'job_costing_line' in self._context and self._context.get('job_costing_line', False):
            job_costing_line_id = self.env['job.cost.line'].browse(self._context.get('job_costing_line', False))
            res['product_id'] = job_costing_line_id.product_id.id
            res['price_ihr'] = job_costing_line_id.price_ihr
            res['labor_cost'] = job_costing_line_id.labor_cost
            res['move_cost'] = job_costing_line_id.move_cost
            res['manager_cost'] = job_costing_line_id.manager_cost
            res['discount'] = job_costing_line_id.discount
            res['price_discount'] = job_costing_line_id.price_discount
            res['verage_cost'] = job_costing_line_id.verage_cost
            res['job_costing_line_id'] = job_costing_line_id.id
            res['tax'] = job_costing_line_id.tax
        if 'job_costing_id' in self._context and self._context.get('job_costing_id', False):
            res['job_costing_id'] = self._context.get('job_costing_id', False)
        if 'job_quotaion_id' in self._context and self._context.get('job_quotaion_id', False):
            res['job_quotaion_id'] = self._context.get('job_quotaion_id', False)
        return res

    @api.multi
    def action_update_job_costing(self):
        for record in self:
            data_write = {
                'price_ihr': record.price_ihr,
                'labor_cost': record.labor_cost,
                'move_cost': record.move_cost,
                'manager_cost': record.manager_cost,
                'discount': record.discount,
                'price_discount': record.price_discount,
                'verage_cost': record.verage_cost,
                'tax' : record.tax,
            }
            jcl_update_ids = self.env['job.cost.line']
            if record.type == 'job_costing':
                jcl_update_ids = self.env['job.cost.line'].search(
                    [('product_id','=',record.product_id.id),('direct_id','in',record.job_costing_ids.ids)])
            else:
                job_costing_ids = record.project_ids.mapped('job_cost_ids')
                jcl_update_ids = self.env['job.cost.line'].search(
                    [('product_id', '=', record.product_id.id), ('direct_id', 'in', job_costing_ids.ids)])
            if jcl_update_ids:
                for line in jcl_update_ids:
                    line.write(data_write)
                    line.onchange_price_ihr()

    @api.multi
    def action_update_job_costing_1(self):
        for record in self:
            for line in record.job_costing_id.job_cost_line_ids:
                data_write = {
                    'price_ihr': line.price_ihr,
                    'labor_cost': line.labor_cost,
                    'move_cost': line.move_cost,
                    'manager_cost': line.manager_cost,
                    'discount': line.discount,
                    'price_discount': line.price_discount,
                    'verage_cost': line.verage_cost,
                    'tax': line.tax,
                }
                jcl_update_ids = self.env['job.cost.line']
                if record.type == 'job_costing':
                    jcl_update_ids = self.env['job.cost.line'].search(
                        [('product_id', '=', line.product_id.id), ('direct_id', 'in', record.job_costing_ids.ids)])
                else:
                    job_costing_ids = record.project_ids.mapped('job_cost_ids')
                    jcl_update_ids = self.env['job.cost.line'].search(
                        [('product_id', '=', line.product_id.id), ('direct_id', 'in', job_costing_ids.ids)])
                if jcl_update_ids:
                    for jcl_line in jcl_update_ids:
                        jcl_line.write(data_write)
                        jcl_line.onchange_price_ihr()

    @api.multi
    def action_update_job_costing_base_jq(self):
        for record in self:
            for line in record.job_costing_id.job_cost_line_ids.filtered(lambda l: l.job_quotation_id == record.job_quotaion_id):
                data_write = {
                    'price_ihr': line.price_ihr,
                    'labor_cost': line.labor_cost,
                    'move_cost': line.move_cost,
                    'manager_cost': line.manager_cost,
                    'discount': line.discount,
                    'price_discount': line.price_discount,
                    'verage_cost': line.verage_cost,
                    'tax': line.tax,
                }
                jcl_update_ids = self.env['job.cost.line']
                if record.type == 'job_costing':
                    jcl_update_ids = self.env['job.cost.line'].search(
                        [('product_id', '=', line.product_id.id), ('direct_id', 'in', record.job_costing_ids.ids), ('job_quotation_id','=',record.job_quotaion_id.id)])
                else:
                    job_costing_ids = record.project_ids.mapped('job_cost_ids')
                    jcl_update_ids = self.env['job.cost.line'].search(
                        [('product_id', '=', line.product_id.id), ('direct_id', 'in', job_costing_ids.ids), ('job_quotation_id','=',record.job_quotaion_id.id)])
                if jcl_update_ids:
                    for jcl_line in jcl_update_ids:
                        jcl_line.write(data_write)
                        jcl_line.onchange_price_ihr()
