# -*- coding: utf-8 -*-

from odoo import models, fields, api
import base64
from xlrd import open_workbook
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare
import StringIO
import xlsxwriter
from collections import defaultdict
from datetime import datetime


class account_invoice_inherit(models.Model):
    _inherit = 'account.invoice'

    def _prepare_invoice_line_from_po_line(self, line):
        if line.product_id.purchase_method == 'purchase':
            qty = line.product_qty - line.qty_invoiced
        else:
            qty = line.qty_received - line.qty_invoiced
        if float_compare(qty, 0.0, precision_rounding=line.product_uom.rounding) <= 0:
            qty = 0.0
        taxes = line.taxes_id
        invoice_line_tax_ids = line.order_id.fiscal_position_id.map_tax(taxes)
        invoice_line = self.env['account.invoice.line']
        price_unit = line.order_id.currency_id.with_context(date=self.date_invoice).compute(line.price_unit, self.currency_id, round=False)
        if line.price_discount:
            if line.discount == 100:
                price_unit = line.price_discount
            else:
                price_unit = line.price_discount*100/(100-line.discount)
        data = {
            'purchase_line_id': line.id,
            'name': line.order_id.name+': '+line.name,
            'origin': line.order_id.origin,
            'uom_id': line.product_uom.id,
            'product_id': line.product_id.id,
            'account_id': invoice_line.with_context({'journal_id': self.journal_id.id, 'type': 'in_invoice'})._default_account(),
            'price_unit': price_unit,
            'quantity': qty,
            'discount': line.discount,
            'price_discount': line.price_discount,
            'account_analytic_id': line.account_analytic_id.id,
            'analytic_tag_ids': line.analytic_tag_ids.ids,
            'invoice_line_tax_ids': invoice_line_tax_ids.ids
        }
        account = invoice_line.get_invoice_line_account('in_invoice', line.product_id, line.order_id.fiscal_position_id, self.env.user.company_id)
        if account:
            data['account_id'] = account.id
        return data

