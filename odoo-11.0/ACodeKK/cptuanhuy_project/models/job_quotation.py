# -*- coding: utf-8 -*-

from odoo import _, api, fields, models, SUPERUSER_ID, tools
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime
from odoo.exceptions import UserError
import json

class job_quotaion_type(models.Model):
    _name = 'job.quotaion.type'

    name                        = fields.Char('Tên')
    account_analytic_tag_ids    = fields.Many2many('account.analytic.tag',string='Doanh thu')
    cost_account_analytic_tag_ids = fields.Many2many('account.analytic.tag','job_quotaion_type_analytic_tag_rel', 'type_id', 'tag_id',string='Chi Phí')

class job_quotaion_inherit(models.Model):
    _inherit = 'job.quotaion'


    @api.model
    def default_manufaturing_type(self):
        try:
            if self.env.ref('cptuanhuy_project.job_quotaion_type_manufacturing'):
                return self.env.ref('cptuanhuy_project.job_quotaion_type_manufacturing').id
        except:
            return False

    type        = fields.Many2one('job.quotaion.type', string='Loại', default=default_manufaturing_type)
    product_id  = fields.Many2one('product.template', string='Sản phẩm')
    bom_id      = fields.Many2one('mrp.bom', string='Định mức sản xuất')

    @api.model
    def default_get(self, fields):
        res = super(job_quotaion_inherit, self).default_get(fields)
        if self._context and 'project_id' in self._context:
            res['project_id'] = self._context.get('project_id',False)
        return res

    @api.multi
    def action_confirm(self):
        for record in self:
            for line in record.line_ids:
                if not line.product_id:
                    raise UserError("Vui lòng chọn sản phẩm (STT: %s) cho định mức '%s'."%(line.sequence,record.name))
            product_data    = {
                'name'          : record.name,
                'default_code'  : record.job_quotaion_code,
                'list_price'    : sum(job_line.list_price*float(job_line.so_luong) for job_line in record.line_ids),
                'standard_price': sum(job_line.list_price*float(job_line.so_luong) for job_line in record.line_ids),
                'type'          : 'product',
            }
            so_type_sx_id = self.env.ref('cptuanhuy_project.job_quotaion_type_manufacturing')
            if record.type == so_type_sx_id:
                product_data.update({
                    'purchase_ok': False,
                    'route_ids': [(6, 0, [self.env.ref('mrp.route_warehouse0_manufacture').id,
                                          self.env.ref('stock.route_warehouse0_mto').id])],
                })
            else:
                product_data.update({
                        'purchase_ok' : True,
                        'route_ids': [(6, 0, [self.env.ref('purchase.route_warehouse0_buy').id])],
                    })
            if not record.product_id:
                product_id          = self.env['product.template'].create(product_data)
                record.product_id   = product_id
            else:
                record.product_id.write(product_data)
                product_id = record.product_id
            bom_data        = {
                'product_tmpl_id'   : product_id.id,
                'product_qty'       : 1,
                'product_uom_id'    : product_id.uom_id.id,
                'type'              : 'normal',
                'bom_line_ids'      : [(0,0,{
                        'product_id'    : line.product_id.id,
                        'product_qty'   : float(line.so_luong or 0),
                        'product_uom_id': line.product_uom.id or line.product_id.uom_id.id,
                        'sequence'      : line.sequence

                }) for line in record.line_ids]

            }
            if record.type and record.type.id != self.env.ref('cptuanhuy_project.job_quotaion_type_manufacturing').id:
                bom_data.update({'type':'phantom'})
            if not record.bom_id:
                bom_id          = self.env['mrp.bom'].create(bom_data)
                record.bom_id = bom_id
            else:
                record.bom_id.bom_line_ids.unlink()
                record.bom_id.write(bom_data)
                bom_id = record.bom_id

            # Tao bom rong cho tiep dau ngu trong sale setting
            bom_line_product_list = []
            ma_dau_setting  = self.env['ir.values'].get_default('sale.config.settings', 'ma_dau_sp_setting')
            if ma_dau_setting:
                ma_dau_ids  = self.env['tiep.ngu.dau'].browse(ma_dau_setting)
                for ma_dau_id in ma_dau_ids:
                    for line in record.line_ids:
                        if ma_dau_id.name in line.product_id.default_code:
                            domain = ['|', ('product_id', 'in', line.product_id.ids), '&', ('product_id', '=', False),('product_tmpl_id', 'in', line.product_id.mapped('product_tmpl_id').ids)]
                            exist_bom = self.env['mrp.bom'].search(domain)
                            if not exist_bom:
                                bom_line_product = self.env['mrp.bom'].create({
                                    'product_tmpl_id': line.product_id.product_tmpl_id.id,
                                    'product_qty': float(line.so_luong or 0),
                                    'product_uom_id': line.product_id.uom_id.id,
                                    'type': 'normal',
                                })
                                bom_line_product_list.append(bom_line_product.id)
                                line.product_id.product_tmpl_id.write({'route_ids':[(6, 0, [self.env.ref('mrp.route_warehouse0_manufacture').id,self.env.ref('stock.route_warehouse0_mto').id])]})

            record.state    = 'done'
            action          = self.env.ref('mrp.mrp_bom_form_action').read()[0]
            action['domain'] = [('id','in',bom_id.ids + bom_line_product_list)]
            return action
        #     job_cost_line = []
        #     job_labour_line = []
        #     job_overhead_line = []
        #     for line in record.line_ids:
        #         data = {}
        #         if line.product_id:
        #             data.update({
        #                 'date': datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT),
        #                 'product_id': line.product_id.id,
        #                 'description': line.product_id.name,
        #                 'product_qty': line.so_luong,
        #                 'uom_id': line.product_id.uom_id.id,
        #             })
        #             job_type_id = line.type
        #             if job_type_id:
        #                 data.update({
        #                     'job_type_id': job_type_id.id
        #                 })
        #                 if job_type_id.job_type == 'material':
        #                     data.update({
        #                         'job_type': 'material',
        #                     })
        #                     job_cost_line.append((0, 0, data))
        #                 elif job_type_id.job_type == 'labour':
        #                     data.update({
        #                         'job_type': 'labour',
        #                     })
        #                     job_labour_line.append((0, 0, data))
        #                 else:
        #                     data.update({
        #                         'job_type': 'overhead',
        #                     })
        #                     job_overhead_line.append((0, 0, data))
        #             else:
        #                 data.update({
        #                     'job_type': 'material',
        #                 })
        #                 job_cost_line.append((0, 0, data))
        #
        #     job_costing = {
        #         # 'project_id': record.project_id.id or False,
        #         # 'default_project_id': record.project_id.id or False,
        #         # 'analytic_id': record.project_id.analytic_account_id.id or False,
        #         # 'partner_id': record.partner_id.id,
        #         'default_start_date': datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT),
        #         'default_name': record.name or 'New',
        #         'default_job_cost_line_ids': job_cost_line,
        #         'default_job_labour_line_ids': job_labour_line,
        #         'default_job_overhead_line_ids': job_overhead_line,
        #     }
        #     # job_costing_id = self.env['job.costing'].create(job_costing)
        #     # for line in job_costing_id.job_cost_line_ids + job_costing_id.job_labour_line_ids + job_costing_id.job_overhead_line_ids:
        #     #     line.onchange_product_for_ck(record.partner_id.id)
        #     #     line.onchange_price_ihr()
        #     # record.job_costing_id = job_costing_id
        #     # record.state = 'done'
        # return {'type': 'ir.actions.act_window',
        #         'res_model': 'job.costing',
        #         'view_mode': 'form',
        #         # 'res_id': job_costing_id.id,
        #         'res_id': False,
        #         'context': job_costing,
        #         'target': 'current'}

    @api.multi
    def action_set_draft(self):
        for record in self:
            record.state = 'draft'


    @api.multi
    def quick_create_product(self):
        product_obj = self.env['product.template']
        for line in self.line_ids.filtered(lambda line: line.number_product == 0):
            line.quick_create_product()


