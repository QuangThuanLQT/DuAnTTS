# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError

import sys

reload(sys)
sys.setdefaultencoding('utf-8')


class import_warning_order(models.TransientModel):
    _name = 'import.warning.order'

    import_warning_product_lost_ids = fields.One2many('import.warning.product.lost', 'import_warning_id')
    import_warning_price_diff_ids = fields.One2many('import.warning.price.diff', 'import_warning_id')
    import_warning_res_partner = fields.One2many('import.warning.res.partner', 'import_warning_id')
    check_product_lost_ids = fields.Boolean(default=False)
    check_price_diff_ids = fields.Boolean(default=False)
    check_res_partner = fields.Boolean(default=False)

    name_action = fields.Char()
    name_model = fields.Char()

    def update_product_to_invoice(self):
        # product_ids = self.env['product.template'].search([('invoice_policy','!=','order')])
        # for product_id in product_ids:
        #     product_id.invoice_policy = 'order'
        account_move_ids = self.env['account.move'].search([('journal_id', '=', 1)])
        count = 0
        for acc_move_id in account_move_ids:
            inv_id = self.env['account.invoice'].search(
                ['|', ('number', '=', acc_move_id.name), ('move_id', '=', acc_move_id.id)])
            if not inv_id:
                voucher_id = self.env['account.voucher'].search(
                    ['|', ('number', '=', acc_move_id.name), ('move_id', '=', acc_move_id.id)])
                if not voucher_id:
                    count += 1
                    print
                    "STT:" + str(count) + " Account Move: " + str(acc_move_id.id) + " - " + acc_move_id.name
        print
        "---------------" + str(count)

    def update_date_account_move(self):
        purchase_ids = self.env['purchase.order'].search([('purchase_order_return', '=', False)])

    def update_tax_sale_order(self):
        sale_order_ids = self.env['sale.order'].search([])
        for sale_order_id in sale_order_ids:
            if any(tax.type_tax_use == 'purchase' for tax in sale_order_id.mapped('order_line').mapped('tax_id')):
                for line in sale_order_id.order_line:
                    line.onchange_tax_sub()
                sale_order_id.with_context({'active_ids': sale_order_id.ids}).multi_update_account_invoice()

    def update_invoice_status_for_so_po(self):
        sale_order_ids = self.env['sale.order'].search(
            [('state', '!=', 'draft'), ('invoice_status', '=', 'to invoice')])
        for sale_order_id in sale_order_ids:
            for line in sale_order_id.order_line:
                line._compute_invoice_status()
                if sale_order_id.id == 1400:
                    print
                    line.invoice_status
            sale_order_id._get_invoiced()
        purchase_ids = self.env['sale.order'].search(
            [('state', '!=', 'draft'), ('invoice_status', '=', 'to invoice')])
        for purchase_id in purchase_ids:
            purchase_id._get_invoiced()

    def update_ref_acount_move(self):
        account_voucher_ids = self.env['account.voucher'].search([])
        for account_voucher_id in account_voucher_ids:
            if account_voucher_id.move_id:
                account_voucher_id.move_id.ref = account_voucher_id.number_voucher
        invoice_ids = self.env['account.invoice'].search([])
        for invoice_id in invoice_ids:
            if invoice_id.move_id:
                invoice_id.move_id.ref = invoice_id.origin

    def update_price_so_to_in(self):
        sale_order_ids = self.env['sale.order'].search([('state', '!=', 'draft')])
        count = 1
        for order_id in sale_order_ids:
            # for line in order_id.order_line:
            #     price_unit = line.price_discount * 100 / (100 - line.discount) if (100 - line.discount) != 0 else 0
            #     if price_unit != line.price_unit and line.price_discount != 0:
            #         print "count: %s-Gia Dung: %s-Gia: %s-CK: %s-Gia Da CK: %s"%(order_id.id,price_unit,line.price_unit,line.discount,line.price_discount)
            #         count += 1
            if order_id.invoice_ids and order_id.amount_total != sum(order_id.invoice_ids.mapped('amount_total')):
                for invoice in order_id.invoice_ids:
                    for line in order_id.invoice_ids.invoice_line_ids:
                        line._compute_price()
                print
                "--------------------------%s-%s-%s" % (
                order_id.id, order_id.amount_total, sum(order_id.invoice_ids.mapped('amount_total')))

    def update_name_sale_return(self):
        sale_return_ids = self.env['sale.order'].search([('sale_order_return', '=', True)], order="id ASC")
        for sale_return_id in sale_return_ids:
            sale_return_id.name = self.env['ir.sequence'].next_by_code('sale.order.return') or _('New')

    def update_name_po(self):
        purchase_ids = self.env['purchase.order'].search([])
        for purchase_id in purchase_ids:
            if purchase_id.notes:
                purchase_id.name = purchase_id.notes
            if purchase_id.date_order:
                date = purchase_id.date_order.split(' ')[0] + " 00:30:00"
                date = datetime.strptime(date, DEFAULT_SERVER_DATETIME_FORMAT)
                purchase_id.date_order = date
                purchase_id.date_planned = date
                for line in purchase_id.order_line:
                    line.date_planned = date

    def update_name_so(self):
        picking_ids = self.env['stock.picking'].search([('state', '=', 'assigned')]).filtered(
            lambda p: 'WH/IN' in p.name)
        count = 0
        for picking in picking_ids:
            for line in picking.pack_operation_product_ids:
                line.qty_done = line.product_qty
            picking.do_new_transfer()
            count += 1
            print
            "----------------------------%s" % count

        # product_ids = self.env['product.template'].browse([52287,52282,52288,52281,52283,52284,52285,52286]).mapped('product_variant_id')
        # for product_id in product_ids:
        #     string = ['INV:update số lượng chuyển từ bộ sang cái SIBA','INV:Tồn Kho Đầu Kỳ']
        #     aml_ids = self.env['account.move.line'].search([('product_id','=',product_id.id),('name','in',string)])
        #     for aml_id in aml_ids:
        #         if aml_id.credit:
        #             self._cr.execute("""UPDATE account_move_line SET credit=%s,reconcile_number=%s WHERE id=%s""" % (product_id.standard_price*aml_id.quantity,-product_id.standard_price*aml_id.quantity,aml_id.id))
        #         if aml_id.debit:
        #             self._cr.execute("""UPDATE account_move_line SET debit=%s,reconcile_number=%s WHERE id=%s""" % (product_id.standard_price*aml_id.quantity,product_id.standard_price*aml_id.quantity,aml_id.id))

    @api.multi
    def auto_create_invoice(self):
        sale_ids = self.env['sale.order'].search([]).filtered(lambda record: record.state != 'done' and all(
            [do.state == 'assigned' for do in record.picking_ids]) and not record.invoice_ids)
        count = 1
        for order in sale_ids:
            print
            "------------------" + str(count)
            popup_obj = self.env['sale.advance.payment.inv']
            try:
                for picking in order.picking_ids:
                    for line in picking.pack_operation_product_ids:
                        line.qty_done = line.product_qty
                    picking.do_new_transfer()
                popup_obj.create(popup_obj.default_get(popup_obj._fields)).with_context(
                    {'active_ids': order.ids}).create_invoices()
                count += 1
            except:
                continue

    def update_order_date(self):
        sale_ids = self.env['sale.order'].search([])
        for record in sale_ids:
            if record.invoice_ids:
                for inv in record.invoice_ids:
                    date_order = datetime.strptime(record.date_order, DEFAULT_SERVER_DATETIME_FORMAT).strftime(
                        DEFAULT_SERVER_DATE_FORMAT)
                    self._cr.execute("""UPDATE account_invoice SET date_order='%s', date_invoice='%s'
                                                                            WHERE id=%s""" % (
                        date_order, date_order, inv.id))
        purchase_ids = self.env['purchase.order'].search([])
        for purchase in purchase_ids:
            for purchase_inv in purchase.invoice_ids:
                date_order = datetime.strptime(purchase.date_order, DEFAULT_SERVER_DATETIME_FORMAT).strftime(
                    DEFAULT_SERVER_DATE_FORMAT)
                self._cr.execute("""UPDATE account_invoice SET date_invoice='%s', date_due='%s',date='%s'
                                                                                            WHERE id=%s""" % (
                    date_order, date_order, date_order, purchase_inv.id))

    # def update_name_so(self):
    #     sale_ids = self.env['sale.order'].search([('state','=','sale')])
    #     count = 0
    #     for sale_id in sale_ids:
    #         sale_id.confirmation_date = sale_id.date_order
    #         # if sale_id.origin:
    #         #     sale_id.name = sale_id.origin
    #         # if sale_id.date_order:
    #         #     date = sale_id.date_order.split(' ')[0] + " 00:30:00"
    #         #     date = datetime.strptime(date,DEFAULT_SERVER_DATETIME_FORMAT)
    #         #     sale_id.date_order = date
    #         #     sale_id.action_confirm()
    #         #     if sale_id.picking_ids:
    #         #         for picking in sale_id.picking_ids:
    #         #             picking.min_date = date
    #             #         for line in picking.pack_operation_product_ids:
    #             #             line.qty_done = line.product_qty
    #             #         picking.do_new_transfer()
    #         count +=1
    #         print "----------------------------%s" % count

    @api.model
    def default_get(self, fields):
        res = super(import_warning_order, self).default_get(fields)
        if 'name_action' in self._context:
            res['name_action'] = self._context.get('name_action')
        if 'name_model' in self._context:
            res['name_model'] = self._context.get('name_model')
        if 'data' in self._context:
            data_line = []
            data = self._context.get('data')
            for line_product in data.get('product_not_find'):
                data_line.append((0, 0, line_product))
            if data_line:
                res['check_product_lost_ids'] = True
                res['import_warning_product_lost_ids'] = data_line

            data_line = []
            for line_price in data.get('price_not_sync'):
                data_line.append((0, 0, line_price))
            if data_line:
                res['check_price_diff_ids'] = True
                res['import_warning_price_diff_ids'] = data_line

            data_line = []
            for line_price in data.get('customer_not_find'):
                data_line.append((0, 0, line_price))
            if data_line:
                res['check_res_partner'] = True
                res['import_warning_res_partner'] = data_line

        return res

    @api.multi
    def action_cancel(self):
        name = ""
        if 'name' in self._context:
            name = self._context.get('name')
        return {
            'name': self.name_action,
            'type': 'ir.actions.act_window',
            'res_model': self.name_model,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'import_data': self._context.get('import_data'),
                'name': name,
            }
        }


class import_warning_product_lost(models.TransientModel):
    _name = 'import.warning.product.lost'

    line = fields.Char(string='Line')
    default_code = fields.Char(string='Default Code')
    import_warning_id = fields.Many2one('import.warning.order')


class import_warning_res_partner(models.TransientModel):
    _name = 'import.warning.res.partner'

    line = fields.Char(string='Line')
    customer_name = fields.Char(string='Partner Name')
    import_warning_id = fields.Many2one('import.warning.order')


class import_warning_price_diff(models.TransientModel):
    _name = 'import.warning.price.diff'

    line = fields.Char(string='Line')
    default_code = fields.Char(string='Default Code')
    import_warning_id = fields.Many2one('import.warning.order')


class update_by_sql(models.TransientModel):
    _name = "update.by.sql"

    sql_text = fields.Text(string="SQL text")

    def action_run(self):
        try:
            self._cr.execute(self.sql_text)
        except:
            raise UserError('Error')
