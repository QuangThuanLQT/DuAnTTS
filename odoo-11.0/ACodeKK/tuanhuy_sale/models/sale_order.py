# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT,DEFAULT_SERVER_DATE_FORMAT
from odoo.tools import float_is_zero, float_compare
import base64
import StringIO
import xlsxwriter
from datetime import datetime
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

class account_move_line(models.Model):
    _inherit = "account.move.line"

    def update_open_amount_residual(self):
        for line in self:
            if not line.account_id.reconcile:
                self._cr.execute("""UPDATE account_move_line SET reconciled=FALSE, amount_residual=0,amount_residual_currency=0
                                                                    WHERE id=%s""" % (line.id))
                continue
            #amounts in the partial reconcile table aren't signed, so we need to use abs()
            amount = abs(line.debit - line.credit)
            amount_residual_currency = abs(line.amount_currency) or 0.0
            sign = 1 if (line.debit - line.credit) > 0 else -1
            if not line.debit and not line.credit and line.amount_currency and line.currency_id:
                #residual for exchange rate entries
                sign = 1 if float_compare(line.amount_currency, 0, precision_rounding=line.currency_id.rounding) == 1 else -1

            for partial_line in (line.matched_debit_ids + line.matched_credit_ids):
                # If line is a credit (sign = -1) we:
                #  - subtract matched_debit_ids (partial_line.credit_move_id == line)
                #  - add matched_credit_ids (partial_line.credit_move_id != line)
                # If line is a debit (sign = 1), do the opposite.
                sign_partial_line = sign if partial_line.credit_move_id == line else (-1 * sign)

                amount += sign_partial_line * partial_line.amount
                #getting the date of the matched item to compute the amount_residual in currency
                if line.currency_id:
                    if partial_line.currency_id and partial_line.currency_id == line.currency_id:
                        amount_residual_currency += sign_partial_line * partial_line.amount_currency
                    else:
                        if line.balance and line.amount_currency:
                            rate = line.amount_currency / line.balance
                        else:
                            date = partial_line.credit_move_id.date if partial_line.debit_move_id == line else partial_line.debit_move_id.date
                            rate = line.currency_id.with_context(date=date).rate
                        amount_residual_currency += sign_partial_line * line.currency_id.round(partial_line.amount * rate)

            #computing the `reconciled` field. As we book exchange rate difference on each partial matching,
            #we can only check the amount in company currency
            reconciled = False
            digits_rounding_precision = line.company_id.currency_id.rounding
            if float_is_zero(amount, precision_rounding=digits_rounding_precision):
                if line.currency_id and line.amount_currency:
                    if float_is_zero(amount_residual_currency, precision_rounding=line.currency_id.rounding):
                        reconciled = True
                else:
                    reconciled = True
            self._cr.execute("""UPDATE account_move_line SET reconciled=%s, amount_residual=%s,amount_residual_currency=%s
                                            WHERE id=%s""" % (reconciled,line.company_id.currency_id.round(amount * sign),
                                                              line.currency_id and line.currency_id.round(
                                                              amount_residual_currency * sign) or 0.0,line.id))

