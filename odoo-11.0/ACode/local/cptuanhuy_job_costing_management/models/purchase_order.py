from odoo import models, fields, api

class purchase_order_wizard(models.TransientModel):
    _inherit = 'purchase.order.wizard'

    @api.multi
    def create_purchase_requistion(self):
        res = super(purchase_order_wizard, self).create_purchase_requistion()
        picking = self.env['stock.picking'].browse(self._context.get('active_ids', []))
        for purchase in picking[0].purchase_order_ids:
            purchase.button_dummy()
        return res