class product_product_inherit(models.Model):
    _inherit = 'product.product'

    @api.multi
    def name_get(self):
        if 'only_show_default_code' in self._context:
            return [(record.id, "%s" % (record.default_code)) for record
                    in self]
        if self._context.get('name_search',False):
            return [(record.id, "[%s] %s - %s - %s%s" % (record.default_code, record.name, '{0:,.0f}'.format(record.virtual_available), '{0:,.0f}'.format(record.list_price),record.currency_id.symbol or '')) for record in self]
        else:
            return super(product_product_inherit, self).name_get()

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        res = super(product_product_inherit, self.with_context(name_search=True)).name_search(name=name, args=args, operator=operator, limit=limit)
        return res

class job_quotaion_product_line(models.TransientModel):
    _name = 'job.quotaion.product.line'

    default_code = fields.Char('Mã sản phẩm', required=True)
    description = fields.Char('Mô tả', required=True)
    uom_id = fields.Many2one('product.uom', 'Đơn vị')

    @api.model
    def default_get(self, fields):
        res = super(job_quotaion_product_line, self).default_get(fields)
        if self._context and 'active_id' in self._context and self._context['active_id']:
            quoaion_line = self.env['job.quotaion.line'].browse(self._context['active_id'])
            if quoaion_line:
                res.update({
                    'default_code': quoaion_line.ma_san_pham,
                    'description': quoaion_line.description,
                    'uom_id': quoaion_line.product_uom and quoaion_line.product_uom.id or False
                })
        return res

    @api.multi
    def create_product(self):
        product_obj = self.env['product.template']
        product_id = product_obj.create({
            'name': self.description,
            'default_code': self.default_code,
            'uom_id': self.uom_id.id,
            'uom_po_id': self.uom_id.id,
        })
        if self._context and 'active_id' in self._context and self._context['active_id']:
            quoaion_line = self.env['job.quotaion.line'].browse(self._context['active_id'])
            if quoaion_line:
                quoaion_line.product_id = product_id.product_variant_id
                quoaion_line.description = product_id.name
                quoaion_line.ma_san_pham = product_id.default_code
                quoaion_line.product_uom = product_id.uom_id
                quoaion_line.product_ids = json.dumps(product_id.product_variant_id.ids)


