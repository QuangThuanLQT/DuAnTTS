from odoo import models, fields, api

class stock_picking(models.Model):
    _inherit = 'stock.picking'

    cancel_reason = fields.Char(String="Cancel Reason",compute='get_cancel_reason')
    picking_cancel = fields.Boolean(default=False)

    @api.depends('sale_id','purchase_id')
    def get_cancel_reason(self):
        for record in self:
            if record.sale_id or record.purchase_id:
                if record.sale_id and record.sale_id.state == 'cancel':
                    record.cancel_reason = record.sale_id.cancel_reason
                elif record.purchase_id and record.purchase_id.state == 'cancel':
                    record.cancel_reason = record.purchase_id.cancel_reason