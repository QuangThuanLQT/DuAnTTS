# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

class tiep_ngu_dau(models.Model):
    _name = 'tiep.ngu.dau'

    name = fields.Char('Name')

class SaleConfiguration(models.TransientModel):
    _inherit = 'sale.config.settings'

    ma_dau_sp_setting = fields.Many2many(
        'tiep.ngu.dau',
        string='Mặc định tạo MO cho sản phẩm có mã',
        help='Tiếp ngữ đầu')

    @api.multi
    def set_ma_dau_sp_setting_defaults(self):
        return self.env['ir.values'].sudo().set_default(
            'sale.config.settings', 'ma_dau_sp_setting', self.ma_dau_sp_setting.ids)

class sale_order(models.Model):
    _inherit = 'sale.order'

    def get_ma_dau_sp_setting(self):
        tiep_ngu_dau_ids = self.env['ir.values'].get_default('sale.config.settings', 'ma_dau_sp_setting')
        return self.env['tiep.ngu.dau'].browse(tiep_ngu_dau_ids).mapped('name')

    @api.multi
    def action_create_bom(self):
        manufacture_id = self.env.ref('mrp.route_warehouse0_manufacture').id
        routing_id     = self.env.ref('cptuanhuy_mrp.mrp_routing_tuanhuy').id

        for record in self:
            for order_line in record.order_line:
                if manufacture_id in order_line.product_id.route_ids.ids:
                    mrp_bom = self.env['mrp.bom'].search([
                        ('product_tmpl_id', '=', order_line.product_id.product_tmpl_id.id)
                    ], limit=1)
                    if not mrp_bom:
                        bom_data = {
                            'product_tmpl_id' : order_line.product_id.product_tmpl_id.id,
                            'product_uom_id'  : order_line.product_id.uom_id.id,
                            'routing_id'      : routing_id or False,
                            'so_id'           : record.id,
                            'so_line_id'      : order_line.id,
                        }
                        self.env['mrp.bom'].create(bom_data)

        return True

    @api.multi
    def action_open_mo(self):
        mo_ids = []
        procurement_group_ids = self.procurement_group_id
        procurement_ids = self.env['procurement.order'].search([('group_id','in',procurement_group_ids.ids)])
        for procurement_id in procurement_ids:
            mo_id = self.env['mrp.production'].search([('procurement_ids','=',procurement_id.id)])
            if mo_id:
                mo_ids.append(mo_id.id)
        action = self.env.ref('mrp.mrp_production_action').read()[0]
        action['domain'] = [('id', 'in', mo_ids)]
        action['context'] = {'default_origin': self.name or ''}
        return action

    @api.multi
    def action_open_full_mo(self):
        mo_ids = []
        procurement_group_ids = self.procurement_group_id
        picking_ids = self.env['stock.picking'].search([('sale_select_id','=',self.id)])
        procurement_picking_ids = picking_ids.mapped('move_lines').mapped('procurement_id').ids
        procurement_ids = self.env['procurement.order'].search(['|',('group_id', 'in', procurement_group_ids.ids),('id','in',procurement_picking_ids)])
        for procurement_id in procurement_ids:
            mo_id = self.env['mrp.production'].search([('procurement_ids', '=', procurement_id.id)])
            if mo_id:
                mo_ids.append(mo_id.id)
        production_ids = self.env['mrp.production'].search([
            ('origin', 'like', '%'+self.name+'%')
        ])
        for record in production_ids:
            if record.id not in mo_ids:
                mo_ids.append(record.id)
        action = self.env.ref('mrp.mrp_production_action').read()[0]
        action['domain'] = [('id', 'in', mo_ids)]
        action['context'] = {'default_origin': self.name or ''}
        return action

    @api.multi
    def action_cancel(self):
        mo_obj_ids = self.env['mrp.production']
        procurement_group_ids = self.procurement_group_id
        procurement_ids = self.env['procurement.order'].search([('group_id', 'in', procurement_group_ids.ids)])
        for procurement_id in procurement_ids:
            mo_ids = self.env['mrp.production'].search([('procurement_ids', '=', procurement_id.id)])
            if mo_ids and any(mo_id.state not in ('confirmed','cancel','planned') for mo_id in mo_ids):
                raise UserError('Không thể huỷ đơn hàng có lệnh sản xuất đang xử lý.')
            else:
                mo_obj_ids += mo_ids
        for mo_obj_id in mo_obj_ids:
            finish_moves = mo_obj_id.move_finished_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
            raw_moves = mo_obj_id.move_raw_ids.filtered(lambda x: x.state not in ('done', 'cancel'))

            procurements = self.env['procurement.order'].search([('move_dest_id', 'in', (finish_moves | raw_moves).ids)])
            for procurement_id in procurements:
                if procurement_id.rule_id.action == 'buy' and procurement_id.purchase_line_id:
                    if procurement_id.purchase_line_id.order_id.state not in ('draft', 'cancel', 'sent', 'to validate'):
                        procurement_id.purchase_line_id.order_id.button_cancel()
            mo_obj_id.action_cancel()
            mo_obj_id.unlink()

        res = super(sale_order, self).action_cancel()
        return res

    @api.multi
    def action_confirm(self):
        for record in self:
            # so_type_sx_id = self.env.ref('cptuanhuy_project_contract.sale_order_type_sx')
            # if record.sale_from_project == True and record.so_type_id.type != so_type_sx_id:
            #     for line in record.order_line:
            #         line.product_id.write({
            #             'purchase_ok' : True,
            #             'route_ids': [(6, 0, [self.env.ref('purchase.route_warehouse0_buy').id])],
            #         })

            if record.so_type_id.type == 'sanxuat':
                for line in record.order_line:
                    # list_ma_dau = record.get_ma_dau_sp_setting()
                    # check = False
                    # if not list_ma_dau:
                    #     check = True
                    # for ma_dau in list_ma_dau:
                    #     if line.product_id.default_code and ma_dau in line.product_id.default_code:
                    #         check = True
                    # if check:
                    line.product_id.write({
                        'purchase_ok' : False,
                        'route_ids' : [(6, 0, [
                            self.env.ref('mrp.route_warehouse0_manufacture').id,
                            self.env.ref('stock.route_warehouse0_mto').id
                        ])],
                    })

            record.create_bom_form_sale()

        res = super(sale_order, self).action_confirm()
        return res

    @api.multi
    def create_bom_form_sale(self):
        self.action_create_bom()

        for record in self:
            for order_line in record.order_line:
                mrp_bom = self.env['mrp.bom'].search([
                    ('product_tmpl_id', '=', order_line.product_id.product_tmpl_id.id)
                ], limit=1)
                # if not mrp_bom:
                #     mrp_bom = self.env['mrp.bom'].create({
                #         'product_tmpl_id': order_line.product_id.product_tmpl_id.id,
                #         # 'routing_id': self.mrp_routing_id and self.mrp_routing_id.id or False,
                #         'so_id' : self.id,
                #         'so_line_id' : order_line.id,
                #     })
                #     for line in self.job_costing_id.job_cost_line_ids:
                #         mrp_bom.bom_line_ids += mrp_bom.bom_line_ids.new({
                #             'product_id': line.product_id.id,
                #             'product_qty': line.product_qty
                #         })
                # else:
                if mrp_bom:
                    if not mrp_bom.routing_id:
                        # mrp_bom.routing_id = self.mrp_routing_id
                        mrp_bom.so_id      = record.id
                        mrp_bom.so_line_id = order_line.id