class job_quotaion_line(models.Model):
    _inherit = 'job.quotaion.line'

    list_price          = fields.Float('Giá bán',related='product_id.list_price')
    virtual_available   = fields.Float('SL Dự báo',related='product_id.virtual_available')
    so_luong            = fields.Char(string="S/L", default='1')

    @api.multi
    def quick_create_product(self):
        product_obj = self.env['product.template']
        if self.ma_san_pham:
            product_id = product_obj.search([('default_code', 'ilike', self.ma_san_pham)])
            if not product_id:
                product_id = product_obj.create({
                    'name': self.description or self.ma_san_pham,
                    'default_code': self.ma_san_pham,
                    'uom_id': self.product_uom and self.product_uom.id or self.product_uom.search(
                        [('name', '=', 'Cái')], limit=1).id,
                    'uom_po_id': self.product_uom and self.product_uom.id or self.product_uom.search(
                        [('name', '=', 'Cái')], limit=1).id
                })
                self.product_id = product_id.product_variant_id
                self.product_ids = json.dumps(product_id.product_variant_id.ids)
            else:
                raise UserError("Mã sản phẩm %s đã tồn tại." % (self.ma_san_pham))
        else:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'job.quotaion.product.line',
                'view_mode': 'form',
                'view_type': 'form',
                'view_id': self.env.ref('cptuanhuy_project.job_quotaion_product_line_form').id,
                'target': 'new',
            }


