# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
import StringIO
import xlsxwriter
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo.tools import float_compare, float_round, float_repr


class modifier_sale_order_inherit(models.Model):
    _inherit= 'sale.order'

    @api.multi
    def directly_create_inv(self):
        res = super(modifier_sale_order_inherit, self).directly_create_inv()
        invoice_id = self.env['account.invoice'].search([('origin', '=', self.name)])
        product_id = self.env['sale.order'].search([('name', '=', self.name)]).order_line
        tn = 0
        for product in product_id:
            commision = self.env['product.product'].search([('default_code', '=', product.product_default_code)]).commision
            tn += product.price_subtotal * commision / 100
        sale_income = self.env['sale.income'].create({
                    'user': self.user_id.id,
                    'don_hang': self.name,
                    'khach_hang': self.partner_id.name,
                    'hoa_don': invoice_id.number,
                    'time_hd': invoice_id.date_invoice,
                    'amount': self.amount_untaxed,
                    'thu_nhap': tn
                })

        code = 'SKL' + str(int(self.user_id.id)) + '/' + datetime.now().strftime("%m%y")
        value = self.env['salary.sale.income'].search([('default_code', '=', code)])
        if not value:
            salary_sale = self.env['salary.sale.income'].create({
                'default_code': code,
                'month': datetime.now().strftime("%m/%Y"),
                'user': self.user_id.id,
                'doanh_so_ban_hang': self.amount_untaxed,
                'thuong_ban_hang': tn,
                'thang': datetime.now().strftime("%m"),
                'nam': datetime.now().strftime("%Y"),
            })
        else:
            doanh_so = value.doanh_so_ban_hang + self.amount_untaxed
            thuong_bh = value.thuong_ban_hang + tn
            value.write({
                'doanh_so_ban_hang': doanh_so,
                'thuong_ban_hang': thuong_bh,
            })
        return res

    @api.multi
    def create_invoice_return(self):
        res = super(modifier_sale_order_inherit, self).create_invoice_return()
        invoice_id = self.env['account.invoice'].search([('origin', '=', self.name)])
        product_id = self.env['sale.order'].search([('name', '=', self.name)]).order_line
        tn = 0
        for product in product_id:
            commision = self.env['product.product'].search(
                [('default_code', '=', product.product_default_code)]).commision
            tn += product.price_subtotal * commision / 100
        sale_income = self.env['sale.income'].create({
            'user': self.user_id.id,
            'don_hang': self.name,
            'khach_hang': self.partner_id.name,
            'hoa_don': invoice_id.number,
            'time_hd': invoice_id.date_invoice,
            'amount': self.amount_untaxed,
            'thu_nhap': -tn
        })

        code = 'SKL' + str(int(self.user_id.id)) + '/' + datetime.now().strftime("%m%y")
        value = self.env['salary.sale.income'].search([('default_code', '=', code)])
        if not value:
            salary_sale = self.env['salary.sale.income'].create({
                'default_code': code,
                'month': datetime.now().strftime("%m/%Y"),
                'user': self.user_id.id,
                'tong_tra_hang': self.amount_untaxed,
                'tru_tra_hang': tn,
                'thang': datetime.now().strftime("%m"),
                'nam': datetime.now().strftime("%Y"),
            })
        else:
            tra_hang = value.tong_tra_hang + self.amount_untaxed
            tru_th = value.tru_tra_hang + tn
            value.write({
                'tong_tra_hang': tra_hang,
                'tru_tra_hang': tru_th
            })
        return res
