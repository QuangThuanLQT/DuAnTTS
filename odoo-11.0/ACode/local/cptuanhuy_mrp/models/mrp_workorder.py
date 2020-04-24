# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import UserError
from odoo.tools import float_round

class mrp_workorder_inherit(models.Model):
    _inherit = 'mrp.workorder'

    stock_picking_delivery_ids = fields.One2many('stock.picking', 'mrp_workorder_delivery_id')
    stock_picking_return_ids   = fields.One2many('stock.picking', 'mrp_workorder_return_id')
    stock_picking_lost_ids     = fields.One2many('stock.picking', 'mrp_workorder_lost_id')
    mrp_bom_line_ids           = fields.Many2many('stock.move',compute="_get_mrp_bom_line_ids")
    responsible_id             = fields.Many2one('res.users', 'Responsible')
    code                       = fields.Char(string='Mã công việc')
    code_before                = fields.Char(string='Công việc trước')
    priority_id                = fields.Many2one('mrp.priority', u'Độ ưu tiên',default=lambda x: x.env.ref('cptuanhuy_mrp.mrp_priority_trung_binh'))

    def get_list_code_before(self):
        list = []
        if self.code_before:
            list = self.code_before.split(',')
            list = [l.strip() for l in list]
        return list

    def check_next_work_order_id(self):
        workorder_ids = self.env['mrp.workorder'].search([('production_id','=',self.production_id.id),('id','!=',self.id)])
        next_work_order_ids = self.env['mrp.workorder']
        for workorder_id in workorder_ids:
            list_code_before = workorder_id.get_list_code_before()
            if self.code in list_code_before:
                list_workorder_before = self.env['mrp.workorder'].search([('production_id', '=', self.production_id.id),('id','!=',self.id),('code', 'in', list_code_before)])
                if all(workorder.state == 'done' for workorder in list_workorder_before):
                    next_work_order_ids += workorder_id
        return next_work_order_ids

    @api.multi
    def record_production(self):
        self.ensure_one()
        if self.qty_producing <= 0:
            raise UserError(_('Please set the quantity you produced in the Current Qty field. It can not be 0!'))

        if (self.production_id.product_id.tracking != 'none') and not self.final_lot_id:
            raise UserError(_('You should provide a lot for the final product'))

        # Update quantities done on each raw material line
        raw_moves = self.move_raw_ids.filtered(
            lambda x: (x.has_tracking == 'none') and (x.state not in ('done', 'cancel')) and x.bom_line_id)
        for move in raw_moves:
            if move.unit_factor:
                rounding = move.product_uom.rounding
                move.quantity_done += float_round(self.qty_producing * move.unit_factor, precision_rounding=rounding)

        # Transfer quantities from temporary to final move lots or make them final
        for move_lot in self.active_move_lot_ids:
            # Check if move_lot already exists
            if move_lot.quantity_done <= 0:  # rounding...
                move_lot.sudo().unlink()
                continue
            if not move_lot.lot_id:
                raise UserError(_('You should provide a lot for a component'))
            # Search other move_lot where it could be added:
            lots = self.move_lot_ids.filtered(
                lambda x: (x.lot_id.id == move_lot.lot_id.id) and (not x.lot_produced_id) and (not x.done_move))
            if lots:
                lots[0].quantity_done += move_lot.quantity_done
                lots[0].lot_produced_id = self.final_lot_id.id
                move_lot.sudo().unlink()
            else:
                move_lot.lot_produced_id = self.final_lot_id.id
                move_lot.done_wo = True

        # One a piece is produced, you can launch the next work order
        next_work_order_ids = self.check_next_work_order_id()
        if next_work_order_ids:
            for next_work_order_id in next_work_order_ids:
                if next_work_order_id.state == 'pending':
                    next_work_order_id.state = 'ready'
                if next_work_order_id and self.final_lot_id and not next_work_order_id.final_lot_id:
                    next_work_order_id.final_lot_id = self.final_lot_id.id

        self.move_lot_ids.filtered(
            lambda move_lot: not move_lot.done_move and not move_lot.lot_produced_id and move_lot.quantity_done > 0
        ).write({
            'lot_produced_id': self.final_lot_id.id,
            'lot_produced_qty': self.qty_producing
        })

        # If last work order, then post lots used
        # TODO: should be same as checking if for every workorder something has been done?
        if not next_work_order_ids:
            production_moves = self.production_id.move_finished_ids.filtered(
                lambda x: (x.state not in ('done', 'cancel')))
            for production_move in production_moves:
                if production_move.product_id.id == self.production_id.product_id.id and production_move.product_id.tracking != 'none':
                    move_lot = production_move.move_lot_ids.filtered(lambda x: x.lot_id.id == self.final_lot_id.id)
                    if move_lot:
                        move_lot.quantity += self.qty_producing
                        move_lot.quantity_done += self.qty_producing
                    else:
                        move_lot.create({'move_id': production_move.id,
                                         'lot_id': self.final_lot_id.id,
                                         'quantity': self.qty_producing,
                                         'quantity_done': self.qty_producing,
                                         'workorder_id': self.id,
                                         })
                elif production_move.unit_factor:
                    rounding = production_move.product_uom.rounding
                    production_move.quantity_done += float_round(self.qty_producing * production_move.unit_factor,
                                                                 precision_rounding=rounding)
                else:
                    production_move.quantity_done += self.qty_producing  # TODO: UoM conversion?
        # Update workorder quantity produced
        self.qty_produced += self.qty_producing

        # Set a qty producing
        if self.qty_produced >= self.production_id.product_qty:
            self.qty_producing = 0
        elif self.production_id.product_id.tracking == 'serial':
            self.qty_producing = 1.0
            self._generate_lot_ids()
        else:
            self.qty_producing = self.production_id.product_qty - self.qty_produced
            self._generate_lot_ids()

        self.final_lot_id = False
        if self.qty_produced >= self.production_id.product_qty:
            self.button_finish()
        return True

    @api.multi
    def _get_mrp_bom_line_ids(self):
        for record in self:
            mrp_bom_line_ids = []
            if record.production_id and record.production_id.bom_id:
                for line in record.production_id.bom_id.bom_line_ids:
                    if line.operation_id == record.operation_id:
                        mrp_bom_line_ids.append(line.id)
            if record.production_id:
                record.mrp_bom_line_ids = record.production_id.move_raw_ids.filtered(lambda l:l.bom_line_id.id in mrp_bom_line_ids)

    @api.model
    def create(self, values):
        res = super(mrp_workorder_inherit, self).create(values)
        if res.mrp_bom_line_ids:
            picking_id = self.env['stock.picking'].with_context(stock_picking_delivery=True,production_id=res.production_id.id).create({
                'picking_workorder_from_mo' : True
            })
            picking_id.move_lines = [(6,0,res.mrp_bom_line_ids.ids)]
            res.stock_picking_delivery_ids = [(6,0,picking_id.ids)]
        if not res.priority_id:
            res.priority_id = res.production_id.priority_id
        return res




