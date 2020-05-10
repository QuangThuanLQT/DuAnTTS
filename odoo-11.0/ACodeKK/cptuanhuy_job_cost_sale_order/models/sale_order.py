# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime


class sale_order_inherit(models.Model):
    _inherit = 'sale.order'

    job_costing_id = fields.Many2one('job.costing', 'Báo giá')

    def update_sequence_number_next_actual(self):
        sequences = self.env['ir.sequence'].search([('code', 'in', ['cp.sale.order.bh', 'cp.sale.order'])])
        for sequence in sequences:
            sequence.number_next_actual = 1

    @api.model
    def create(self, values):
        record = super(sale_order_inherit, self).create(values)
        if record.team_id and record.team_id.sequence_id and record.team_id.sequence_id.code:
            so_number = self.env['ir.sequence'].next_by_code(record.team_id.sequence_id.code)
        else:
            so_number = self.env['ir.sequence'].next_by_code('cp.sale.order')
        record.name = so_number
        return record

    @api.onchange('contract_id')
    def onchange_contract_id(self):
        if self.contract_id:
            return {
                'domain': {
                    'job_costing_id': [('id', 'in', self.contract_id.job_costing_ids.ids)]
                }
            }
        else:
            return {
                'domain': {
                    'job_costing_id': [('id', 'in', self.env['job.costing'].search([]).ids)]
                }
            }

    def get_so_line(self,job_costing_ids,qty):
        line_list = []
        for job_costing_id in job_costing_ids:
            for job_quotaion_cost_id in job_costing_id.job_quotaion_cost_ids:
                product_id = job_quotaion_cost_id.job_quotaion_id.product_id.product_variant_id if job_quotaion_cost_id.job_quotaion_id.product_id else False
                analytic_tag_ids = job_quotaion_cost_id.job_quotaion_id.type.account_analytic_tag_ids
                if product_id:
                    line_list.append({
                        'product_id': product_id.id,
                        'product_uom': product_id.uom_id.id,
                        'product_uom_qty': qty * job_quotaion_cost_id.quantity,
                        'price_unit': job_quotaion_cost_id.total_cost / job_quotaion_cost_id.quantity,
                        'name' : product_id.name,
                        'analytic_tag_ids' : [(6,0,analytic_tag_ids.ids)]
                    })
            product_id = self.env['product.product'].search([('default_code', '=', job_costing_id.number)])
            if product_id:
                analytic_tag_ids = self.env.ref('cptuanhuy_project.account_analytic_tag_thuong_mai')
                line_list.append({
                        'product_id': product_id.id,
                        'product_uom': product_id.uom_id.id,
                        'product_uom_qty': qty,
                        'price_unit': product_id.list_price,
                        'name': product_id.name,
                        'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)]
                    })
            for child_job_costing_id in job_costing_id.child_job_costing_ids:
                line_list += self.get_so_line(child_job_costing_id.child_job_costing_id,qty * child_job_costing_id.quantity)
        return line_list

    @api.onchange('job_costing_id')
    def onchange_job_costing_id(self):
        if self.job_costing_id:
            self.sale_project_id = self.job_costing_id.project_id
            self.contract_id     = self.job_costing_id.analytic_id
            line_list            = self.get_so_line(self.job_costing_id,1)
            self.order_line.write({
                'active' : False
            })
            self.order_line = None
            for line in line_list:
                so_line = self.order_line.new({
                    'product_id': line.get('product_id',False),
                    'product_uom': line.get('product_uom',False),
                    'product_uom_qty': line.get('product_uom_qty',False),
                    'price_unit': line.get('price_unit',False),
                    'name' : line.get('name',False),
                    'analytic_tag_ids' : line.get('analytic_tag_ids',False),
                })
                so_line.onchange_product_for_ck()
                self.order_line += so_line