class sale_order(models.Model):
    _inherit = 'sale.order'

    tax_id = fields.Many2one('account.tax', 'Tax', domain=[('type_tax_use', '=', 'sale')])
    total_text = fields.Char('Total Text', compute='_compute_total')
    check_box_co_cq = fields.Boolean(default=False,string = "CO, CQ")
    check_box_invoice_gtgt = fields.Boolean(default=False, string="Invoice GTGT")
    check_color_picking = fields.Boolean(compute="_check_color_picking",default=False)
    record_checked = fields.Boolean('Checked')
    delivery_status = fields.Selection([
        ('draft', 'Draft'), ('cancel', 'Cancelled'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting Availability'),
        ('partially_available', 'Partially Available'),
        ('cancel', 'Đã Huỷ'),
        ('assigned', 'Open'), ('done', 'Done')], string='Delivery Status', compute='_compute_delivery_status')
    create_invoice_check = fields.Boolean(compute='_get_create_invoice_check', default=False)
    amount_untaxed = fields.Monetary(digits=(16, 0))
    amount_tax = fields.Monetary(digits=(16, 0))
    amount_total = fields.Monetary(digits=(16, 0))
    amount_discount = fields.Monetary(digits=(16, 0))
    product_code = fields.Char('Product code')
    invoice_status = fields.Selection([
        ('upselling', 'Upselling Opportunity'),
        ('invoiced', 'Fully Invoiced'),
        ('to invoice', 'To Invoice'),
        ('no', 'Nothing to Invoice'),
        ('cancel', 'Hoá Đơn Huỷ')
    ], string='Invoice Status', compute='_get_invoiced', store=True, readonly=True)
    queue_procurement = fields.Boolean('Queue Procurement', default=False)
    invoice_number_total_real = fields.Char(string='Số hoá đơn thực', compute='get_invoice_number_total_real')

    @api.multi
    def name_get(self):
        return [(order.id, '%s [%s]' % (order.name, order.partner_id.name)) for order in self]

    @api.multi
    def get_invoice_number_total_real(self):
        for record in self:
            name = ', '.join( (invoice.invoice_number_real or '') + ' - ' + str(invoice.invoice_total_real) for invoice in record.invoice_ids)
            record.invoice_number_total_real = name

    @api.multi
    def button_dummy(self):
        self.supply_rate()

        for line in self.order_line:
            if line.price_discount:
                price = line.price_discount
            else:
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                            product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.write({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_subtotal': taxes['total_excluded'],
                'price_total': taxes['total_included'],
            })

        for order in self:
            amount_untaxed = amount_tax = amount_discount = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
                if line.price_discount:
                    amount_discount += (line.product_uom_qty * (line.price_unit - line.price_discount))
                else:
                    amount_discount += (line.product_uom_qty * line.price_unit * line.discount) / 100
            order.write({
                'amount_untaxed': order.pricelist_id.currency_id.round(amount_untaxed),
                'amount_tax': order.pricelist_id.currency_id.round(amount_tax),
                'amount_discount': order.pricelist_id.currency_id.round(amount_discount),
                'amount_total': amount_untaxed + amount_tax,
            })
        return True

    @api.depends('order_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        return True
        # for order in self:
        #     amount_untaxed = amount_tax = amount_discount = 0.0
        #     for line in order.order_line:
        #         amount_untaxed += line.price_subtotal
        #         amount_tax += line.price_tax
        #         if line.price_discount:
        #             amount_discount += (line.product_uom_qty * (line.price_unit - line.price_discount))
        #         else:
        #             amount_discount += (line.product_uom_qty * line.price_unit * line.discount) / 100
        #     order.update({
        #         'amount_untaxed': order.pricelist_id.currency_id.round(amount_untaxed),
        #         'amount_tax': order.pricelist_id.currency_id.round(amount_tax),
        #         'amount_discount': order.pricelist_id.currency_id.round(amount_discount),
        #         'amount_total': amount_untaxed + amount_tax,
        #     })

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
            if 'sale_order_return' not in fields:
                fields.append('sale_order_return')
            res = super(sale_order, self).search_read(domain=domain, fields=fields, offset=offset,
                                                          limit=limit, order=order)

            def convertVals(x):
                if x.get('sale_order_return', False):
                    x['amount_untaxed'] = -x['amount_untaxed']
                    x['amount_total'] = -x['amount_total']
                return x

            res = map(lambda x: convertVals(x), res)
            return res
        return super(sale_order, self).search_read(domain=domain, fields=fields, offset=offset,
                                                       limit=limit, order=order)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
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
        res = super(sale_order, self).read_group(domain, fields, groupby, offset=offset,
                                                                                limit=limit, orderby=orderby, lazy=lazy)
        return res

    @api.depends('state', 'order_line.invoice_status')
    def _get_invoiced(self):
        """
        Compute the invoice status of a SO. Possible statuses:
        - no: if the SO is not in status 'sale' or 'done', we consider that there is nothing to
          invoice. This is also hte default value if the conditions of no other status is met.
        - to invoice: if any SO line is 'to invoice', the whole SO is 'to invoice'
        - invoiced: if all SO lines are invoiced, the SO is invoiced.
        - upselling: if all SO lines are invoiced or upselling, the status is upselling.

        The invoice_ids are obtained thanks to the invoice lines of the SO lines, and we also search
        for possible refunds created directly from existing invoices. This is necessary since such a
        refund is not directly linked to the SO.
        """
        for order in self:
            invoice_ids = order.order_line.mapped('invoice_lines').mapped('invoice_id').filtered(
                lambda r: r.type in ['out_invoice', 'out_refund'])
            # Search for invoices which have been 'cancelled' (filter_refund = 'modify' in
            # 'account.invoice.refund')
            # use like as origin may contains multiple references (e.g. 'SO01, SO02')
            refunds = invoice_ids.search(
                [('origin', 'like', order.name), ('company_id', '=', order.company_id.id)]).filtered(
                lambda r: r.type in ['out_invoice', 'out_refund'])
            invoice_ids |= refunds.filtered(lambda r: order.name in [origin.strip() for origin in r.origin.split(',')])
            # Search for refunds as well
            refund_ids = self.env['account.invoice'].browse()
            if invoice_ids:
                for inv in invoice_ids:
                    refund_ids += refund_ids.search(
                        [('type', '=', 'out_refund'), ('origin', '=', inv.number), ('origin', '!=', False),
                         ('journal_id', '=', inv.journal_id.id)])

            # Ignore the status of the deposit product
            deposit_product_id = self.env['sale.advance.payment.inv']._default_product_id()
            line_invoice_status = [line.invoice_status for line in order.order_line if
                                   line.product_id != deposit_product_id]

            if order.state not in ('sale', 'done'):
                invoice_status = 'no'
            elif any(invoice_status == 'to invoice' for invoice_status in line_invoice_status):
                invoice_status = 'to invoice'
            elif all(invoice_status == 'invoiced' for invoice_status in line_invoice_status):
                invoice_status = 'invoiced'
            elif all(invoice_status in ['invoiced', 'upselling'] for invoice_status in line_invoice_status):
                invoice_status = 'upselling'
            else:
                invoice_status = 'no'
            if invoice_ids and all(invoice.state == 'cancel' for invoice in invoice_ids):
                    invoice_status = 'cancel'
            order.update({
                'invoice_count': len(set(invoice_ids.ids + refund_ids.ids)),
                'invoice_ids': invoice_ids.ids + refund_ids.ids,
                'invoice_status': invoice_status
            })

    @api.onchange('product_code')
    def on_onchange_product_code(self):
        if self.product_code:
            default_code = self.product_code
            product = self.env['product.product'].search(['|',('default_code', '=', default_code),('barcode', '=', default_code)])
            if not product:
                product_barcode_id = self.env['product.barcode'].search([('name','=',default_code)])
                if product_barcode_id:
                    product = product_barcode_id.product_id.product_variant_id
            if product:
                corresponding_line = self.order_line.filtered(lambda r: r.product_id == product)
                if corresponding_line:
                    corresponding_line[0].product_uom_qty += 1
                else:
                    line = self.order_line.new({
                        'product_id': product.id,
                        'product_uom': product.uom_id.id,
                        'product_uom_qty': 1.0,
                        'price_unit': product.lst_price,
                    })
                    line.product_id_change()
                    line.product_uom_change()
                    self.order_line += line
            self.product_code = False
            return

    @api.multi
    def multi_create_picking(self):
        ids = self.env.context.get('active_ids', [])
        sale_order_ids = self.browse(ids)
        for sale_order_id in sale_order_ids:
            if not sale_order_id.picking_ids.filtered(lambda p:p.state != 'cancel'):
                sale_order_id.order_line.mapped('procurement_ids').filtered(lambda p:p.state != 'cancel').unlink()
                sale_order_id.order_line.with_context(create_from_sale_order=sale_order_id.id)._action_procurement_create()
        # return True

    @api.depends('picking_ids')
    def _get_create_invoice_check(self):
        for record in self:
            if  all(move.state in ['done', 'assigned'] for move in record.picking_ids) and record.state == 'sale':
                record.create_invoice_check = True

    @api.multi
    def multi_create_account_invoice(self):
        ids = self.env.context.get('active_ids', [])
        orderlines = self.browse(ids)
        for order in orderlines:
            if not order.invoice_ids.filtered(lambda inv:inv.state != 'cancel') and order.amount_total != 0:
                for line in order.order_line:
                    line._get_invoice_qty()
                order.directly_create_inv()

    @api.multi
    def update_account_invoice_so(self):
        ids = self.env.context.get('active_ids', [])
        orders = self.browse(ids)
        for order in orders:
            # Cancel stock picking
            for picking_id in order.picking_ids:
                if picking_id.state in ['draft', 'confirmed']:
                    new_picking_id = picking_id.copy()
                    picking_id.do_cancel_stock_picking()
                    self._cr.execute("""DELETE FROM stock_picking WHERE id=%s""" % (picking_id.id))
                    new_picking_id.do_unreserve()
                    continue
                if picking_id.state in ['partially_available','assigned']:
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
            #Cancel invoice
            for invoice in order.invoice_ids:
                if invoice.state not in ['paid','cancel']:
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
                    account_partial_reconcile_ids = self.env['account.partial.reconcile'].search(['|',('debit_move_id','in',payment_line_move_ids),('credit_move_id','in',payment_line_move_ids)])
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
        orderlines = self.browse(ids)
        for order in orderlines:
            for invoice_id in order.invoice_ids:
                if invoice_id.state == 'draft':
                    print "----------------" + str(order.id)
                if invoice_id.state == 'open':
                    if invoice_id.move_id and datetime.strptime(order.date_order,DEFAULT_SERVER_DATETIME_FORMAT).date() != datetime.strptime(invoice_id.move_id.date,DEFAULT_SERVER_DATE_FORMAT).date():
                        self._cr.execute("""UPDATE account_move SET date='%s' WHERE id=%s""" % (
                        datetime.strptime(order.date_order, DEFAULT_SERVER_DATETIME_FORMAT).strftime(
                            DEFAULT_SERVER_DATE_FORMAT)
                        , invoice_id.move_id.id))
                        for move_line in invoice_id.move_id.line_ids:
                            self._cr.execute("""UPDATE account_move_line SET date='%s' WHERE id=%s""" % (datetime.strptime(order.date_order,DEFAULT_SERVER_DATETIME_FORMAT).strftime(DEFAULT_SERVER_DATE_FORMAT)
                            , move_line.id))
                            print "----------------" + str(order.id)
        for order in orderlines:
            if order.amount_total > 0 and order.invoice_ids and (len(orderlines) == 1 or order.amount_total != sum(order.invoice_ids.mapped('amount_total')) or any(product_id not in order.invoice_ids.mapped('invoice_line_ids').mapped('product_id')
                                                              for product_id in order.order_line.mapped('product_id'))):
                if order.invoice_ids and all(invoice.state in ['draft','open'] for invoice in order.invoice_ids):
                    invoice_line_ids = order.invoice_ids.mapped('invoice_line_ids')
                    for invoice_line_id in invoice_line_ids:
                        if not invoice_line_id.sale_line_ids:
                            self._cr.execute("""DELETE FROM account_invoice_line WHERE id=%s""" % (invoice_line_id.id))
                        else:
                            order_line_id = invoice_line_id.sale_line_ids[0]
                            if order_line_id:
                                invoice_line_id.write({
                                    'quantity': order_line_id.product_uom_qty,
                                    'discount' : order_line_id.discount,
                                    'price_unit': order_line_id.price_unit,
                                    'price_discount' : order_line_id.price_discount,
                                    'invoice_line_tax_ids': [(6, 0, order_line_id.tax_id.ids)],
                                })
                                invoice_line_id._compute_price()
                                if order_line_id.product_id != invoice_line_id.product_id:
                                    invoice_line_id.product_id = order_line_id.product_id
                                    invoice_line_id.name = order_line_id.name
                    if len(order.order_line) > len(invoice_line_ids):
                        if not order.sale_order_return:
                            for order_line_id in (order.order_line - invoice_line_ids.mapped('sale_line_ids')):
                                if order_line_id.qty_to_invoice > 0:
                                    order_line_id.invoice_line_create(order.invoice_ids[0].id, order_line_id.qty_to_invoice)
                        else:
                            new_lines = self.env['account.invoice.line']
                            for order_line_id in (order.order_line - invoice_line_ids.mapped('sale_line_ids')):
                                account_id = self.env['account.account'].search([('code', '=', '5213')],
                                                                                limit=1).id or False
                                if line.product_id or line.quantity != 0:
                                    data = {
                                        'product_id': line.product_id.id,
                                        'quantity': line.product_uom_qty,
                                        'uom_id': line.product_uom.id,
                                        'price_unit': line.price_unit,
                                        'discount': line.discount,
                                        'price_discount': line.price_discount,
                                        'invoice_line_tax_ids': [(6, 0, line.tax_id.ids)],
                                        'name': line.product_id.display_name,
                                        'account_id': account_id,
                                        'sale_line_ids': [(6, 0, line.ids)]
                                    }
                                    data['quantity'] = line.product_uom_qty
                                    new_line = new_lines.new(data)
                                    new_lines += new_line
                            order_line_id.invoice_ids[0].invoice_line_ids += new_lines
                    order.invoice_ids.compute_taxes()
            check_diff = float_compare(sum(order.invoice_ids.mapped('move_id').mapped('line_ids').mapped('credit')), order.amount_total, precision_digits=2)
            if order.amount_total > 0 and order.invoice_ids.filtered(lambda inv: inv.move_id) and check_diff != 0:
                for invoice_id in order.invoice_ids.filtered(lambda inv: inv.move_id):
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
                            script = """INSERT INTO account_move_line (ref,name, invoice_id, tax_line_id, credit,product_uom_id,currency_id,product_id,debit
                                                      ,amount_currency,quantity,partner_id,account_id,move_id,date_maturity)
                                                             VALUES ('%s','%s',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'%s')"""%(invoice_id.origin,line_data['name'],
                                line_data['invoice_id'],line_data['tax_line_id'] or 'NULL',line_data['credit'] or 0,line_data['product_uom_id'] or 'NULL',line_data['currency_id'] or 'NULL',line_data['product_id'] or 'NULL',
                                        line_data['debit'] or 0,line_data['amount_currency'] or 0,line_data['quantity'] or 0,
                                        line_data['partner_id'] or 'NULL',line_data['account_id'],invoice_id.move_id.id,fields.Date.context_today(self))
                            self._cr.execute(script)
                            self._cr.commit()
                    for line_remove in (invoice_id.move_id.mapped('line_ids') - line_not_ext):
                        self._cr.execute("""DELETE FROM account_move_line WHERE id=%s""" % (line_remove.id))
                    if invoice_id.payments_widget == 'false':
                        invoice_id.residual = invoice_id.amount_total
                    else:
                        raise UserError("Bạn không thể cập nhật hoá đơn đã thanh toán một phần: %s từ đơn hàng %s"%(invoice_id.number,order.name))
                        # invoice_id._compute_residual()


    @api.depends('picking_ids')
    def _compute_delivery_status(self):
        for record in self:
            if len(record.picking_ids) == 1:
                record.delivery_status = record.picking_ids.state
            elif len(record.picking_ids) > 1:
                record.delivery_status = record.picking_ids.filtered(lambda t: t.state != 'done')[0].state if record.picking_ids.filtered(lambda t: t.state != 'done') else 'done'

    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     res = super(sale_order, self).fields_view_get(view_id, view_type, toolbar=toolbar, submenu=False)
    #     if view_type == 'form' and res.get('toolbar', False) and 'print' in res['toolbar']:
    #         del res['toolbar']['print']
    #     return res

    @api.multi
    def print_quotation(self):
        self.filtered(lambda s: s.state == 'draft').write({'state': 'sent'})
        # pdf = self.env['report'].sudo().get_pdf([self.id], 'sale.report_saleorder', data=None)
        # from pyPdf import PdfFileWriter, PdfFileReader
        # reader = PdfFileReader(cStringIO.StringIO(pdf))
        # pages_number = reader.getNumPages()
        # if pages_number > 1:
        #     return self.env['report'].get_action(self, 'tuanhuy_sale.report_saleorder_a4')
        # else:
        return self.env['report'].get_action(self, 'sale.report_saleorder')

    @api.multi
    def delivery_set(self):
        return True

    @api.multi
    def change_record_checked(self):
        for record in self:
            if not record.record_checked:
                record.record_checked = True
            else:
                record.record_checked = False

    def _check_color_picking(self):
        for record in self:
            pickings = record.mapped('picking_ids')
            for picking in pickings:
                if picking.check_return_picking:
                    record.check_color_picking = True


    @api.onchange('date_order')
    def onchange_date_order(self):
        for record in self:
            if record.date_order:
                record.validity_date = record.date_order

    @api.onchange('tax_id')
    def onchange_tax_id(self):
        for record in self:
            for line in record.order_line:
                line.tax_id = record.tax_id
                line.tax_sub = int(record.tax_id.amount)


    @api.model
    def default_get(self, fields):
        res = super(sale_order, self).default_get(fields)

        payment_term = self.env.ref('account.account_payment_term_immediate')
        if payment_term and payment_term.id:
            res['payment_term_id'] = payment_term.id

        delivery = self.env.ref('tuanhuy_sale.tuanhuy_shop_delivery', False)
        if delivery and delivery.id:
            res['carrier_id'] = delivery.id

        return res

    @api.multi
    def _compute_total(self):
        for record in self:
            subtotal = record.amount_total
            total_text = self.env['stock.picking'].DocTienBangChu(subtotal)
            record.total_text = total_text

    @api.model
    def create(self, vals):
        res = super(sale_order, self.with_context(mail_notrack=True)).create(vals)
        if not res.sale_order_return:
            date_order = datetime.strptime(res.date_order,DEFAULT_SERVER_DATETIME_FORMAT)
            datime_now = datetime.today()
            if date_order.month != datime_now.month or date_order.year != datime_now.year:
                name_sub = date_order.strftime("/%m%y")
                self.env.cr.execute("select name from sale_order where name LIKE '%s' and name LIKE '%s' ORDER BY name DESC" % ("%" + name_sub,"SO%") )
                res_trans = self.env.cr.fetchall()
                if res_trans and res_trans[0]:
                    int_name = int(res_trans[0][0].split('SO')[1].split(name_sub)[0]) + 1
                    name_order = "SO%s%s" % ('{0:06}'.format(int_name),name_sub)
                    res.name = name_order
                else:
                    if date_order.month < datime_now.month and date_order.year <= datime_now.year:
                        res.name = "SO0000001"+name_sub

        else:
            date_order = datetime.strptime(res.date_order,DEFAULT_SERVER_DATETIME_FORMAT)
            datime_now = datetime.today()
            if date_order.month != datime_now.month or date_order.year != datime_now.year:
                name_sub = date_order.strftime("/%m%y")
                self.env.cr.execute("select name from sale_order where name LIKE '%s' and name LIKE '%s' ORDER BY name DESC" % ("%" + name_sub,"RT%") )
                res_trans = self.env.cr.fetchall()
                if res_trans and res_trans[0]:
                    int_name = int(res_trans[0][0].split('RT')[1].split(name_sub)[0]) + 1
                    name_order = "RT%s%s" % ('{0:06}'.format(int_name),name_sub)
                    res.name = name_order
                else:
                    if date_order.month < datime_now.month and date_order.year <= datime_now.year:
                        res.name = "RT0000001"+name_sub
        # sequence = 1
        # for line in res.order_line.sorted('id', reverse=False):
        #     line.sequence = sequence
        #     sequence += 1
        res.with_context(button_dummy_create=True).button_dummy()
        return res

    @api.multi
    def write(self, vals):
        if 'date_order' in vals and not self.sale_order_return:
            name = ''
            date_order = datetime.strptime(vals['date_order'], DEFAULT_SERVER_DATETIME_FORMAT)
            datime_now = datetime.today()
            if date_order.month != datime_now.month or date_order.year != datime_now.year:
                name_sub = date_order.strftime("/%m%y")
                self.env.cr.execute(
                    "select name from sale_order where name LIKE '%s' and name LIKE '%s' ORDER BY name DESC" % (
                    "%" + name_sub, "SO%"))
                res_trans = self.env.cr.fetchall()
                if res_trans and res_trans[0]:
                    int_name = int(res_trans[0][0].split('SO')[1].split(name_sub)[0]) + 1
                    name_order = "SO%s%s" % ('{0:06}'.format(int_name),name_sub)
                    name = name_order
                else:
                    if date_order.month < datime_now.month and date_order.year <= datime_now.year:
                        name = "SO0000001"+name_sub
                if name:
                    vals['name'] = name
        if 'date_order' in vals and self.sale_order_return:
            name = ''
            date_order = datetime.strptime(vals['date_order'], DEFAULT_SERVER_DATETIME_FORMAT)
            datime_now = datetime.today()
            if date_order.month != datime_now.month or date_order.year != datime_now.year:
                name_sub = date_order.strftime("/%m%y")
                self.env.cr.execute(
                    "select name from sale_order where name LIKE '%s' and name LIKE '%s' ORDER BY name DESC" % (
                        "%" + name_sub, "RT%"))
                res_trans = self.env.cr.fetchall()
                if res_trans and res_trans[0]:
                    int_name = int(res_trans[0][0].split('RT')[1].split(name_sub)[0]) + 1
                    name_order = "RT%s%s" % ('{0:06}'.format(int_name), name_sub)
                    name = name_order
                else:
                    if date_order.month < datime_now.month and date_order.year <= datime_now.year:
                        name = "RT0000001" + name_sub
                if name:
                    vals['name'] = name
            # else:
            #     vals['name'] = self.env['ir.sequence'].next_by_code('sale.order') or '/'
        res = super(sale_order, self).write(vals)
        # for record in self:
        #     sequence = 1
        #     for line in record.order_line.sorted('id', reverse=False):
        #         line.sequence = sequence
        #         sequence += 1
        if not 'button_dummy_create' in self._context and not 'button_dummy_write' in self._context:
            if 'order_line' in vals:
                self.with_context(button_dummy_write=True).button_dummy()
        return res

    def _update_sequence(self):
        orders = self.search([])
        for order in orders:
            sequence = 1
            for line in order.order_line.sorted('id', reverse=False):
                line.sequence = sequence
                line.date_order = order.date_order
                line.brand_name = line.product_tmpl_id.brand_name
                line.group_sale_id = line.product_tmpl_id.group_sale_id and line.product_tmpl_id.group_sale_id.id
                sequence += 1
            if order.sale_order_return == True:
                for pick in order.picking_ids:
                    if pick.origin != order.name:
                        pick.origin = order.name
    @api.multi
    def action_confirm(self):
        # self.button_dummy()
        res = super(sale_order, self).action_confirm()
        for record in self:
            record.confirmation_date = record.date_order
            record.order_line.write({
                'date_order': record.date_order
            })
            # TODO: Create procurement
            record.queue_procurement = True
            # record.order_line._action_procurement_create()
        return res

    @api.model
    def _cron_queue_create_picking(self):
        sales = self.search([
            ('queue_procurement', '=', True),
            ('state', '=', 'sale'),
        ])

        if len(sales) > 0:
            for sale in sales:
                sale.order_line.with_context(create_from_sale_order=sale.id)._action_procurement_create()

            sales.write({
                'queue_procurement': False
            })

        return True


    @api.multi
    def action_confirm_order(self):
        self.with_context(create_from_so=True).action_confirm()
        # if self.amount_total > 0:
        #     self.directly_create_inv()

    @api.multi
    def print_excel(self):
        self.ensure_one()

        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        string_sheet = 'Phieu Xuat Kho Ban hang' if not self.sale_order_return else 'Phieu Nhap Kho Tra hang'
        worksheet = workbook.add_worksheet(string_sheet)
        bold = workbook.add_format({'bold': True})

        merge_format = workbook.add_format({'bold': True,  'align': 'center', 'valign': 'vcenter', 'font_size': '16'})
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

        string_header = "PHIẾU XUẤT KHO BÁN HÀNG" if not self.sale_order_return else "PHIẾU NHẬP KHO TRẢ HÀNG"
        worksheet.merge_range('C3:E3', unicode(string_header, "utf-8"), merge_format)
        date = datetime.strptime(self.confirmation_date, DEFAULT_SERVER_DATETIME_FORMAT)
        string = "Ngày %s tháng %s năm %s" % (date.day, date.month, date.year)
        worksheet.merge_range('C4:E4', unicode(string, "utf-8"), header_bold_color)

        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 40)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 20)
        worksheet.set_column('G:G', 20)

        worksheet.merge_range('A5:F5', 'Người mua:', body_bold_color)
        worksheet.merge_range('A6:F6', 'Tên khách hàng: %s' %(self.partner_id.name), body_bold_color)
        worksheet.merge_range('A7:F7', 'Địa chỉ: %s' %(self.partner_id.street), body_bold_color)
        worksheet.merge_range('A8:F8', 'Diễn giải: %s' %(self.note or ('Bán hàng %s' %(self.partner_id.name))), body_bold_color)
        worksheet.merge_range('A9:F9', 'Điện thoại: %s' %(self.partner_id.phone), body_bold_color)

        worksheet.write(4, 6, 'Số: %s' % (self.name), body_bold_color)
        worksheet.write(5, 6, 'Loại tiền: VND', body_bold_color)

        row = 10
        count = 0
        summary_header = ['STT', 'Mã hàng', 'Tên hàng', 'Đơn vị', 'Số lượng', 'Đơn giá', 'Thành tiền']
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_border_color) for header_cell in
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
            worksheet.write(row, 4, line.product_uom_qty, money)
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


    def action_update_check_record(self):
        ids = self.env.context.get('active_ids', [])
        orderlines = self.browse(ids)
        for order in orderlines:
            order.record_checked = False

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        res = super(sale_order, self).action_invoice_create(grouped, final)
        if res:
            sale_order_ids = []
            if self._context.get('active_model',False) == 'sale.order' and self._context.get('active_ids',False):
                sale_order_ids = self.env['sale.order'].browse(self._context.get('active_ids',False))
            for sale_order_id in sale_order_ids:
                if sale_order_id.confirmation_date:
                    invoice_id = sale_order_id.invoice_ids
                    invoice_id.write({'date_order' : datetime.strptime(sale_order_id.confirmation_date,DEFAULT_SERVER_DATETIME_FORMAT).strftime(DEFAULT_SERVER_DATE_FORMAT)})
        for invoice in res:
            account_invoice = self.env['account.invoice'].search([('id', '=', invoice)])
            # account_invoice.action_invoice_open()
        return res

    @api.multi
    def update_line_qty_invoiced(self):
        for record in self:
            for line in record.order_line:
                line._get_invoice_qty()
                self.env.cr.commit()
        return True

    @api.multi
    def directly_create_inv(self):
        if self.amount_total == 0:
            raise UserError("Bạn không thể  hoá đơn khi Tổng bằng 0")
        popup_obj = self.env['sale.advance.payment.inv']
        context = self.env.context.copy()
        context.update({
            'active_model': 'sale.order',
            'active_ids': self.ids,
            'mail_auto_subscribe_no_notify': True,
            'mail_notrack': True,
        })
        popup_obj.create(popup_obj.default_get(popup_obj._fields)).with_context(context).create_invoices()
        for record in self:
            if record.date_order:
                for invoice in record.invoice_ids:
                    invoice.write({
                        'date_order': record.date_order,
                        'date_invoice': record.date_order,
                    })
            #set state open for invoice
            record.invoice_ids.filtered(lambda x: x.state == 'draft').with_context(context).action_invoice_open()

        return True


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    @api.model
    def default_get(self, fields):
        res = super(SaleAdvancePaymentInv, self).default_get(fields)
        res['advance_payment_method'] = 'delivered'
        return res

    @api.multi
    def _create_invoice(self, order, so_line, amount):
        res = super(SaleAdvancePaymentInv, self)._create_invoice(order, so_line, amount)
        if res:
            sale_order_id = False
            if self._context.get('active_model',False) == 'sale.order' and self._context.get('active_ids',False):
                sale_order_id = self.env['sale.order'].browse(self._context.get('active_ids',False))
            if sale_order_id and sale_order_id.confirmation_date:
                res.write({'date_order' : datetime.strptime(sale_order_id.confirmation_date,DEFAULT_SERVER_DATETIME_FORMAT).strftime(DEFAULT_SERVER_DATE_FORMAT)})

        res.action_invoice_open()
        return res

    @api.multi
    def create_invoices(self):
        # sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        # if not all(move.state in ['done', 'assigned'] for move in sale_orders.picking_ids):
        #     raise UserError(_("You can not create invoices if all of the Deliveries are incomplete."))
        res = super(SaleAdvancePaymentInv, self).create_invoices()
        return res
