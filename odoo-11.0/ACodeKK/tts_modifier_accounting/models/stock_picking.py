# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
import StringIO
import xlsxwriter
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo.tools import float_compare, float_round, float_repr


class stock_picking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def internal_action_do_new_transfer(self):
        res = super(stock_picking, self).internal_action_do_new_transfer()
        for record in self:
            if record.internal_transfer_state == 'done':
                if record.group_id:
                    purchase_id = self.env['purchase.order'].search([('group_id', '=', record.group_id.id)])
                    if purchase_id:
                        invoices = purchase_id.invoice_ids.filtered(lambda x: x.state != 'cancel')
                        if not len(invoices):
                            purchase_id.create_invoice_show_view()
                if record.purchase_id:
                    invoices = record.purchase_id.invoice_ids.filtered(lambda x: x.state != 'cancel')
                    if not len(invoices):
                        record.purchase_id.create_invoice_show_view()
                if record.sale_id:
                    if not record.sale_id.invoice_ids.filtered(lambda inv: inv.state != 'cancel'):
                        invoice_id = record.sale_id.create_invoice_return()

                        for line in record.sale_id.order_line:
                            invoice_lines = invoice_id.invoice_line_ids.filtered(
                                lambda l: line.id in l.sale_line_ids.ids).ids or []
                            line.invoice_lines = [(6, 0, invoice_lines)]
        return res

    @api.model
    def action_picking_create_so_invoice(self, sale_id, active_id, active_ids):
        if sale_id:
            sale = self.env['sale.order'].browse(sale_id)
            sale.with_context({
                'active_id': active_id,
                'active_ids': active_ids
            }).multi_create_account_invoice()
        return 'ok'

    @api.multi
    def queue_client_create_invoice(self):
        import json
        import gearman

        queue_server = self.env['sale.order'].get_queue_server()
        if queue_server:
            gm_client = gearman.GearmanClient([queue_server.queue_server])
            for record in self:
                values = json.dumps({
                    'sale_id': record.sale_id.id,
                    'active_id': record.sale_id.id,
                    'active_ids': record.sale_id.ids
                })
                job_name = '%s_picking_create_so_invoice' % (queue_server.prefix)
                gm_client.submit_job(job_name.encode('ascii', 'ignore'), values, priority=gearman.PRIORITY_HIGH,
                                     background=True)

    @api.multi
    def delivery_action_assign(self):
        res = super(stock_picking, self).delivery_action_assign()
        for record in self:
            if record.state_delivery == 'delivery':
                if record.sale_id:
                    self.env.cr.commit()
                    record.sudo().queue_client_create_invoice()
                    # record.sale_id.with_context({
                    #     'active_id': record.sale_id.id,
                    #     'active_ids': record.sale_id.ids
                    # }).multi_create_account_invoice()
                if record.purchase_id:
                    record.purchase_id.with_context({
                        'active_id': record.purchase_id.id,
                        'active_ids': record.purchase_id.ids
                    }).multi_create_account_invoice()
        return res


class modifier_sale_ihr(models.Model):
    _inherit = 'sale.order'

    create_invoice = fields.Boolean(default=False)

    @api.multi
    def multi_create_account_invoice(self):
        super(modifier_sale_ihr, self).multi_create_account_invoice()
        for rec in self:
            rec.invoice_ids.write({
                'date_invoice': fields.Datetime.now()
            })

    @api.model
    def _cron_queue_create_invoice(self):
        sales = self.search([
            ('create_invoice', '=', False),
            ('state', '=', 'sale'),
            ('trang_thai_dh', '=', 'delivery'),
        ])

        if len(sales) > 0:
            for sale in sales:
                if not sale.invoice_ids:
                    sale.directly_create_inv()

        return True

    @api.multi
    def directly_create_inv(self):
        res = super(modifier_sale_ihr, self).directly_create_inv()
        for record in self:
            record.create_invoice = True
            for invoice in record.invoice_ids:
                invoice.write({
                    'date_invoice': fields.Datetime.now(),
                })
        return res
