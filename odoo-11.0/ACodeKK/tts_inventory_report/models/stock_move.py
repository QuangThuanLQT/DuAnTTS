# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

class stock_move(models.Model):
    _inherit = 'stock.move'

    amount_cost_sale = fields.Float('Gia Von', compute='get_cost_product', store=True)

    @api.depends('state', 'date')
    def get_cost_product(self):
        for record in self:
            if record.state == 'done':
                if record.location_id.usage == 'procurement' and record.location_dest_id.usage == 'internal':
                    if record.picking_id.picking_from_sale_return:
                        if record.picking_id.sale_id.sale_order_return_ids:
                            order_return = record.picking_id.sale_id.sale_order_return_ids[0]
                            if order_return.invoice_ids:
                                invoice_id = order_return.invoice_ids[0]
                                date_order = invoice_id.create_date
                            else:
                                date_order = order_return.confirmation_date
                        else:
                            date_order = record.picking_id.sale_id.confirmation_date
                        amount_cost_sale = record.product_id.get_history_price(record.company_id.id, date_order)
                        record.amount_cost_sale = amount_cost_sale




