# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class stock_picking(models.Model):
    _inherit = 'stock.picking'

    invoice_ids = fields.Many2many('account.invoice', string='Invoice')
    invoice_count = fields.Integer('Số hoá đơn', compute='compute_invoice_count')

    @api.multi
    def create_invoice(self):
        self.ensure_one()

        inv_obj = self.env['account.invoice']
        inv_line_obj = self.env['account.invoice.line']
        ir_property_obj = self.env['ir.property']
        journal_obj = self.env['account.journal']

        order = False
        default_type = 'out_invoice'
        default_journal_type = 'sale'

        # vendor bill
        if self.picking_type_id and self.picking_type_id.code == 'incoming':
            order = self.purchase_id_base_origin or self.purchase_id or self.sale_select_id
            default_type = 'in_invoice'
            default_journal_type = 'purchase'

        # customer invoice
        else:
            order = self.sale_select_id if self.sale_select_id else self.sale_id
            default_type = 'out_invoice'
            default_journal_type = 'sale'

        inv_data = inv_obj.with_context(type=default_type).default_get(inv_obj._fields)
        journal_id = inv_data.get('journal_id', False) or inv_obj.with_context(type=default_type)._default_journal()

        line_account_id = False
        if default_type in ('out_invoice', 'in_refund') and journal_id:
            line_account_id = journal_obj.browse(journal_id).default_credit_account_id.id or False
        else:
            line_account_id = journal_obj.browse(journal_id).default_debit_account_id.id or False

        account_id = False
        # if self.product_id.id:
        #     account_id = self.product_id.property_account_income_id.id or self.product_id.categ_id.property_account_income_categ_id.id
        if not account_id:
            inc_acc = ir_property_obj.get('property_account_income_categ_id', 'product.category')
            account_id = order.fiscal_position_id.map_account(inc_acc).id if inc_acc else False
        if not account_id:
            raise UserError(_(
                'There is no income account defined. You may have to install a chart of account from Accounting app, settings menu.'))

        invoice_line = []
        picking_product = {}
        invoice_product = {}
        # summary all product and qty of invoice
        if self.invoice_ids:
            for line in self.invoice_ids.mapped('invoice_line_ids'):
                if line.product_id not in invoice_product.keys():
                    invoice_product.update({line.product_id: line.quantity})
                else:
                    invoice_product.update({line.product_id: picking_product.get(line.product_id) + line.quantity})

        # get all product and qty of picking
        if self.pack_operation_product_ids and len(self.pack_operation_product_ids.ids):

            for pack_line in self.pack_operation_product_ids:
                if pack_line.product_id not in picking_product.keys():
                    picking_product.update({pack_line.product_id: pack_line.qty_done})
                else:
                    picking_product.update(
                        {pack_line.product_id: picking_product.get(pack_line.product_id) + pack_line.qty_done})

        else:

            for move in self.move_lines:
                if move.product_id not in picking_product.keys():
                    picking_product.update({move.product_id: move.product_uom_qty})
                else:
                    picking_product.update(
                        {move.product_id: picking_product.get(move.product_id) + move.product_uom_qty})

        # Compare product,qty between invoices and picking and add missing line
        missing_product = {}
        for key, val in picking_product.iteritems():
            missing_qty = val - invoice_product.get(key, 0)
            if missing_qty > 0:
                missing_product.update({key: missing_qty})

        if not missing_product:
            raise UserError(_("The Invoices are fully"))
        else:

            # get data for invoice line
            for product, qty in missing_product.iteritems():
                order_line = order.order_line.filtered(lambda rec: rec.product_id.id == product.id)
                line_data = {
                    'name': product.description or (str(self.name) + ' - ' + (order.display_name or '')),
                    'origin': self.name,
                    'account_id': line_account_id,
                    'product_id': product.id or False,
                    'price_unit': order_line and order_line[0].last_price_unit or 0,
                    'quantity': qty,
                    'discount': 0,
                    'uom_id': product.uom_id.id or False,
                    'sale_line_ids': order_line and [(6, 0, order_line.ids)] or [],
                    # 'invoice_line_tax_ids': order_line and [(6,0,order_line.tax_id.ids)] or [],
                    # 'account_analytic_id': order.project_id.id or False,
                }

                if order._name == 'purchase.order':
                    line_data.update({'invoice_line_tax_ids': order_line and order_line[0] and [
                        (6, 0, order_line[0].taxes_id.ids)] or [],
                                      'account_analytic_id': order_line and order_line[0] and order_line[
                                          0].account_analytic_id.id or False})
                elif order._name == 'sale.order':
                    line_data.update({'invoice_line_tax_ids': order_line and order_line[0] and [
                        (6, 0, order_line[0].tax_id.ids)] or [], 'account_analytic_id': order.project_id.id or False})

                invoice_line.append([0, 0, line_data])
            # get data for invoice
            name = ''
            user_id = False
            inv_account_id = False
            team_id = False
            note = ''
            partner_id = False
            partner_shipping_id = False
            currency_id = False
            if order._name == 'purchase.order':
                name = order.name
                user_id = order.activity_user_id.id or False
                inv_account_id = order.partner_id.property_account_payable_id.id or False
                note = order.notes
                partner_id = order.partner_id.id or False
                currency_id = order.currency_id.id or False
            elif order._name == 'sale.order':
                name = order.client_order_ref or order.name
                user_id = order.user_id.id or False
                inv_account_id = order.partner_id.property_account_receivable_id.id or False
                team_id = order.team_id.id or False
                note = order.note
                partner_id = order.partner_invoice_id.id or False
                partner_shipping_id = order.partner_shipping_id.id or False
                currency_id = order.pricelist_id.currency_id.id

            invoice_vals = {}
            for key, val in inv_data.iteritems():
                default_key = 'default_' + str(key)
                invoice_vals.update({default_key: val})

            invoice_vals.update({
                'default_name': name,
                'default_origin': order.name,
                'default_type': default_type,
                'default_journal_type': default_journal_type,
                'default_reference': False,
                'default_account_id': inv_account_id,
                'default_partner_id': partner_id,
                'default_partner_shipping_id': partner_shipping_id,
                'default_invoice_line_ids': invoice_line,
                'default_currency_id': currency_id,
                'default_payment_term_id': order.payment_term_id.id,
                'default_fiscal_position_id': order.fiscal_position_id.id or order.partner_id.property_account_position_id.id,
                'default_team_id': team_id,
                'default_user_id': user_id,
                'default_comment': note,
                'create_from_picking': self.id or False
            })
            invoice_vals.pop('default_state', None)
            str_name = 'Hóa đơn khách hàng'
            view_id = self.env.ref('account.invoice_form').id
            if self.picking_type_id and self.picking_type_id.code == 'incoming':
                # invoice_vals.update({'default_type' : 'in_invoice','default_journal_type': 'purchase'})
                str_name = 'Hóa đơn Nhà cung cấp'
                view_id = self.env.ref('account.invoice_supplier_form').id

            return {
                'name': str_name,
                'type': 'ir.actions.act_window',
                'res_model': 'account.invoice',
                'view_mode': 'form',
                'view_id': view_id,
                'context': invoice_vals
            }

    @api.multi
    def create_invoices(self):
        for record in self:
            record.create_invoice()

    @api.depends('invoice_ids')
    def compute_invoice_count(self):
        for record in self:
            record.invoice_count = len(record.invoice_ids)

    @api.multi
    def action_view_invoice_ids(self):
        action = False
        if self.picking_type_id and self.picking_type_id.code == 'incoming':
            action = self.env.ref('account.action_invoice_tree2').read()[0]
            action['domain'] = [('type', 'in', ('in_invoice', 'in_refund')), ('id', 'in', self.invoice_ids.ids)]
            return action
        else:
            action = self.env.ref('account.action_invoice_tree1').read()[0]
            action['domain'] = [('type', 'in', ('out_invoice', 'out_refund')), ('id', 'in', self.invoice_ids.ids)]
            return action


