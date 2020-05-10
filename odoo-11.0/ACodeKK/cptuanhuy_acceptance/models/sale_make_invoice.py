# -*- coding: utf-8 -*-
from odoo import models, fields, api

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _prepare_deposit_product(self):
        res = super(SaleAdvancePaymentInv, self)._prepare_deposit_product()
        res.update({'name':'Biên bản nghiệm thu'})
        return res

    def _create_invoice(self, order, so_line, amount):
        res = super(SaleAdvancePaymentInv, self)._create_invoice( order, so_line, amount)
        if self.advance_payment_method == 'fixed':
            if self._context.get('acceptance_id',False):
                acceptance_id = self.env['project.acceptance'].browse(self._context.get('acceptance_id',False))
                acceptance_id.write({'invoice_ids' : [(4,res.id)]})
                res.invoice_line_ids.write({'name':acceptance_id.name or ''})
        return res

