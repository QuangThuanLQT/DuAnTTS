# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import UserError

class cancel_function_reason(models.TransientModel):
    _name = 'cancel.function.reason'

    reason = fields.Char(required=True)

    def action_cancel(self):
        ctx = self._context
        if 'active_model' in ctx and 'active_id' in ctx:
            if ctx.get('active_model') == 'purchase.order':
                purchase_order_id = self.env['purchase.order'].search([('id', '=', ctx.get('active_id'))], limit=1)
                if purchase_order_id:
                    purchase_order_id.cancel_reason = self.reason
                    purchase_order_id.button_cancel()

            if ctx.get('active_model') == 'sale.order':
                sale_order_id = self.env['sale.order'].search([('id', '=', ctx.get('active_id'))], limit=1)
                if sale_order_id:
                    sale_order_id.cancel_reason = self.reason
                    sale_order_id.action_cancel()
        else:
            if 'params' in ctx and 'model' in ctx.get('params') and 'id' in ctx.get('params'):
                if ctx.get('params').get('model') == 'sale.order':
                    sale_order_id = self.env['sale.order'].search([('id','=',ctx.get('params').get('id'))],limit=1)
                    if sale_order_id:
                        sale_order_id.cancel_reason = self.reason
                        sale_order_id.action_cancel()
                if ctx.get('params').get('model') == 'purchase.order':
                    purchase_order_id = self.env['purchase.order'].search([('id','=',ctx.get('params').get('id'))],limit=1)
                    if purchase_order_id:
                        purchase_order_id.cancel_reason = self.reason
                        purchase_order_id.button_cancel()

class sale_order_need_return(models.TransientModel):
    _name = "sale.order.return.warning"

    return_warning_line_ids = fields.One2many('sale.order.return.warning.line','return_warning_id')

    @api.model
    def default_get(self, fields):
        res = super(sale_order_need_return, self).default_get(fields)
        line_data = [(6,0,[])]
        if 'order_ids' in self._context:
            for order_id in self._context.get('order_ids'):
                line_data.append((0,0,{'sale_order_id':order_id}))
        res['return_warning_line_ids'] = line_data
        return res

class sale_order_need_return_line(models.TransientModel):
    _name = "sale.order.return.warning.line"

    sale_order_id = fields.Many2one('sale.order',string="Sale Order")
    return_warning_id = fields.Many2one('sale.order.return.warning')

    @api.model
    def sale_order_action_cancel(self):
        self.sale_order_id.action_cancel()

