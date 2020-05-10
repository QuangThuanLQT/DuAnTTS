# -*- coding: utf-8 -*-

from odoo import models, fields, api


class stock_picking_ihr(models.Model):
    _inherit = 'stock.picking'


    purchase_reason_cancel = fields.Many2one('reason.cancel.purchase', 'Lý do huỷ', readonly=True)
    user_return_id = fields.Many2one('res.users', 'Nhân viên tạo trả hàng NCC', readonly=True, copy=False)
    purchase_id = fields.Many2one('purchase.order', related=False, compute='_get_purchase_id',
                                  string="Purchase Orders", readonly=True)

    @api.multi
    def write(self, val):
        res = super(stock_picking_ihr, self).write(val)
        for rec in self:
            if (val.get('state_pick',False) or val.get('state_pack',False) or val.get('receipt_state',False) or \
                val.get('state_delivery', False) or val.get('internal_transfer_state',False)) and rec.purchase_id:
                rec.purchase_id.get_operation_state()
        return res

    @api.model
    def create(self, val):
        res = super(stock_picking_ihr, self).create(val)
        if res.origin:
            if 'RTP' in res.origin:
                purchase_id = self.env['purchase.order'].search([('name', '=', res.origin)], limit=1)
                if purchase_id and purchase_id.purchase_order_return == True:
                    purchase_id.get_operation_state()
            if 'PO' in res.origin:
                purchase_id = self.env['purchase.order'].search([('name', '=', res.origin)], limit=1)
                if purchase_id and purchase_id.purchase_order_return == False:
                    purchase_id.get_operation_state()
        return res

    @api.multi
    def _get_purchase_id(self):
        for record in self:
            id = False
            for move in record.move_lines:
                if move.purchase_line_id:
                    id = move.purchase_line_id.order_id
                    break
            if not id:
                if record.group_id:
                    purchase_id = self.env['purchase.order'].search([('group_id', '=', record.group_id.id)])
                    id = purchase_id if purchase_id else False
            record.purchase_id = id


    @api.multi
    def do_new_transfer(self):
        res = super(stock_picking_ihr, self).do_new_transfer()
        for rec in self:
            if rec.is_picking_return :
                if rec.purchase_id and rec.purchase_id.purchase_order_return == False:
                    rec.purchase_id.state = 'cancel'
        return res

    @api.multi
    def pick_action_do_new_transfer(self):
        res = super(stock_picking_ihr, self).pick_action_do_new_transfer()
        for rec in self:
            if rec.purchase_id:
                rec.purchase_id.get_operation_state()
        return res