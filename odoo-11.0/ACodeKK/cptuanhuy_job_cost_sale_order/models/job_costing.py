# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import UserError

class job_costing_inherit(models.Model):
    _inherit = 'job.costing'

    check_show_button = fields.Boolean(compute='get_check_show_button')
    sale_order_id = fields.Many2one('sale.order')

    @api.multi
    def get_check_show_button(self):
        for record in self:
            if record.state == 'draft':
                record.check_show_button = True
            else:
                if record.project_id.analytic_account_id.project_manager_id and record.project_id.analytic_account_id.project_manager_id.id == self._uid:
                    if record.project_id.analytic_account_id.state != 'draft':
                        record.check_show_button = False
                    else:
                        record.check_show_button = True
                else:
                    record.check_show_button = True

    @api.multi
    def create_sale_order(self):
        for record in self:
            if record.sale_order_id:
                if record.sale_order_id.state == 'draft':
                    for job_quotation in record.job_quotaion_cost_ids:
                        if job_quotation.job_quotaion_id.state == 'draft':
                            raise UserError("Định mức '%s' cần xác nhận." % (job_quotation.job_quotaion_id.name))
                    record.sale_order_id.write({
                        'partner_id': record.partner_id.id,
                        'partner_invoice_id': record.partner_id.id,
                        'partner_shipping_id': record.partner_id.id,
                    })
                    record.sale_order_id.order_line.unlink()
                    record.sale_order_id.onchange_job_costing_id()

                return {'type': 'ir.actions.act_window',
                        'res_model': 'sale.order',
                        'view_mode': 'form',
                        'res_id': record.sale_order_id.id,
                        'target': 'current'}
            else:
                for job_quotation in record.job_quotaion_cost_ids:
                    if job_quotation.job_quotaion_id.state == 'draft':
                        raise UserError("Định mức '%s' cần xác nhận." % (job_quotation.job_quotaion_id.name))
                sale_order_id = self.env['sale.order'].create({
                    'partner_id': record.partner_id.id,
                    'partner_invoice_id': record.partner_id.id,
                    'partner_shipping_id': record.partner_id.id,
                    'sale_project_id': record.project_id.id,
                    'job_costing_id': record.id,
                    'contract_id': record.project_id.analytic_account_id.id,
                    'project_id': record.project_id.analytic_account_id.id,
                    'sale_from_project': True,
                })
                sale_order_id.onchange_job_costing_id()

                record.sale_order_id = sale_order_id
                return {'type': 'ir.actions.act_window',
                        'res_model': 'sale.order',
                        'view_mode': 'form',
                        'res_id': sale_order_id.id,
                        'target': 'current'}


    # @api.multi
    # def create_sale_order(self):
    #     for record in self:
    #         product_id = self.env['product.product'].search([('default_code', '=', record.number)])
    #         if product_id and record.jobcost_total != 0 and product_id.list_price != record.jobcost_total:
    #             product_id.list_price = record.jobcost_total
    #         sale_order_id = self.env['sale.order'].search([('job_costing_id','=',record.id),('state','!=','cancel')],limit=1)
    #         if sale_order_id:
    #             for line in sale_order_id.order_line:
    #                 if line.product_id == product_id and line.product_id != record.jobcost_total:
    #                     line.price_unit = record.jobcost_total
    #                     line.price_unit_sub = record.jobcost_total
    #                     sale_order_id.button_dummy()
    #             return {'type': 'ir.actions.act_window',
    #                     'res_model': 'sale.order',
    #                     'view_mode': 'form',
    #                     'res_id': sale_order_id.id,
    #                     'target': 'current'}
    #         else:
    #             sale_order_id = self.env['sale.order'].create({
    #                 'partner_id': record.partner_id.id,
    #                 'partner_invoice_id': record.partner_id.id,
    #                 'partner_shipping_id': record.partner_id.id,
    #                 'sale_project_id' : record.project_id.id,
    #                 'job_costing_id' : record.id,
    #                 'contract_id' : record.project_id.analytic_account_id.id,
    #                 'project_id' : record.project_id.analytic_account_id.id,
    #                 'sale_from_project' : True,
    #             })
    #             # product_id = self.env['product.product'].search([('default_code','=',self.number)])
    #             if not product_id:
    #                 product_id = self.env['product.product'].create({
    #                     'name' : record.name,
    #                     'purchase_ok' : False,
    #                     'route_ids' : [(6,0,[self.env.ref('mrp.route_warehouse0_manufacture').id,self.env.ref('stock.route_warehouse0_mto').id])],
    #                     'default_code' : record.number,
    #                     'list_price' : record.jobcost_total,
    #                 })
    #             sale_order_id.order_line += sale_order_id.order_line.new({
    #                 'analytic_tag_ids' : [(6,0,self.env.ref('cptuanhuy_project_contract.account_analytic_tag_thuong_mai').ids)],
    #                 'product_id' : product_id.id,
    #                 'price_unit' : record.jobcost_total,
    #                 'price_unit_sub': record.jobcost_total,
    #             })
    #
    #             # Create BOM
    #             # mrp_bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', product_id.product_tmpl_id.id)])
    #             # if not mrp_bom:
    #             #     mrp_bom = self.env['mrp.bom'].create({
    #             #         'product_tmpl_id': product_id.product_tmpl_id.id,
    #             #     })
    #             #     for line in record.job_cost_line_ids:
    #             #         mrp_bom.bom_line_ids += mrp_bom.bom_line_ids.new({
    #             #             'product_id': line.product_id.id,
    #             #             'product_qty': line.product_qty
    #             #         })
    #
    #
    #             return {'type': 'ir.actions.act_window',
    #                     'res_model': 'sale.order',
    #                     'view_mode': 'form',
    #                     'res_id': sale_order_id.id,
    #                     'target': 'current'}

class project_project_inherit(models.Model):
    _inherit = 'project.project'

    sale_order_count = fields.Integer(compute="_get_sale_order")

    def _get_sale_order(self):
        for rec in self:
            sale_order_ids = self.env['sale.order'].search([('sale_project_id', '=', rec.id)])
            rec.sale_order_count = len(sale_order_ids)

    @api.multi
    def action_open_sale_order(self):
        action = self.env.ref('sale.action_orders').read()[0]
        sale_order_ids = self.env['sale.order'].search([('sale_project_id', '=', self.id)])
        action['domain'] = [('id', 'in', sale_order_ids.ids)]
        action['context'] = {'contract_id': self.id, 'partner_id': self.partner_id.id, 'sale_from_project': True}
        return action