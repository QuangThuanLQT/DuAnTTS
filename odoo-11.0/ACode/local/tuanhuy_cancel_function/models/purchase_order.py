# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import UserError


class purchase_order(models.Model):
    _inherit = 'purchase.order'

    cancel_reason = fields.Char(String="Cancel Reason")

    @api.multi
    def button_cancel(self):
        if self.picking_ids:
            self.picking_ids.do_cancel_stock_picking()

        self.write({'state': 'cancel'})
        if self.invoice_ids:
            for invoice in self.invoice_ids:
                if invoice.state == 'paid':
                    if invoice.payment_move_line_ids:
                        for payment in invoice.payment_move_line_ids:
                            payment.with_context(invoice_id=invoice.id).remove_move_reconcile()

                if invoice.state not in ['paid', 'cancel']:
                    if invoice.payment_move_line_ids:
                        for payment in invoice.payment_move_line_ids:
                            payment.with_context(invoice_id=invoice.id).remove_move_reconcile()
                    if invoice.move_id:
                        self._cr.execute(
                            """DELETE FROM account_move_line WHERE move_id=%s""" % (invoice.move_id.id))
                        self._cr.execute("""UPDATE account_invoice SET move_id=NULL WHERE id=%s""" % (invoice.id))
                        self._cr.execute("""DELETE FROM account_move WHERE id=%s""" % (invoice.move_id.id))

                self._cr.execute("""DELETE FROM account_invoice WHERE id=%s""" % (invoice.id))

        for line in self.order_line:
            line.move_ids = None
            line.invoice_lines = None

    @api.multi
    def action_cancel_reason(self):
        return {
            'name': 'Cancel',
            'type': 'ir.actions.act_window',
            'res_model': 'cancel.function.reason',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }