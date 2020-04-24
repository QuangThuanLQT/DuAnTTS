# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

class sale_order_ihr(models.Model):
    _inherit = 'sale.order'

    state_log_ids = fields.One2many('state.log','sale_id',string='History Log', readonly=1)

    @api.multi
    def update_sale_log_block(self):
        for rec in self:
            check = False
            sequence = 0
            for log_line in rec.state_log_ids.sorted('sequence', reverse=False):
                if check:
                    log_line.sequence = sequence
                    sequence += 1
                if log_line.state == rec.trang_thai_dh and not check:
                    check = True
                    sequence = log_line.sequence
                    sequence += 1
                    self.env['state.log'].create({
                        'sequence': sequence,
                        'state': 'block',
                        'sale_id': rec.id,
                        'date' : datetime.now(),
                    })
                    sequence += 1

    @api.model
    def create(self, val):
        res = super(sale_order_ihr, self).create(val)
        if not res.sale_order_return:
            trang_thai = ['waiting_pick','ready_pick','picking','waiting_pack','packing','waiting_delivery','delivery','done']
            count = 0
            for tt in trang_thai:
                count += 1
                self.env['state.log'].create({
                    'sequence' : count,
                    'state' : tt,
                    'sale_id' : res.id,
                })
        else:
            trang_thai = ['reveive', 'waiting', 'checking', 'done']
            count = 0
            for tt in trang_thai:
                count += 1
                self.env['state.log'].create({
                    'state' : tt,
                    'sale_id' : res.id,
                    'sequence': count,
                })
        return res

class purchase_order_ihr(models.Model):
    _inherit = 'purchase.order'

    state_log_ids = fields.One2many('state.log', 'purchase_id', string='History Log', readonly=1)

    @api.model
    def create(self, val):
        res = super(purchase_order_ihr, self).create(val)
        if not res.purchase_order_return:
            trang_thai = ['reveive', 'waiting', 'checking', 'done']
            count = 0
            for tt in trang_thai:
                count += 1
                self.env['state.log'].create({
                    'sequence': count,
                    'state': tt,
                    'purchase_id': res.id,
                })
        else:
            trang_thai = ['waiting_pick', 'ready_pick', 'picking', 'waiting_pack', 'packing', 'waiting_delivery',
                          'delivery', 'done']
            count = 0
            for tt in trang_thai:
                count += 1
                self.env['state.log'].create({
                    'sequence': count,
                    'state': tt,
                    'purchase_id': res.id,
                })
        return res

    def button_action_return(self):
        res = super(purchase_order_ihr, self).button_action_return()
        for rec in self:
            if rec.purchase_order_return:
                state_log_id = self.env['state.log'].search([('purchase_id', '=', rec.id), ('state', '=', 'waiting_pick')])
                if state_log_id:
                    state_log_id.date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        return res

