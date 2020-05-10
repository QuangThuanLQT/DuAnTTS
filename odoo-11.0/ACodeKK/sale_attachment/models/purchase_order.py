# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _

class purchase_order(models.Model):
    _inherit = 'purchase.order'

    attachment_ids = fields.One2many('sale.attachment.line', 'purchase_order_id', string="Các đính kèm")

    @api.multi
    def button_confirm(self):
        res = super(purchase_order, self).button_confirm()
        for record in self:
            pickings = record.mapped('picking_ids')
            for picking in pickings:
                for attachment in record.attachment_ids:
                    attachment.picking_id = picking.id
            return res
