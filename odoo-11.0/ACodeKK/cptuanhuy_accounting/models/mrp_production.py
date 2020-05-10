# -*- coding: utf-8 -*-

from odoo import models, fields, api

class mrp_production_inherit(models.Model):
    _inherit = 'mrp.production'

    material_cost    = fields.Float(compute='compute_amount_product', store=True)
    account_move_ids = fields.One2many('account.move.line', 'mrp_production_id', string="Phân bổ")
    raw_picking_ids  = fields.Many2many('stock.picking', compute = '_get_raw_picking_ids')

    @api.multi
    def _get_raw_picking_ids(self):
        for record in self:
            group_id = record.procurement_ids.mapped('group_id')
            so_id    = self.env['sale.order'].search([('procurement_group_id', '=', group_id.id)], limit=1)
            if so_id:
                picking_same_so_ids    = self.env['stock.picking'].search([('sale_select_id', '=', so_id.id), ('state', '=', 'done')])
                record.raw_picking_ids = picking_same_so_ids

    def get_count_mrp_for_so(self,so_id):
        mo_ids = []
        procurement_group_ids = so_id.procurement_group_id
        procurement_ids = self.env['procurement.order'].search([
            ('group_id', 'in', procurement_group_ids.ids)
        ])
        for procurement_id in procurement_ids:
            mo_id = self.env['mrp.production'].search([
                ('procurement_ids', '=', procurement_id.id)
            ])
            if mo_id:
                mo_ids.append(mo_id.id)
        return len(mo_ids)

    @api.multi
    def update_production_price(self):
        for rec in self:
            if rec.state == 'done':
                rec.compute_amount_product()
                new_cost = rec.material_cost + sum(rec.account_move_ids.mapped('debit'))
                for move in rec.move_finished_ids:
                    total_qty = sum(rec.move_finished_ids.mapped('product_uom_qty'))
                    move.price_unit = new_cost / total_qty
                    move.quant_ids.write({
                        'cost': new_cost / move.product_uom_qty,
                    })
                    for quant_id in move.quant_ids:
                        for move_id in quant_id.history_ids:
                            if move_id.picking_id:
                                picking_aml_ids = self.env['account.move.line'].search(
                                    [('ref', '=', move_id.picking_id.name), (
                                        'product_code', '=', move.product_id.default_code)])
                                for aml_id in picking_aml_ids:
                                    if aml_id.debit > 0:
                                        self._cr.execute("""UPDATE account_move_line SET debit=%s WHERE id=%s""" % (
                                            new_cost / move.product_uom_qty * move_id.product_uom_qty, aml_id.id))
                                    elif aml_id.credit > 0:
                                        self._cr.execute(
                                            """UPDATE account_move_line SET credit=%s WHERE id=%s""" % (
                                                new_cost / move.product_uom_qty * move_id.product_uom_qty,
                                                aml_id.id))
                    aml_ids = self.env['account.move.line'].search([('name', '=', rec.name), (
                        'product_code', '=', move.product_id.default_code)])
                    for aml in aml_ids:
                        if aml.debit > 0:
                            self._cr.execute(
                                """UPDATE account_move_line SET debit=%s WHERE id=%s""" % (new_cost, aml.id))
                        elif aml.credit > 0:
                            self._cr.execute(
                                """UPDATE account_move_line SET credit=%s WHERE id=%s""" % (new_cost, aml.id))

    @api.multi
    @api.depends('state', 'move_raw_ids', 'workorder_ids',)
    def compute_amount_product(self):
        for record in self:
            if record.state == 'done' or 'get_price_unit' in self._context:
                account_move_add = record.move_raw_ids.ids
                account_move_remove = []
                for workorder in record.workorder_ids:
                    if workorder.stock_picking_delivery_ids:
                        account_move_add += workorder.stock_picking_delivery_ids.filtered(lambda sp: sp.state == 'done').mapped('move_lines').ids
                    if workorder.stock_picking_return_ids:
                        account_move_remove += workorder.stock_picking_return_ids.filtered(lambda sp: sp.state == 'done').mapped('move_lines').ids
                    # if workorder.stock_picking_lost_ids:
                    #     account_move_add += workorder.stock_picking_lost_ids.mapped('move_lines').ids
                account_move_add = self.env['stock.move'].search([('id','in',account_move_add)])
                account_move_remove = self.env['stock.move'].search([('id','in',account_move_remove)])
                total_amount = 0
                for account_move_id in account_move_add:
                    total_amount += account_move_id.price_unit * account_move_id.product_uom_qty
                for account_move_id in account_move_remove:
                    total_amount -= account_move_id.price_unit * account_move_id.product_uom_qty
                # record.material_cost = total_amount

                location_production_id = self.env.ref('cptuanhuy_mrp.location_ksx_stock').id
                mrp_transfer_pickings  = self.env['stock.picking'].search([
                    ('mrp_production', '=', record.id),
                    ('state', '=', 'done'),
                    ('location_dest_id', '=', location_production_id)
                ])
                total_picking_transfer = sum(mrp_transfer_pickings.mapped('move_lines').mapped('quant_ids').mapped('inventory_value'))
                # if not total_picking_transfer:
                #     total_picking_transfer = sum(mrp_transfer_pickings.mapped('move_lines').mapped('quant_ids').mapped('inventory_value'))
                total_amount          += total_picking_transfer
                record.material_cost   = total_amount

                # group_id = record.procurement_ids.mapped('group_id')
                # so_id = self.env['sale.order'].search([('procurement_group_id','=',group_id.id)],limit=1)
                # if so_id:
                #     count_mrp_for_so = self.get_count_mrp_for_so(so_id)
                #     picking_same_so_ids = self.env['stock.picking'].search([('sale_select_id', '=', so_id.id),('mrp_production','=',False), ('state', '=', 'done')])
                #     for picking_same_so_id in picking_same_so_ids:
                #         total_picking = sum(picking_same_so_id.mapped('move_lines').mapped('quant_ids').mapped('inventory_value'))
                #         record.material_cost += total_picking / count_mrp_for_so

