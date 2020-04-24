# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import StringIO
import xlsxwriter
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import pytz
from odoo.exceptions import UserError

class tts_salary_sale_income(models.Model):
    _name = 'sale.income'

    user = fields.Many2one('res.users')
    don_hang = fields.Text()
    khach_hang = fields.Char()
    hoa_don = fields.Text()
    time_hd = fields.Date()
    amount = fields.Float(digits=(16, 0))
    thu_nhap = fields.Float(digits=(16, 0))

    @api.multi
    def update_sale_income(self):
        record = self.env['account.invoice'].search([('type', 'in', ('out_invoice', 'out_refund'))])
        for rec in record:
            product_id = self.env['sale.order'].search([('name', '=', rec.origin)]).order_line
            tn = 0
            date = datetime.strptime(rec.date_invoice, "%Y-%m-%d")
            user = self.env['sale.order'].search([('name', '=', rec.origin)]).user_id
            code = 'SKL' + str(int(user.id)) + '/' + date.strftime("%m%y")
            value = self.env['salary.sale.income'].search([('default_code', '=', code)])
            for product in product_id:
                commision = self.env['product.product'].search([('default_code', '=', product.product_default_code), ('name', '=', product.name)]).commision
                tn += product.price_subtotal * commision / 100
            if rec.type == 'out_invoice':
                sale_income = self.env['sale.income'].create({
                    'user': user.id,
                    'don_hang': rec.origin,
                    'khach_hang': rec.partner_id.name,
                    'hoa_don': rec.number,
                    'time_hd': rec.date_invoice,
                    'amount': rec.amount_untaxed,
                    'thu_nhap': tn,
                })
                if not value:
                    salary_sale = self.env['salary.sale.income'].create({
                        'default_code': code,
                        'month': date.strftime("%m/%Y"),
                        'user': user.id,
                        'doanh_so_ban_hang': rec.amount_untaxed,
                        'thuong_ban_hang': tn,
                        'thang': date.strftime("%m"),
                        'nam': date.strftime("%Y"),
                    })
                else:
                    doanh_so = value.doanh_so_ban_hang + rec.amount_untaxed
                    thuong_bh = value.thuong_ban_hang + tn
                    value.write({
                        'doanh_so_ban_hang': doanh_so,
                        'thuong_ban_hang': thuong_bh,
                    })
            else:
                sale_income = self.env['sale.income'].create({
                    'user': user.id,
                    'don_hang': rec.origin,
                    'khach_hang': rec.partner_id.name,
                    'hoa_don': rec.number,
                    'time_hd': rec.date_invoice,
                    'amount': rec.amount_untaxed,
                    'thu_nhap': -tn,
                })
                if not value:
                    salary_sale = self.env['salary.sale.income'].create({
                        'default_code': code,
                        'month': date.strftime("%m/%Y"),
                        'user': user.id,
                        'tong_tra_hang': rec.amount_untaxed,
                        'tru_tra_hang': tn,
                        'thang': date.strftime("%m"),
                        'nam': date.strftime("%Y"),
                    })
                else:
                    tra_hang = value.tong_tra_hang + rec.amount_untaxed
                    tru_th = value.tru_tra_hang + tn
                    value.write({
                        'tong_tra_hang': tra_hang,
                        'tru_tra_hang': tru_th
                    })