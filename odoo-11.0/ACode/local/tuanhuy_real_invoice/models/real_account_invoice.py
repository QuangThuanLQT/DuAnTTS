# -*- coding: utf-8 -*-
from odoo import models, fields, api

class real_invoice(models.Model):
    _name = 'real.invoice'

    invoice_date_real       = fields.Date('Ngày Hoá Đơn Thực')
    invoice_number_real     = fields.Char('Số Hoá Đơn Thực')
    invoice_total_real      = fields.Float('Giá Trị Hoá Đơn Thực')
    invoice_id              = fields.Many2one('account.invoice')

class account_invoice(models.Model):
    _inherit = 'account.invoice'

    real_invoice_ids    = fields.One2many('real.invoice','invoice_id')