class purchase_order(models.Model):
    _inherit = 'purchase.order'

    @api.depends('order_line.invoice_lines.invoice_id.state', 'picking_ids.invoice_ids')
    def _compute_invoice(self):
        for order in self:
            invoices = self.env['account.invoice']
            for line in order.order_line:
                invoices |= line.invoice_lines.mapped('invoice_id')
            if order.picking_ids.mapped('invoice_ids') and len(order.picking_ids.mapped('invoice_ids')):
                invoices += order.picking_ids.mapped('invoice_ids')

            order.invoice_ids = invoices
            order.invoice_count = len(invoices)


class sale_order(models.Model):
    _inherit = 'sale.order'

    @api.depends('state', 'order_line.invoice_status', 'picking_ids.invoice_ids')
    def _get_invoiced(self):
        res = super(sale_order, self)._get_invoiced()
        for record in self:
            if record.picking_ids.mapped('invoice_ids') and len(record.picking_ids.mapped('invoice_ids')):
                record.invoice_count += len(record.picking_ids.mapped('invoice_ids'))
                record.invoice_ids += record.picking_ids.mapped('invoice_ids')
        return res


class account_invoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def create(self, vals):
        res = super(account_invoice, self).create(vals)
        if self.env.context.get('create_from_picking', False):
            self.env['stock.picking'].browse(self.env.context.get('create_from_picking', False)).write(
                {'invoice_ids': [(4, res.id)]})
        return res