class sale_order_line_inherit(models.Model):
    _inherit = 'sale.order.line'


    @api.model
    def _get_wo_state(self):
        result = []
        states = self.env['work.order.state'].sudo().search([])
        for state in states:
            result.append((state.code, state.name))
        return result

    wo_id = fields.Many2one('mrp.workorder', 'Công đoạn', compute='_compute_mo')
    wo_state = fields.Selection([
        ('pending', 'Đang chờ'),
        ('ready', 'Sẵn sàng'),
        ('progress', 'Đang xử lý'),
        ('done', 'Đã kết thúc'),
        ('cancel', 'Huỷ')], string='Trạng thái',compute='_compute_mo')

    @api.multi
    def _compute_mo(self):
        for record in self:
            record.wo_id = False
            record.wo_state = False
            # mo_ids = []
            # procurement_group_ids = record.order_id.procurement_group_id
            # procurement_ids = self.env['procurement.order'].search([('group_id', 'in', procurement_group_ids.ids)])
            # for procurement_id in procurement_ids:
            #     mo_id = self.env['mrp.production'].search([('procurement_ids', '=', procurement_id.id)])
            #     if mo_id:
            #         mo_ids.append(mo_id.id)
            # productions = self.env['mrp.production'].browse(mo_ids)
            # production = productions.filtered(lambda r: r.product_id == record.product_id)
            # # production = self.env['mrp.production'].search([
            # #     ('so_id', '=', record.order_id.id),
            # #     ('so_line_id', '=', record.id),
            # # ], limit=1)
            # if production and len(production) == 1 and production.id:
            #     if production.workorder_ids:
            #         wc_end = production.workorder_ids[len(production.workorder_ids) - 1].id
            #         for wo_line in production.workorder_ids:
            #             if wo_line.state != 'done' or wc_end == wo_line.id:
            #                 record.wo_id = wo_line
            #                 record.wo_state = wo_line.state
            #                 break
            # else:
            #     production = self.env['mrp.production'].search([
            #         ('so_id', '=', record.order_id.id),
            #         ('so_line_id', '=', record.id),
            #     ], limit=1)
            #     if production.workorder_ids:
            #         wc_end = production.workorder_ids[len(production.workorder_ids) - 1].id
            #         for wo_line in production.workorder_ids:
            #             if wo_line.state != 'done' or wc_end == wo_line.id:
            #                 record.wo_id = wo_line
            #                 record.wo_state = wo_line.state
            #                 break