# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _

class sale_order(models.Model):
    _inherit = "sale.order"

    state = fields.Selection([
        ('draft', '1. Draft Quotation'),
        ('waiting_manager', '2. Waiting Manager'),
        ('waiting_director', '3. Waiting Director'),
        ('approved', '4. Approved'),
        ('sent', '5. Quotation Sent'),
        ('sale', '6. Sale Order'),
        ('progress', '7. Order Processing'),
        ('manual', '7. Sale to Invoice'),
        ('cancel', '8. Cancelled'),
        ('done', '8. Done'),
        ('waiting_date', 'Waiting Schedule'),
        ('invoice_except', 'Invoice Exception'),
    ], 'Status', readonly=True, track_visibility='onchange', select=True)
    internal_state = fields.Char('State', compute="_compute_state", store=True)

    @api.model
    def _bom_find(self, order_line):
        bom_obj = self.env['mrp.bom']
        domain = [('so_line_id', '=', order_line.id)]
        return bom_obj.search(domain, order='sequence, product_id', limit=1)

    @api.multi
    def button_dummy(self):
        for order in self:
            if order.sale_order_type == 'customize':
                for order_line in order.order_line:
                    gia_ban = 0
                    gia_von = 0

                    bom = self._bom_find(order_line)
                    if not bom or not bom.id:
                        raise exceptions.UserError(_('Please to create bom structure.'))

                    for bom_line in bom.bom_line_ids:
                        # price_id = order.pricelist_id.id
                        list_price = bom_line.product_id.uom_id._compute_price(bom_line.product_id.lst_price, to_unit=bom_line.product_uom_id)
                        gia_ban += list_price * bom_line.product_qty

                        cost_price = bom_line.product_id.uom_id._compute_price(bom_line.product_id.standard_price, to_unit=bom_line.product_uom_id)
                        gia_von += cost_price * bom_line.product_qty

                    order_line.price_unit = gia_ban
        return True

    @api.multi
    @api.depends('state')
    def _compute_state(self):
        for order in self:
            str = ''
            if order.state == 'draft':
                str = '1. Draft Quotation'
            elif order.state == 'waiting_manager':
                str = '2. Waiting Manager'
            elif order.state == 'waiting_director':
                str = '3. Waiting Director'
            elif order.state == 'approved':
                str = '4. Approved'
            elif order.state == 'sent':
                str = '5. Quotation Sent'
            elif order.state == 'progress':
                str = '6. Order Processing'
            elif order.state == 'manual':
                str = '7. Sale to Invoice'
            elif order.state == 'done':
                str = '8. Done'
            elif order.state == 'cancel':
                str = '8. Cancelled'
            elif order.state == 'shipping_except':
                str = 'Shipping Exception'
            elif order.state == 'invoice_except':
                str = 'Invoice Exception'
            elif order.state == 'order_in_process':
                str = 'Undefined'
            order.internal_state = str

    @api.multi
    def action_waiting_manager(self):
        self.write({'state': 'waiting_manager'})
        return True

    @api.multi
    def action_waiting_director(self):
        self.write({'state': 'waiting_director'})
        return True

    @api.multi
    def action_approve(self):
        self.write({'state': 'approved'})
        return True

    @api.multi
    def action_refuse_director(self):
        self.write({'state': 'waiting_manager'})
        return True

    @api.multi
    def action_refuse_manager(self):
        self.write({'state': 'draft'})
        return True

    @api.multi
    def action_refuse_customer(self):
        self.write({'state': 'draft'})
        return True