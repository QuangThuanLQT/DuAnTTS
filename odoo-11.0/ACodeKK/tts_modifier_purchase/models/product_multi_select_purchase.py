from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime


class product_multi_select(models.TransientModel):
    _inherit = 'product.multi.select.purchase'

    @api.multi
    def add_product_to_line(self):
        for record in self:
            if 'active_id' in self._context:
                purchase_order_id = self.env['purchase.order'].search([('id', '=', self._context['active_id'])])
                line_ids = purchase_order_id.order_line.browse([])
                list_product = []
                date_planned = datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                for product in record.product_ids:
                    product_line = {
                        'product_id': product.id,
                        'product_uom': product.uom_id.id,
                        'price_unit': product.standard_price,
                        'product_qty': 1, 'name': product.name,
                        'date_planned': date_planned
                    }
                    line = purchase_order_id.order_line.new(product_line)
                    line.onchange_product_id()
                    line._bill_onchange_quantity()
                    line_ids += line
                purchase_order_id.order_line += line_ids

