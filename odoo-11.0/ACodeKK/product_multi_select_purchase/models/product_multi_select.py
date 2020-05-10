from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime

class product_multi_select(models.TransientModel):
    _name = 'product.multi.select.purchase'

    product_ids = fields.Many2many('product.product',string="Products")

    @api.multi
    def add_product_to_line(self):
        for record in self:
            if 'active_id' in self._context:
                purchase_order_id = self.env['purchase.order'].search([('id','=',self._context['active_id'])])
                list_product = []
                date_planned = datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                for product in record.product_ids:
                        list_product.append((0,0,{'product_id': product.id,'product_uom':product.uom_id.id, 'price_unit': product.standard_price, 'product_qty': 1, 'name': product.name, 'date_planned': date_planned}))
                purchase_order_id.write({
                    'order_line': list_product
                })