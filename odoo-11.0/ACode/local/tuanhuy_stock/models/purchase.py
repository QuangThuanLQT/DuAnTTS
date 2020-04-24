# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import UserError


class purchase_order(models.Model):
    _inherit = 'purchase.order'

    # @api.multi
    # def button_cancel(self):
    #
    #     for record in self:
    #         if record.state == 'purchase':
    #             new_purchase_order = record.copy()
    #             new_purchase_order.button_confirm()
    #             if new_purchase_order.picking_ids:
    #                 new_purchase_order.picking_ids.filtered(lambda x: x.state == 'assigned').mapped('move_lines').write(
    #                     {'state': 'done'})
    #                 new_purchase_order.picking_ids.filtered(lambda x: x.state == 'assigned').write({'state' : 'done'})
    #
    #                 moves = record.picking_ids.mapped('move_lines').filtered(lambda x: x.state == 'done')
    #                 for move in moves:
    #                     quants = move.quant_ids
    #                     new_moves = new_purchase_order.picking_ids.mapped('move_lines').filtered(lambda x: x.product_id == move.product_id and x.product_uom_qty == move.product_uom_qty)
    #                     if new_moves:
    #                         move.write({'state': 'cancel'});
    #                         quants.write({
    #                             'history_ids': [(4, new_moves[0].id), (2, move.id)],
    #                         })
    #
    #         if self.picking_ids:
    #             picking_type_in = self.env.ref('stock.picking_type_in').id
    #             for picking in self.picking_ids.filtered(lambda p: p.picking_type_id.id == picking_type_in):
    #                 if picking.name not in self.picking_ids.mapped('origin'):
    #                     if picking.state not in ['done', 'cancel']:
    #                         picking.action_cancel()
    #                     else:
    #                         if picking.state != 'cancel':
    #                             popup_obj = self.env['stock.return.picking']
    #                             return_picking_default = popup_obj.with_context({'active_id': picking.id}).default_get(
    #                                 popup_obj._fields)
    #                             if 'product_return_moves' in return_picking_default:
    #                                 order_ids = []
    #                                 for return_line in return_picking_default.get('product_return_moves', False):
    #                                     return_line = return_line[2]
    #                                     move_id = self.env['stock.move'].browse(return_line.get('move_id', False))
    #                                     if move_id.product_uom_qty > return_line.get('quantity', 0):
    #                                         customer_location = self.env.ref('stock.stock_location_customers')
    #                                         for quant_id in move_id.quant_ids.filtered(
    #                                                 lambda q: q.location_id == customer_location):
    #                                             for stock_move_id in quant_id.history_ids.filtered(
    #                                                     lambda q: q.location_dest_id == customer_location):
    #                                                 if stock_move_id.state == 'done' and stock_move_id.sale_order_id and stock_move_id.sale_order_id.id not in order_ids:
    #                                                     order_ids.append(stock_move_id.sale_order_id.id)
    #                                 if order_ids:
    #                                     return {
    #                                         'name': 'Cancel',
    #                                         'type': 'ir.actions.act_window',
    #                                         'res_model': 'sale.order.return.warning',
    #                                         'view_type': 'form',
    #                                         'view_mode': 'form',
    #                                         'target': 'current',
    #                                         'context': {'order_ids': order_ids, },
    #                                     }
    #                             new_picking_id, pick_type_id = popup_obj.with_context({'active_id': picking.id}).create(
    #                                 popup_obj.with_context({'active_id': picking.id}).default_get(
    #                                     popup_obj._fields))._create_returns()
    #                             new_picking_id = self.env['stock.picking'].browse(new_picking_id)
    #                             new_picking_id.do_new_transfer()
    #                             new_picking_id.check_return_picking = True
    #                             new_picking_id.picking_cancel = True
    #                             picking.picking_cancel = True
    #
    #         self.write({'state': 'cancel'})
    #         if self.invoice_ids:
    #             for invoice in self.invoice_ids:
    #                 if invoice.state not in ['paid', 'cancel']:
    #                     if invoice.move_id:
    #                         self._cr.execute(
    #                             """DELETE FROM account_move_line WHERE move_id=%s""" % (invoice.move_id.id))
    #                         self._cr.execute("""UPDATE account_invoice SET move_id=NULL WHERE id=%s""" % (invoice.id))
    #                         self._cr.execute("""DELETE FROM account_move WHERE id=%s""" % (invoice.move_id.id))
    #                     # self._cr.execute("""DELETE FROM account_invoice_line WHERE invoice_id=%s""" % (invoice.id))
    #                     # self._cr.execute("""DELETE FROM account_invoice WHERE id=%s""" % (invoice.id))
    #                     # self._cr.execute("""UPDATE account_invoice SET state = 'cance' WHERE id=%s""" % (invoice.id))
    #
    #                 if invoice.state == 'paid':
    #                     for payment in invoice.payment_ids:
    #                         self._cr.execute("""DELETE FROM account_payment WHERE id=%s""" % (payment.id))
    #                     payment_move_ids = []
    #                     payment_line_move_ids = []
    #                     for payment_move_line_id in invoice.payment_move_line_ids:
    #                         if payment_move_line_id.move_id.id not in payment_move_ids:
    #                             payment_move_ids.append(payment_move_line_id.move_id.id)
    #                             for line_move in payment_move_line_id.move_id.line_ids.ids:
    #                                 payment_line_move_ids.append(line_move)
    #                     account_partial_reconcile_ids = self.env['account.partial.reconcile'].search(
    #                         ['|', ('debit_move_id', 'in', payment_line_move_ids),
    #                          ('credit_move_id', 'in', payment_line_move_ids)])
    #                     account_partial_reconcile_ids.unlink()
    #                     for move_id in payment_move_ids:
    #                         self._cr.execute("""DELETE FROM account_move_line WHERE move_id = %s""" % (move_id))
    #                         self._cr.execute("""DELETE FROM account_move WHERE id = %s""" % (move_id))
    #                     if invoice.move_id:
    #                         self._cr.execute(
    #                             """DELETE FROM account_move_line WHERE move_id=%s""" % (invoice.move_id.id))
    #                         self._cr.execute("""UPDATE account_invoice SET move_id=NULL WHERE id=%s""" % (invoice.id))
    #                         self._cr.execute("""DELETE FROM account_move WHERE id=%s""" % (invoice.move_id.id))
    #                     # self._cr.execute("""DELETE FROM account_invoice_line WHERE invoice_id=%s""" % (invoice.id))
    #                     # self._cr.execute("""DELETE FROM account_invoice WHERE id=%s""" % (invoice.id))
    #                 # invoice.state = 'cancel'
    #
    #                 self._cr.execute("""UPDATE account_invoice SET state='cancel' WHERE id=%s""" % (invoice.id))
    #
    #         for line in self.order_line:
    #             line.move_ids = None
    #             line.invoice_lines = None