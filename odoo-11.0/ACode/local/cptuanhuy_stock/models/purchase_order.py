from odoo import models, fields, api

class purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'

    @api.multi
    def _prepare_stock_moves(self, picking):
        res = super(purchase_order_line, self)._prepare_stock_moves(picking)
        for index in range(len(res)):
            if res[index].get('purchase_line_id',False):
                line_id = self.env['purchase.order.line'].browse(res[index].get('purchase_line_id',False))
                if line_id and line_id.sale_id:
                    res[index].update({'sale_stock_out_id' : line_id.sale_id.id or False})
        return res