class purchase_order(models.Model):
    _inherit = 'purchase.order'

    tax_id = fields.Many2one('account.tax', 'Tax', domain=[('type_tax_use', '=', 'purchase')])
    import_data = fields.Binary(string="Tập tin")
    check_box_co_cq = fields.Boolean(default=False, string="CO, CQ")
    check_box_invoice_gtgt = fields.Boolean(default=False, string="Invoice GTGT")
    invoice_date_real = fields.Date('Invoice Date Real')
    invoice_number_real = fields.Char('Invoice Number Real')
    check_color_picking = fields.Boolean(compute="_check_color_picking", default=False)
    total_text = fields.Char('Total Text', compute='_compute_total')
    record_checked = fields.Boolean('Checked')
    delivery_status = fields.Selection([
        ('draft', 'Draft'), ('cancel', 'Cancelled'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting Availability'),
        ('partially_available', 'Partially Available'),
        ('cancel', 'Đã Huỷ'),
        ('assigned', 'Open'), ('done', 'Done')], string='Delivery Status', compute='_compute_delivery_status')
    product_code = fields.Char('Product code')
    invoice_status = fields.Selection([
        ('no', 'Nothing to Bill'),
        ('to invoice', 'Waiting Bills'),
        ('invoiced', 'Bills Received'),
        ('cancel', 'Hoá Đơn Huỷ')
    ], string='Billing Status', compute='_get_invoiced', store=True, readonly=True, copy=False, default='no')
    invoice_number_total_real = fields.Char(string='Số hoá đơn thực', compute='get_invoice_number_total_real')
    user_id = fields.Many2one('res.users', string='Purchaseperson', index=True, track_visibility='onchange',
                              default=lambda self: self.env.user)
    @api.multi
    def get_invoice_number_total_real(self):
        for record in self:
            name = ', '.join(
                (invoice.invoice_number_real or '') + ' - ' + str(invoice.invoice_total_real) for invoice in
                record.invoice_ids)
            record.invoice_number_total_real = name

    @api.depends('state', 'order_line.qty_invoiced', 'order_line.qty_received', 'order_line.product_qty')
    def _get_invoiced(self):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for order in self:
            if order.state not in ('purchase', 'done'):
                order.invoice_status = 'no'
                continue

            if any(float_compare(line.qty_invoiced,
                                 line.product_qty if line.product_id.purchase_method == 'purchase' else line.qty_received,
                                 precision_digits=precision) == -1 for line in order.order_line):
                order.invoice_status = 'to invoice'
            elif all(float_compare(line.qty_invoiced,
                                   line.product_qty if line.product_id.purchase_method == 'purchase' else line.qty_received,
                                   precision_digits=precision) >= 0 for line in order.order_line) and order.invoice_ids:
                order.invoice_status = 'invoiced'
            else:
                order.invoice_status = 'no'
            if order.invoice_ids and all(invoice.state == 'cancel' for invoice in order.invoice_ids):
                    order.invoice_status = 'cancel'

    @api.depends('order_line.price_total')
    def _amount_all(self):
        return True
        # for order in self:
        #     amount_untaxed = amount_tax = amount_discount = 0.0
        #     for line in order.order_line:
        #         amount_untaxed += line.price_subtotal
        #         # FORWARDPORT UP TO 10.0
        #         if order.company_id.tax_calculation_rounding_method == 'round_globally':
        #             taxes = line.taxes_id.compute_all(line.price_unit, line.order_id.currency_id, line.product_qty,
        #                                               product=line.product_id, partner=line.order_id.partner_id)
        #             amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
        #         else:
        #             amount_tax += line.price_tax
        #         if line.price_discount:
        #             amount_discount += (line.product_qty * (line.price_unit - line.price_discount))
        #         else:
        #             amount_discount += (line.product_qty * line.price_unit * line.discount) / 100
        #     order.update({
        #         'amount_untaxed': order.currency_id.round(amount_untaxed),
        #         'amount_tax': order.currency_id.round(amount_tax),
        #         'amount_discount': order.currency_id.round(amount_discount),
        #         'amount_total': amount_untaxed + amount_tax,
        #     })

    @api.multi
    def button_dummy(self):

        self.supply_rate()

        for line in self.order_line:
            if line.price_discount:
                price = line.price_discount
                taxes_id = line.taxes_id
            else:
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                taxes_id = line.taxes_id

            taxes = taxes_id.compute_all(price, line.order_id.currency_id, line.product_qty,
                                              product=line.product_id, partner=line.order_id.partner_id)
            line.write({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

        for order in self:
            amount_untaxed = amount_tax = amount_discount = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                # FORWARDPORT UP TO 10.0
                if order.company_id.tax_calculation_rounding_method == 'round_globally':
                    taxes = line.taxes_id.compute_all(line.price_unit, line.order_id.currency_id, line.product_qty,
                                                      product=line.product_id, partner=line.order_id.partner_id)
                    amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                else:
                    amount_tax += line.price_tax
                if line.price_discount:
                    amount_discount += (line.product_qty * (line.price_unit - line.price_discount))
                else:
                    amount_discount += (line.product_qty * line.price_unit * line.discount) / 100
            order.write({
                'amount_untaxed': order.currency_id.round(amount_untaxed),
                'amount_tax': order.currency_id.round(amount_tax),
                'amount_discount': order.currency_id.round(amount_discount),
                'amount_total': amount_untaxed + amount_tax,
            })


    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        for do in domain:
            if 'product_id' in do and 'ilike' in do:
                product_code = do[2].split()
                ids = []
                for code in product_code:
                    move_ids = self.search([('product_id', 'ilike', code)]).ids
                    ids += move_ids
                domain.remove(do)
                do_sub = ('id', 'in', ids)
                domain.append(do_sub)
        if self.env.context.get('summaries', False):
            if 'purchase_order_return' not in fields:
                fields.append('purchase_order_return')
            res = super(purchase_order, self).search_read(domain=domain, fields=fields, offset=offset,
                                                               limit=limit, order=order)

            def convertVals(x):
                if x.get('purchase_order_return', False):
                    x['amount_untaxed'] = -x['amount_untaxed']
                    x['amount_total'] = -x['amount_total']
                return x

            res = map(lambda x: convertVals(x), res)
            return res
        return super(purchase_order, self).search_read(domain=domain, fields=fields, offset=offset,
                                                            limit=limit, order=order)

    @api.onchange('date_order')
    def on_change_date_order(self):
        if self.date_order:
            self.date_planned = self.date_order
            for line in self.order_line:
                line.date_planned = self.date_order

    @api.onchange('product_code')
    def on_onchange_product_code(self):
        if self.product_code:
            default_code = self.product_code
            product = self.env['product.product'].search(
                ['|', ('default_code', '=', default_code), ('barcode', '=', default_code)])
            if not product:
                product_barcode_id = self.env['product.barcode'].search([('name', '=', default_code)])
                if product_barcode_id:
                    product = product_barcode_id.product_id.product_variant_id
            if product:
                corresponding_line = self.order_line.filtered(lambda r: r.product_id == product)
                if corresponding_line:
                    corresponding_line[0].product_qty += 1
                else:
                    line = self.order_line.new({
                        'product_id': product.id,
                        'product_uom': product.uom_id.id,
                        'product_uom_qty': 1.0,
                        'price_unit': product.lst_price,
                    })
                    line.onchange_product_id()
                    self.order_line += line
            self.product_code = False
            return
    @api.multi
    def button_confirm(self):
        res = super(purchase_order, self).button_confirm()
        for picking in self.picking_ids:
            picking.note = self.notes
        # if any(line.price_subtotal == 0 for line in self.order_line):
        #     raise UserError("Sản phẩm phải có giá ít nhất là 1đ")
        return res

    @api.model
    def _prepare_picking(self):
        res = super(purchase_order, self)._prepare_picking()
        res['note'] = self.notes
        return res

    @api.multi
    def multi_create_picking(self):
        ids = self.env.context.get('active_ids', [])
        purchase_order_ids = self.browse(ids)
        for purchase_order_id in purchase_order_ids:
            if not purchase_order_id.picking_ids.filtered(lambda p:p.state != 'cancel'):
                purchase_order_id._create_picking()

        # return True


    def multi_update_stock_picking(self):
        ids = self.env.context.get('active_ids', [])
        purchase_order_ids = self.browse(ids)
        for purchase_order_id in purchase_order_ids:
            purchase_order_id.update_stock_picking()
            print "--------------------" + str(purchase_order_id.id)

    def update_stock_picking(self):
        for line in self.order_line:
            for move_id in line.move_ids:
                move_id.price_unit = line.price_discount or line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                for quant_id in move_id.quant_ids:
                    quant_id.cost = line.price_discount or line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                move_id.quant_ids.with_context({'update_account_move_wh_in':False}).get_account_for_move(move_id)
                stock_cus_location = self.env.ref('stock.stock_location_customers').id
                quant_purchase_ids = move_id.quant_ids.filtered(lambda q:q.location_id.id == stock_cus_location)
                for quant_purchase_id in quant_purchase_ids:
                    account_move_sale_ids = quant_purchase_id.history_ids.filtered(lambda ac:'WH/OUT' in ac.picking_id.name)
                    for account_move_sale in account_move_sale_ids:
                        account_move_sale.quant_ids.with_context({'update_account_move_wh_out':False}).get_account_for_move(account_move_sale)

    @api.multi
    def update_stock_picking_po(self):
        ids = self.env.context.get('active_ids', [])
        orders = self.browse(ids)
        for order in orders:
            # Cancel stock picking
            # TODO: Need to recheck this
            for picking_id in order.picking_ids:
                if picking_id.state in ['draft', 'confirmed']:
                    new_picking_id = picking_id.copy()
                    picking_id.do_cancel_stock_picking()
                    self._cr.execute("""DELETE FROM stock_picking WHERE id=%s""" % (picking_id.id))
                    new_picking_id.do_unreserve()
                    continue
                if picking_id.state in ['partially_available', 'assigned']:
                    new_picking_id = picking_id.copy()
                    picking_id.do_cancel_stock_picking()
                    self._cr.execute("""DELETE FROM stock_picking WHERE id=%s""" % (picking_id.id))
                    new_picking_id.action_assign()
                    continue
                if picking_id.state == 'done':
                    new_invoice_id = picking_id.copy()
                    picking_id.do_cancel_stock_picking()
                    self._cr.execute("""DELETE FROM stock_picking WHERE id=%s""" % (picking_id.id))
                    new_invoice_id.force_assign()
                    new_invoice_id.do_new_transfer()
            # Cancel invoice
            for invoice in order.invoice_ids:
                if invoice.state not in ['paid', 'cancel']:
                    if invoice.move_id:
                        self._cr.execute("""DELETE FROM account_move_line WHERE move_id=%s""" % (invoice.move_id.id))
                        self._cr.execute("""UPDATE account_invoice SET move_id=NULL WHERE id=%s""" % (invoice.id))
                        self._cr.execute("""DELETE FROM account_move WHERE id=%s""" % (invoice.move_id.id))

                if invoice.state == 'paid':
                    for payment in invoice.payment_ids:
                        self._cr.execute("""DELETE FROM account_payment WHERE id=%s""" % (payment.id))
                    payment_move_ids = []
                    payment_line_move_ids = []
                    for payment_move_line_id in invoice.payment_move_line_ids:
                        if payment_move_line_id.move_id.id not in payment_move_ids:
                            payment_move_ids.append(payment_move_line_id.move_id.id)
                            for line_move in payment_move_line_id.move_id.line_ids.ids:
                                payment_line_move_ids.append(line_move)
                    account_partial_reconcile_ids = self.env['account.partial.reconcile'].search(
                        ['|', ('debit_move_id', 'in', payment_line_move_ids),
                         ('credit_move_id', 'in', payment_line_move_ids)])
                    account_partial_reconcile_ids.unlink()
                    for move_id in payment_move_ids:
                        self._cr.execute("""DELETE FROM account_move_line WHERE move_id = %s""" % (move_id))
                        self._cr.execute("""DELETE FROM account_move WHERE id = %s""" % (move_id))
                    if invoice.move_id:
                        self._cr.execute("""DELETE FROM account_move_line WHERE move_id=%s""" % (invoice.move_id.id))
                        self._cr.execute("""UPDATE account_invoice SET move_id=NULL WHERE id=%s""" % (invoice.id))
                        self._cr.execute("""DELETE FROM account_move WHERE id=%s""" % (invoice.move_id.id))

                self._cr.execute("""UPDATE account_invoice SET state='cancel' WHERE id=%s""" % (invoice.id))

    @api.multi
    def multi_update_account_invoice(self):
        ids = self.env.context.get('active_ids', [])
        purchase_order_ids = self.browse(ids)
        for purchase_order_id in purchase_order_ids:
            for invoice_id in purchase_order_id.invoice_ids:
                if invoice_id.state == 'draft':
                    print "----------------" + str(purchase_order_id.id)
                if invoice_id.state == 'open':
                    if invoice_id.move_id and datetime.strptime(purchase_order_id.date_order,DEFAULT_SERVER_DATETIME_FORMAT).date() != datetime.strptime(invoice_id.move_id.date,DEFAULT_SERVER_DATE_FORMAT).date():
                        self._cr.execute("""UPDATE account_move SET date='%s' WHERE id=%s""" % (
                        datetime.strptime(purchase_order_id.date_order, DEFAULT_SERVER_DATETIME_FORMAT).strftime(
                            DEFAULT_SERVER_DATE_FORMAT)
                        , invoice_id.move_id.id))
                        for move_line in invoice_id.move_id.line_ids:
                            self._cr.execute("""UPDATE account_move_line SET date='%s' WHERE id=%s""" % (datetime.strptime(purchase_order_id.date_order,DEFAULT_SERVER_DATETIME_FORMAT).strftime(DEFAULT_SERVER_DATE_FORMAT)
                            , move_line.id))
                            print "----------------" + str(purchase_order_id.id)
            if purchase_order_id.amount_total > 0 and purchase_order_id.invoice_ids and (purchase_order_id.amount_total != sum(purchase_order_id.invoice_ids.mapped('amount_total')) or any(
                        product_id not in purchase_order_id.invoice_ids.mapped('invoice_line_ids').mapped('product_id')
                        for product_id in purchase_order_id.order_line.mapped('product_id'))):
                if purchase_order_id.invoice_ids and all(invoice.state in ['draft','open'] for invoice in purchase_order_id.invoice_ids):
                    invoice_line_ids = purchase_order_id.invoice_ids.mapped('invoice_line_ids')
                    for invoice_line_id in invoice_line_ids:
                        purchase_line_id = invoice_line_id.purchase_line_id
                        if purchase_line_id:
                            invoice_line_id.write({
                                'quantity': purchase_line_id.product_qty,
                                'discount': purchase_line_id.discount,
                                'price_unit': purchase_line_id.price_unit,
                                'price_discount' : purchase_line_id.price_discount,
                                'invoice_line_tax_ids': [(6, 0, purchase_line_id.taxes_id.ids)],
                            })
                            invoice_line_id._compute_price()
                            if purchase_line_id.product_id != purchase_line_id.product_id:
                                invoice_line_id.product_id = purchase_line_id.product_id
                                invoice_line_id.name = purchase_line_id.name
                    if len(purchase_order_id.order_line) > len(invoice_line_ids):
                        if not purchase_order_id.purchase_order_return:
                            new_lines = self.env['account.invoice.line']
                            for line in (purchase_order_id.order_line - invoice_line_ids.mapped('purchase_line_id')):
                                data = purchase_order_id.invoice_ids._prepare_invoice_line_from_po_line(line)
                                data['quantity'] = line.product_qty
                                new_line = new_lines.new(data)
                                new_lines += new_line
                            purchase_order_id.invoice_ids[0].invoice_line_ids += new_lines
                        else:
                            new_lines = self.env['account.invoice.line']
                            for line in (
                                purchase_order_id.order_line - invoice_line_ids.mapped('purchase_line_id')):
                                account_id = self.env['account.account'].search([('code', '=', '3388')],
                                                                                limit=1).id or False
                                if line.product_id or line.quantity != 0:
                                    data = {
                                        'product_id': line.product_id.id,
                                        'quantity': line.product_qty,
                                        'uom_id': line.product_uom.id,
                                        'price_unit': line.price_unit,
                                        'price_discount': line.price_discount,
                                        'discount': line.discount,
                                        'invoice_line_tax_ids': [(6, 0, line.taxes_id.ids)],
                                        'name': line.product_id.display_name,
                                        'account_id': line.product_id.categ_id.property_account_expense_categ_id.id or account_id,
                                        'purchase_line_id': line.id,
                                    }
                                    data['quantity'] = line.product_qty
                                    new_line = new_lines.new(data)
                                    new_lines += new_line
                            purchase_order_id.invoice_ids[0].invoice_line_ids += new_lines

                    purchase_order_id.invoice_ids.compute_taxes()
            check_diff = float_compare(
                sum(purchase_order_id.invoice_ids.mapped('move_id').mapped('line_ids').mapped('credit')),
                purchase_order_id.amount_total, precision_digits=2)
            if purchase_order_id.amount_total > 0 and purchase_order_id.invoice_ids.filtered(
                    lambda inv: inv.move_id) and check_diff != 0:
                for invoice_id in purchase_order_id.invoice_ids.filtered(lambda inv: inv.state == 'open'):
                    move_line = self.env['account.move.line']
                    line_not_ext = self.env['account.move.line']
                    move_line_data = invoice_id.get_move_line_from_inv()
                    for line_data in move_line_data:
                        line_data = line_data[2]
                        move_line_change = (invoice_id.move_id.mapped('line_ids') - move_line).filtered(lambda mvl: mvl.product_id.id == line_data.get('product_id',False)
                         and mvl.account_id.id == line_data.get('account_id',False))
                        if move_line_change:
                            for line in move_line_change:
                                if line.id not in line_not_ext.ids:
                                    line_not_ext += line
                                if line.credit != line_data.get('credit',0) or line.debit != line_data.get('debit', 0):
                                    self._cr.execute("""UPDATE account_move_line SET credit=%s, debit=%s
                                                    WHERE id=%s"""%(line_data.get('credit', 0) or 0, line_data.get('debit', 0) or 0, line.id))
                                    self._cr.commit()
                                    move_line += line
                                    line.update_open_amount_residual()
                                    break
                        else:
                            script = """INSERT INTO account_move_line (name, invoice_id, tax_line_id, credit,product_uom_id,currency_id,product_id,debit
                                                      ,amount_currency,quantity,partner_id,account_id,move_id,date_maturity)
                                                             VALUES ('%s',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'%s')"""%(line_data['name'],
                                line_data['invoice_id'],line_data['tax_line_id'] or 'NULL',line_data['credit'] or 0,line_data['product_uom_id'] or 'NULL',line_data['currency_id'] or 'NULL',line_data['product_id'] or 'NULL',
                                        line_data['debit'] or 0,line_data['amount_currency'] or 0,line_data['quantity'] or 0,
                                        line_data['partner_id'],line_data['account_id'],invoice_id.move_id.id,fields.Date.context_today(self))
                            self._cr.execute(script)
                            self._cr.commit()
                    for line_remove in (invoice_id.move_id.mapped('line_ids') - line_not_ext):
                        self._cr.execute("""DELETE FROM account_move_line WHERE id=%s""" % (line_remove.id))
                    if invoice_id.payments_widget == 'false':
                        invoice_id.residual = invoice_id.amount_total
                    else:
                        raise UserError("Bạn không thể cập nhật hoá đơn đã thanh toán một phần: %s từ đơn hàng %s"%(invoice_id.number,purchase_order_id.name))

    @api.multi
    def multi_create_account_invoice(self):
        ids = self.env.context.get('active_ids', [])
        purchase_order_ids = self.browse(ids)
        for purchase_order_id in purchase_order_ids:
            if not purchase_order_id.invoice_ids.filtered(lambda inv:inv.state != 'cancel') and purchase_order_id.amount_total != 0:
                purchase_order_id.create_invoice_show_view()


    @api.depends('picking_ids')
    def _compute_delivery_status(self):
        for record in self:
            if len(record.picking_ids) == 1:
                record.delivery_status = record.picking_ids.state
            elif len(record.picking_ids) > 1:
                record.delivery_status = record.picking_ids.filtered(lambda t: t.state != 'done')[0].state if record.picking_ids.filtered(lambda t: t.state != 'done') else 'done'

    def bt_action_create_invoice(self):
        journal_domain = [
            ('type', '=', 'purchase'),
            ('company_id', '=', self.company_id.id),
            ('currency_id', '=', self.currency_id.id),
        ]
        default_journal_id = self.env['account.journal'].search(journal_domain, limit=1)
        data_invoice = {
            'partner_id' : self.partner_id.id,
            'type'       : 'in_invoice',
            'purchase_id': self.id,
            'origin'     : self.name,
            'date_invoice':self.date_order,
            'date_due': self.date_order,
            'date': self.date_order,
        }
        if default_journal_id:
            data_invoice.update({
                'journal_id' :  default_journal_id.id,
            })
        invoice_id = self.env['account.invoice'].create(data_invoice)
        invoice_id.purchase_order_change()
        invoice_id._onchange_invoice_line_ids()
        self.invoice_ids = [(4,invoice_id.id)]
        self.invoice_ids.filtered(lambda x: x.state == 'draft').action_invoice_open()

    def create_invoice_show_view(self):
        if self.amount_total == 0:
            raise UserError("Bạn không thể hoá đơn khi Tổng bằng 0")
        if not self.invoice_ids.filtered(lambda inv:inv.state != 'cancel'):
            self.bt_action_create_invoice()
            # result = self.action_view_invoice()
            # return result

    @api.multi
    def button_confirm_order(self):
        self.button_confirm()
        if self.amount_total > 0:
            self.create_invoice_show_view()

    @api.multi
    def print_excel(self):
        self.ensure_one()

        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        string_sheet = 'Phieu Nhap Kho Mua hang' if not self.purchase_order_return else 'Phieu Xuat Kho Tra hang'
        worksheet = workbook.add_worksheet(string_sheet)
        bold = workbook.add_format({'bold': True})

        merge_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': '16'})
        header_bold_color = workbook.add_format({
            'bold': True,
            'font_size': '14',
            'align': 'center',
            'valign': 'vcenter'
        })
        header_bold_border_color = workbook.add_format({
            'bold': True,
            'font_size': '14',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })
        body_bold_color = workbook.add_format({
            'bold': False,
            'font_size': '14',
            'align': 'left',
            'valign': 'vcenter'
        })
        body_bold_center_color = workbook.add_format({
            'bold': False,
            'font_size': '14',
            'align': 'center',
            'valign': 'vcenter'
        })
        body_bold_border_color = workbook.add_format({
            'bold': False,
            'font_size': '14',
            'align': 'left',
            'valign': 'vcenter',
            'border': 1
        })
        money = workbook.add_format({
            'num_format': '#,##0',
            'border': 1,
        })
        # back_color =
        # back_color_date =

        worksheet.merge_range('A1:D1', self.company_id.name, body_bold_color)
        worksheet.merge_range('A2:D2', self.company_id.street, body_bold_color)

        string_header = "PHIẾU NHẬP KHO MUA HÀNG" if not self.purchase_order_return else "PHIẾU XUẤT KHO TRẢ HÀNG"
        worksheet.merge_range('C3:E3', unicode(string_header, "utf-8"), merge_format)
        date = datetime.strptime(self.date_order, DEFAULT_SERVER_DATETIME_FORMAT)
        string = "Ngày %s tháng %s năm %s" % (date.day, date.month, date.year)
        worksheet.merge_range('C4:E4', unicode(string, "utf-8"), header_bold_color)

        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 40)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 20)
        worksheet.set_column('G:G', 20)

        worksheet.merge_range('A5:F5', 'Người bán:', body_bold_color)
        worksheet.merge_range('A6:F6', 'Tên nhà cung cấp: %s' % (self.partner_id.name), body_bold_color)
        worksheet.merge_range('A7:F7', 'Địa chỉ: %s' % (self.partner_id.street), body_bold_color)
        worksheet.merge_range('A8:F8', 'Diễn giải: %s' % (self.notes or ("Mua hàng %s" %(self.partner_id.name,)),), body_bold_color)
        worksheet.merge_range('A9:F9', 'Điện thoại: %s' % (self.partner_id.phone or ""), body_bold_color)

        worksheet.write(4, 6, 'Số: %s' % (self.name), body_bold_color)
        worksheet.write(5, 6, 'Loại tiền: VND', body_bold_color)

        row = 10
        count = 0
        summary_header = ['STT', 'Mã hàng', 'Tên hàng', 'Đơn vị', 'Số lượng', 'Đơn giá', 'Thành tiền']
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_border_color) for
         header_cell in
         range(0, len(summary_header)) if summary_header[header_cell]]
        no = 0
        for line in self.order_line:
            no += 1
            row += 1
            count += 1
            worksheet.write(row, 0, no, body_bold_border_color)
            worksheet.write(row, 1, line.product_id.default_code, body_bold_border_color)
            worksheet.write(row, 2, line.product_id.name, body_bold_border_color)
            worksheet.write(row, 3, line.product_uom.name, body_bold_border_color)
            worksheet.write(row, 4, line.product_qty, money)
            worksheet.write(row, 5, line.final_price, money)
            worksheet.write(row, 6, line.price_subtotal, money)
        row += 1
        # worksheet.merge_range('A9:F9', 'Điện thoại: %s' % (self.partner_id.phone), body_bold_color)
        worksheet.merge_range(row, 0, row, 5, unicode("Cộng", "utf-8"), body_bold_border_color)
        worksheet.write(row, 6, self.amount_untaxed, money)
        row += 1
        worksheet.merge_range(row, 0, row, 5, unicode("Cộng tiền hàng", "utf-8"), body_bold_border_color)
        worksheet.write(row, 6, self.amount_untaxed, money)
        row += 1
        worksheet.merge_range(row, 0, row, 1, unicode("Thuế suất GTGT", "utf-8"), body_bold_border_color)
        worksheet.write(row, 2, '', money)
        worksheet.merge_range(row, 3, row, 5, unicode("Tiền suất GTGT", "utf-8"), body_bold_border_color)
        worksheet.write(row, 6, self.amount_tax, money)
        row += 1
        worksheet.merge_range(row, 3, row, 5, unicode("Tổng thanh toán", "utf-8"), body_bold_border_color)
        worksheet.write(row, 6, self.amount_total, money)
        row += 1
        string = "Số tiền viết bằng chữ: %s đồng."
        string = unicode(string, "utf-8")
        string = string % self.total_text
        worksheet.merge_range(row, 0, row, 6, string, body_bold_color)
        row += 1
        string = "Ngày %s tháng %s năm %s" % (date.day, date.month, date.year)
        worksheet.write(row, 5, unicode(string, "utf-8"), body_bold_center_color)
        row += 2
        worksheet.merge_range(row, 0, row, 1, unicode("Người nhận hàng", "utf-8"), header_bold_color)
        worksheet.write(row, 2, unicode("Kho", "utf-8"), header_bold_color)
        worksheet.merge_range(row, 3, row, 4, unicode("Người lập phiếu", "utf-8"), header_bold_color)
        worksheet.merge_range(row, 5, row, 6, unicode("Giám đốc", "utf-8"), header_bold_color)
        row += 1
        worksheet.merge_range(row, 0, row, 1, unicode("(Ký, họ tên)", "utf-8"), body_bold_center_color)
        worksheet.write(row, 2, unicode("(Ký, họ tên)", "utf-8"), body_bold_center_color)
        worksheet.merge_range(row, 3, row, 4, unicode("(Ký, họ tên)", "utf-8"), body_bold_center_color)
        worksheet.merge_range(row, 5, row, 6, unicode("(Ký, họ tên)", "utf-8"), body_bold_center_color)

        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create(
            {'name': 'DonHangExcel.xlsx', 'datas_fname': 'DonHangExcel.xlsx', 'datas': result})
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return {"type": "ir.actions.act_url",
                "url": str(base_url) + str(download_url)}

    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     res = super(purchase_order, self).fields_view_get(view_id, view_type, toolbar=toolbar, submenu=False)
    #     if view_type == 'form' and res.get('toolbar', False) and 'print' in res['toolbar']:
    #         del res['toolbar']['print']
    #     return res

    @api.multi
    def print_quotation(self):
        self.filtered(lambda s: s.state == 'draft').write({'state': 'sent'})
        # pdf = self.env['report'].sudo().get_pdf([self.id], 'purchase.report_purchasequotation', data=None)
        # from pyPdf import PdfFileWriter, PdfFileReader
        # reader = PdfFileReader(cStringIO.StringIO(pdf))
        # pages_number = reader.getNumPages()
        # if pages_number > 1:
        #     return self.env['report'].get_action(self, 'tuanhuy_purchase.report_purchaseorder_a4')
        # else:
        return self.env['report'].get_action(self, 'purchase.report_purchasequotation')

    @api.multi
    def change_record_checked(self):
        for record in self:
            if not record.record_checked:
                record.record_checked = True
            else:
                record.record_checked = False

    @api.multi
    def _compute_total(self):
        for record in self:
            subtotal = record.amount_total
            total_text = self.env['stock.picking'].DocTienBangChu(subtotal)
            record.total_text = total_text

    def _check_color_picking(self):
        for record in self:
            pickings = record.mapped('picking_ids')
            for picking in pickings:
                if picking.check_return_picking:
                    record.check_color_picking = True

    @api.multi
    def import_data_excel(self):
        for record in self:
            if record.import_data:
                data = base64.b64decode(record.import_data)
                wb = open_workbook(file_contents=data)
                sheet = wb.sheet_by_index(0)

                order_line = record.order_line.browse([])

                row_error = []
                for row_no in range(sheet.nrows):
                    if row_no > 0:
                        row = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                        if len(row) >= 5:
                            product = self.env['product.product'].search([
                                '|', ('default_code', '=', row[0].strip()),
                                ('barcode', '=', row[0].strip())
                            ], limit=1)
                            if not product or float(row[4]) < 0 or int(float(row[3]))< 0:
                                row_error.append({
                                    'default_code' : row[0],
                                    'price': row[4],
                                    'qty': row[3],
                                })
                if row_error:
                    return {
                        'name': 'Import Warning',
                        'type': 'ir.actions.act_window',
                        'res_model': 'import.warning',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'target': 'new',
                        'context': {
                            'data' : row_error,
                        }
                    }

                else:
                    for row_no in range(sheet.nrows):
                        row = (
                        map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                        if len(row) >= 5:
                            product = self.env['product.product'].search([
                                '|', ('default_code', '=', row[0].strip()),
                                ('barcode', '=', row[0].strip())
                            ], limit=1)
                            if product and product.id:
                                line_data = {
                                    'product_id': product.id,
                                    'product_uom': product.uom_id.id,
                                    'name': row[1].strip() or product.name,
                                    'price_discount': float(row[4]),
                                    'product_uom_qty': int(float(row[3])),
                                    'product_qty': int(float(row[3])),
                                }
                                line = record.order_line.new(line_data)
                                line.onchange_product_id()
                                line.product_qty = int(float(row[3]))
                                line.price_unit = float(row[4]) or product.lst_price
                                order_line += line
                    record.order_line = order_line

    def export_po_data_excel(self):
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('%s' % (self.name))

        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 40)
        worksheet.set_column('C:C', 10)
        worksheet.set_column('D:D', 10)
        worksheet.set_column('E:E', 15)

        header_bold_color = workbook.add_format({'bold': True, 'font_size': '11', 'align': 'center', 'valign': 'vcenter'})
        header_bold_color.set_text_wrap(1)
        body_bold_color = workbook.add_format({'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        # body_bold_color_number = workbook.add_format({'bold': False, 'font_size': '14', 'align': 'right', 'valign': 'vcenter'})
        # body_bold_color_number.set_num_format('#,##0')
        row = 0
        summary_header = ['Mã nội bộ', 'Miêu tả','Đơn vị','SL đặt','Giá đã CK']

        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for line in self.order_line:
            row += 1
            worksheet.write(row, 0, line.product_id.default_code or '')
            worksheet.write(row, 1, line.name)
            worksheet.write(row, 2, line.product_uom.name or '')
            worksheet.write(row, 3, line.product_qty)
            worksheet.write(row, 4, line.price_discount)

        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create({
            'name': '%s.xlsx'%(self.name),
            'datas_fname': '%s.xlsx'%(self.name),
            'datas': result
        })
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return {
            'type': 'ir.actions.act_url',
            'url': str(base_url) + str(download_url),
        }

    @api.onchange('tax_id')
    def onchange_tax_id(self):
        for record in self:
            for line in record.order_line:
                line.taxes_id = record.tax_id
                line.tax_sub = int(record.tax_id.amount)

    @api.model
    def create(self, vals):
        res = super(purchase_order, self).create(vals)
        if not res.purchase_order_return:
            date_order = datetime.strptime(res.date_order, DEFAULT_SERVER_DATETIME_FORMAT)
            datime_now = datetime.today()
            if date_order.month != datime_now.month or date_order.year != datime_now.year:
                name_sub = date_order.strftime("/%m%y")
                self.env.cr.execute(
                    "select name from purchase_order where name LIKE '%s' and name LIKE '%s' ORDER BY name DESC" % (
                    "%" + name_sub, "PO%"))
                res_trans = self.env.cr.fetchall()
                if res_trans and res_trans[0]:
                    int_name = int(res_trans[0][0].split('PO')[1].split(name_sub)[0]) + 1
                    name_order = "PO%s%s" % ('{0:06}'.format(int_name), name_sub)
                    res.name = name_order
                else:
                    if date_order.month < datime_now.month and date_order.year <= datime_now.year:
                        res.name = "PO0000001" + name_sub
        else:
            date_order = datetime.strptime(res.date_order, DEFAULT_SERVER_DATETIME_FORMAT)
            datime_now = datetime.today()
            if date_order.month != datime_now.month or date_order.year != datime_now.year:
                name_sub = date_order.strftime("/%m%y")
                self.env.cr.execute(
                    "select name from purchase_order where name LIKE '%s' and name LIKE '%s' ORDER BY name DESC" % (
                        "%" + name_sub, "RTP%"))
                res_trans = self.env.cr.fetchall()
                if res_trans and res_trans[0]:
                    int_name = int(res_trans[0][0].split('RTP')[1].split(name_sub)[0]) + 1
                    name_order = "RTP%s%s" % ('{0:06}'.format(int_name), name_sub)
                    res.name = name_order
                else:
                    if date_order.month < datime_now.month and date_order.year <= datime_now.year:
                        res.name = "RTP0000001" + name_sub
        # sequence = 1
        for line in res.order_line.sorted('id', reverse=False):
            # line.sequence = sequence
            line.brand_name = line.product_id.brand_name
            line.group_sale_id = line.product_id.group_sale_id and line.product_id.group_sale_id.id
            # sequence += 1
        res.with_context(button_dummy_create=True).button_dummy()
        return res

    @api.multi
    def write(self, vals):
        if 'date_order' in vals and not self.purchase_order_return:
            name = ''
            date_order = datetime.strptime(vals['date_order'], DEFAULT_SERVER_DATETIME_FORMAT)
            datime_now = datetime.today()
            if date_order.month != datime_now.month or date_order.year != datime_now.year:
                name_sub = date_order.strftime("/%m%y")
                self.env.cr.execute(
                    "select name from purchase_order where name LIKE '%s' and name LIKE '%s' ORDER BY name DESC" % (
                        "%" + name_sub, "PO%"))
                res_trans = self.env.cr.fetchall()
                if res_trans and res_trans[0]:
                    int_name = int(res_trans[0][0].split('PO')[1].split(name_sub)[0]) + 1
                    name_order = "PO%s%s" % ('{0:06}'.format(int_name), name_sub)
                    name = name_order
                else:
                    if date_order.month < datime_now.month and date_order.year <= datime_now.year:
                        name = "PO0000001" + name_sub
                if name:
                    vals['name'] = name
        if 'date_order' in vals and self.purchase_order_return:
            name = ''
            date_order = datetime.strptime(vals['date_order'], DEFAULT_SERVER_DATETIME_FORMAT)
            datime_now = datetime.today()
            if date_order.month != datime_now.month or date_order.year != datime_now.year:
                name_sub = date_order.strftime("/%m%y")
                self.env.cr.execute(
                    "select name from purchase_order where name LIKE '%s' and name LIKE '%s' ORDER BY name DESC" % (
                        "%" + name_sub, "RTP%"))
                res_trans = self.env.cr.fetchall()
                if res_trans and res_trans[0]:
                    int_name = int(res_trans[0][0].split('RTP')[1].split(name_sub)[0]) + 1
                    name_order = "RTP%s%s" % ('{0:06}'.format(int_name), name_sub)
                    name = name_order
                else:
                    if date_order.month < datime_now.month and date_order.year <= datime_now.year:
                        name = "RTP0000001" + name_sub
                if name:
                    vals['name'] = name
            # else:
            #     vals['name'] = self.env['ir.sequence'].next_by_code('purchase.order') or '/'
        res = super(purchase_order, self).write(vals)
        # sequence = 1
        # for line in self.order_line.sorted('id', reverse=False):
        #     line.sequence = sequence
        #     sequence += 1
        if not 'button_dummy_create' in self._context and not 'button_dummy_write' in self._context:
            self.with_context(button_dummy_write=True).button_dummy()
        return res

    @api.multi
    def update_sequence_purchase(self):
        purchase_ids = self.search([])
        for purchase in purchase_ids:
            sequence = 1
            for line in purchase.order_line.sorted('id', reverse=False):
                line.sequence = sequence
                line.brand_name = line.product_id.brand_name
                line.group_sale_id = line.product_id.group_sale_id and line.product_id.group_sale_id.id
                sequence += 1
        return True

    def action_update_check_record(self):
        ids = self.env.context.get('active_ids', [])
        orderlines = self.browse(ids)
        for order in orderlines:
            order.record_checked = False