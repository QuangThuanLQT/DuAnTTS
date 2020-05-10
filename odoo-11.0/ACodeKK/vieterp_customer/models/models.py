# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class vieterp_customer(models.Model):
    _inherit = 'res.partner'

    ngay_gd_cuoi_cung = fields.Date(string='Ngày giao dịch cuối cùng')
    trang_thai = fields.Selection([('allow', 'Cho phép kinh doanh'), ('stop', 'Ngừng kinh doanh')], string='Trạng thái')


class account_invoice_ihr(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def create(self, vals):
        res = super(account_invoice_ihr, self).create(vals)
        res.partner_id.ngay_gd_cuoi_cung = datetime.now().date()
        return res


