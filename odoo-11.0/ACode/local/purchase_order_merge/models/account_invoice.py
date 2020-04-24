# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _

class account_invoice(models.Model):
    _inherit = 'account.invoice'
    
    @api.onchange('purchase_id')
    def purchase_order_change(self):
        if not self.purchase_id:
            return {}
        if not self.partner_id:
            self.partner_id = self.purchase_id.partner_id.id

        new_lines = self.env['account.invoice.line']
        for line in self.purchase_id.order_line - self.invoice_line_ids.mapped('purchase_line_id'):
	    for invoice_line in self.purchase_id.mapped('invoice_ids').mapped('invoice_line_ids'):
		if invoice_line.mapped('purchase_line_id') == line:
			line -= line	
	    if line:
		    data = self._prepare_invoice_line_from_po_line(line)
		    new_line = new_lines.new(data)
		    new_line._set_additional_fields(self)
		    new_lines += new_line

        self.invoice_line_ids += new_lines
        self.purchase_id = False
        return {}
