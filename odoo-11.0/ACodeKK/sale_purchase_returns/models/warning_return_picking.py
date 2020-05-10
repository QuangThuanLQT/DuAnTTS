# -*- coding: utf-8 -*-

from odoo import models, fields, api

class warning_return_picking(models.Model):
    _name = "warning.return.picking"

    name = fields.Text(readonly=True)
    reason = fields.Text(required=True)

    @api.model
    def default_get(self, fields):
        rec = super(warning_return_picking, self).default_get(fields)
        rec['name'] = self._context.get('parnert_name') + self._context.get('comment') + self._context.get('product_list')
        return rec

    def apply_invoice(self):
        invoice_id = self.env['account.invoice'].browse(self._context.get('invoice_id'))
        invoice_id.with_context(allow_invoice_open=True).action_invoice_open()
        invoice_id.comment = self.reason