# -*- coding: utf-8 -*-

from odoo import models, fields, api

class delivery_carrier(models.Model):
    _inherit = 'delivery.carrier'

    @api.model
    def create(self, values):
        record = super(delivery_carrier, self).create(values)
        return record

    @api.multi
    def write(self, values):
        result = super(delivery_carrier, self).write(values)
        return result

    @api.multi
    def unlink(self):
        return super(delivery_carrier, self).unlink()

class stock_picking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def _add_delivery_cost_to_so(self):
        return True

    @api.model
    def create(self,vals):
        if self.env.context.get('create_from_sale_order',False):
            sale_id =  self.env['sale.order'].browse(self.env.context.get('create_from_sale_order',False))
            if sale_id.note:
                vals.update({'note': sale_id.note or ''})
        res = super(stock_picking, self).create(vals)
        return res