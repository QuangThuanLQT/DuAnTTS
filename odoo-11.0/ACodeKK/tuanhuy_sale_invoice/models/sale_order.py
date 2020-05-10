# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools import float_compare
from odoo.exceptions import UserError

class sale_order(models.Model):
    _inherit = 'sale.order'

    @api.model
    def process_scheduler_invoice_create(self):
        sales = self.env['sale.order.line'].search([
            ('invoice_lines','=',False),
            ('order_id.amount_total', '>', 0),
            ('order_id.sale_order_return', '=', False),
            ('order_id.state', '=', 'sale')
        ],limit=20).mapped('order_id')

        if sales:
            invoice_sales = sales.filtered(lambda x: not x.sale_order_return and not x.invoice_ids.filtered(lambda inv: inv.state != 'cancel'))
            for sale in invoice_sales:
                invoices = sale.invoice_ids.filtered(lambda x: x.state != 'cancel')
                if not len(invoices):
                    try:
                        sale.with_context({
                            'active_id': sale.id,
                            'active_ids': sale.ids
                        }).multi_create_account_invoice()
                    except UserError, e:
                        continue
    @api.model
    def process_scheduler_invoice_update(self):
        sales = self.search([
            ('state', '=', 'sale'),
            ('sale_order_return', '=', False),
            ('amount_total', '>', 0),
        ], order='write_date desc', limit=10)

        # Create invoice for last 10 orders that dont have any invoice
        # invoice_sales = sales.filtered(lambda x: not x.invoice_ids.filtered(lambda inv: inv.state != 'cancel'))
        # for sale in invoice_sales:
        #     invoices = sale.invoice_ids.filtered(lambda x: x.state != 'cancel')
        #     if not len(invoices):
        #         sale.with_context({
        #             'active_id': sale.id,
        #             'active_ids': sale.ids
        #         }).multi_create_account_invoice()

        # Check invalid invoices
        invalid_sales = sales.filtered(lambda x: x.invoice_ids and float_compare(x.amount_total, sum(x.invoice_ids.filtered(lambda y: y.state != 'cancel').mapped('amount_total')),0) != 0)
        for sale in invalid_sales:
            sale.with_context({
                'active_id': sale.id,
                'active_ids': sale.ids
            }).multi_update_account_invoice()

        # Create invoice for last 10 purchases
        purchases = self.env['purchase.order'].search([
            ('state', '=', 'purchase'),
            ('purchase_order_return', '=', False),
            ('amount_total', '>', 0),
        ], order='write_date desc', limit=10)
        invoice_purchases = purchases.filtered(lambda x: not x.invoice_ids.filtered(lambda inv: inv.state != 'cancel'))
        for purchase in invoice_purchases:
            invoices = purchase.invoice_ids.filtered(lambda x: x.state != 'cancel')
            if not len(invoices):
                purchase.create_invoice_show_view()

        # Check invalid purchase invoices
        invalid_purchases = purchases.filtered(lambda x: x.invoice_ids and float_compare(x.amount_total, sum(x.invoice_ids.filtered(lambda y: y.state != 'cancel').mapped('amount_total')),0) != 0)
        for purchase in invalid_purchases:
            purchase.with_context({
                'active_id': purchase.id,
                'active_ids': purchase.ids
            }).multi_update_account_invoice()

        return True