# -*- coding: utf-8 -*-


from odoo import fields, models, api, _

class check_sale_purchase(models.TransientModel):
    _name = 'check.sale.purchase'

    sale_order_ids = fields.Many2many('sale.order')
    purchase_order_ids = fields.Many2many('purchase.order')
    start_date = fields.Date(String='Start Date')
    end_date = fields.Date(String='End Date')

    def check_action(self):
        conditions_sale = [('state', '=', 'sale')]
        conditions_purchase = [('state', '=', 'purchase')]
        if self.start_date:
            conditions_sale.append(('date_order', '>=', self.start_date))
            conditions_purchase.append(('date_order', '>=', self.start_date))
        if self.end_date:
            conditions_sale.append(('date_order', '<=', self.end_date))
            conditions_purchase.append(('date_order', '<=', self.end_date))

        purchase_list_lost = []
        purchase_ids = self.env['purchase.order'].search(conditions_purchase)
        for purchase_id in purchase_ids:
            if not purchase_id.invoice_ids.filtered(
                    lambda inv: inv.state != 'cancel') or not purchase_id.picking_ids.filtered(
                lambda p: p.state != 'cancel'):
                purchase_list_lost.append(purchase_id.id)

        sale_list_lost = []
        sale_ids = self.env['sale.order'].search(conditions_sale)
        for sale_id in sale_ids:
            if not sale_id.invoice_ids.filtered(lambda inv: inv.state != 'cancel') or not sale_id.picking_ids.filtered(
                    lambda p: p.state != 'cancel'):
                sale_list_lost.append(sale_id.id)

        self.sale_order_ids = [(6,0,sale_list_lost)]
        self.purchase_order_ids = [(6, 0, purchase_list_lost)]