class stock_picking_ihr(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def create(self, val):
        res = super(stock_picking_ihr, self).create(val)
        if not res.is_picking_return:
            if res.check_is_pick and res.origin_sub:
                if 'SO' in res.origin_sub:
                    sale_id = self.env['sale.order'].search([('name', '=', res.origin_sub)], limit=1)
                    if sale_id and sale_id.sale_order_return == False:
                        res.write_date_log('sale.order', sale_id.id, 'waiting_pick')
                if 'RTP' in res.origin_sub:
                    purchase_id = self.env['purchase.order'].search([('name', '=', res.origin_sub)], limit=1)
                    if purchase_id and purchase_id.purchase_order_return == True:
                        res.write_date_log('purchase.order', purchase_id.id, 'waiting_pick')
            if res.origin_sub:
                if 'RT' in res.origin_sub:
                    sale_id = self.env['sale.order'].search([('name', '=', res.origin_sub)], limit=1)
                    if sale_id and sale_id.sale_order_return == True:
                        res.write_date_log('sale.order', sale_id.id, 'reveive')
                if 'PO' in res.origin:
                    purchase_id = self.env['purchase.order'].search([('name', '=', res.origin)], limit=1)
                    if purchase_id and purchase_id.purchase_order_return == False:
                        res.write_date_log('purchase.order', purchase_id.id, 'reveive')
        return res

    def write_date_log(self,model,record_id,state):
        if model == 'sale.order':
            state_log_id = self.env['state.log'].search([('sale_id', '=', record_id),('state','=',state)])
            if state_log_id:
                state_log_id.date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        elif model == 'purchase.order':
            state_log_id = self.env['state.log'].search([('purchase_id', '=', record_id), ('state', '=', state)])
            if state_log_id:
                state_log_id.date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    @api.multi
    def write(self, val):
        if 'internal_transfer_state' in val:
            for rec in self:
                if not rec.is_picking_return:
                    new_state = val.get('internal_transfer_state')
                    if rec.sale_id:
                        if new_state == 'waiting':
                            rec.write_date_log('sale.order', rec.sale_id.id, 'waiting')
                        if new_state == 'checking':
                            rec.write_date_log('sale.order', rec.sale_id.id, 'checking')
                        if new_state == 'done':
                            rec.write_date_log('sale.order', rec.sale_id.id, 'done')
                    if rec.purchase_id:
                        if new_state == 'waiting':
                            rec.write_date_log('purchase.order', rec.purchase_id.id, 'waiting')
                        if new_state == 'checking':
                            rec.write_date_log('purchase.order', rec.purchase_id.id, 'checking')
                        if new_state == 'done':
                            rec.write_date_log('purchase.order', rec.purchase_id.id, 'done')

        if 'receipt_state' in val:
            for rec in self:
                if not rec.is_picking_return:
                    new_state = val.get('receipt_state')
                    if rec.sale_id:
                        if new_state == 'reveive':
                            rec.write_date_log('sale.order', rec.sale_id.id, 'reveive')
                    if rec.purchase_id:
                        if new_state == 'reveive':
                            rec.write_date_log('purchase.order', rec.purchase_id.id, 'reveive')

        if 'state_pick' in val:
            for rec in self:
                if not rec.is_picking_return:
                    new_state = val.get('state_pick')
                    sale_id = rec.sale_id or self.env['sale.order'].search([('name', '=', rec.origin_sub)], limit=1) or False
                    if sale_id:
                        if new_state == 'waiting_pick':
                            rec.write_date_log('sale.order',sale_id.id,'waiting_pick')
                        if new_state == 'ready_pick':
                            rec.write_date_log('sale.order', sale_id.id, 'ready_pick')
                        if new_state == 'picking':
                            rec.write_date_log('sale.order', sale_id.id, 'picking')
                    if rec.purchase_id:
                        if new_state == 'waiting_pick':
                            rec.write_date_log('purchase.order',rec.purchase_id.id,'waiting_pick')
                        if new_state == 'ready_pick':
                            rec.write_date_log('purchase.order', rec.purchase_id.id, 'ready_pick')
                        if new_state == 'picking':
                            rec.write_date_log('purchase.order', rec.purchase_id.id, 'picking')

        if 'state_pack' in val:
            for rec in self:
                if not rec.is_picking_return:
                    new_state = val.get('state_pack')
                    if rec.sale_id:
                        if new_state == 'waiting_pack':
                            rec.write_date_log('sale.order', rec.sale_id.id, 'waiting_pack')
                        if new_state == 'packing':
                            rec.write_date_log('sale.order', rec.sale_id.id, 'packing')
                    if rec.purchase_id:
                        if new_state == 'waiting_pack':
                            rec.write_date_log('purchase.order', rec.purchase_id.id, 'waiting_pack')
                        if new_state == 'packing':
                            rec.write_date_log('purchase.order', rec.purchase_id.id, 'packing')

        if 'state_delivery' in val:
            for rec in self:
                if not rec.is_picking_return:
                    new_state = val.get('state_delivery')
                    if rec.sale_id:
                        if new_state == 'waiting_delivery':
                            rec.write_date_log('sale.order', rec.sale_id.id, 'waiting_delivery')
                        if new_state == 'delivery':
                            rec.write_date_log('sale.order', rec.sale_id.id, 'delivery')
                        if new_state == 'done':
                            rec.write_date_log('sale.order', rec.sale_id.id, 'done')
                    if rec.purchase_id:
                        if new_state == 'waiting_delivery':
                            rec.write_date_log('purchase.order', rec.purchase_id.id, 'waiting_delivery')
                        if new_state == 'delivery':
                            rec.write_date_log('purchase.order', rec.purchase_id.id, 'delivery')
                        if new_state == 'done':
                            rec.write_date_log('purchase.order', rec.purchase_id.id, 'done')

        res = super(stock_picking_ihr, self).write(val)
        return res