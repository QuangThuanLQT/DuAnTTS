# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT
import StringIO
import xlsxwriter
from lxml import etree
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

class income_inventory(models.Model):
    _name = 'income.inventory'

    def _get_default(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        if 'alpha' in base_url:
            feosco_city_id = self.env['feosco.city'].search([('name', '=', 'Hồ Chí Minh')], limit=1)
        else:
            feosco_city_id = self.env['feosco.city'].search([('name', '=', 'Đà Nẵng')], limit=1)
        return feosco_city_id.id

    picking_id = fields.Many2one('stock.picking')
    partner_id = fields.Many2one('res.partner', string='Partner', domain=[('active', '=', True)])
    is_customer = fields.Boolean(related='partner_id.customer')
    is_supplier = fields.Boolean(related='partner_id.supplier')
    income_name = fields.Char('Name', compute='get_name', store=True)
    source_sale_id = fields.Many2one('sale.order', string='Source Document', domain=[('state', '!=', 'cancel')])
    source_purchase_id = fields.Many2one('purchase.order', string='Source Document', domain=[('state', '!=', 'cancel')])
    kich_thuoc_don_hang = fields.Many2one('inventory.package.size', string="Kích thước đơn hàng")
    nhan_vien_giao_hang = fields.Many2one('res.users', string='Nhân viên giao hàng')
    delivery_done_date = fields.Datetime('Thời gian hoàn tất giao hàng')
    giao_hang_tang_cuong = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Giao hàng tăng cường', default='no')
    user_delivery_id = fields.Many2one('res.users', string='Nhân viên giao hàng')
    delivery_method = fields.Selection(
        [('warehouse', 'Tới kho lấy hàng'),
         ('delivery', 'Giao tới tận nơi'),
         ('transport', 'Giao tới nhà xe'), ], string='Phương thức giao hàng')
    city_id = fields.Many2one('feosco.city', 'Tỉnh/Thành Phố', default=_get_default)
    district_id = fields.Many2one('feosco.district', 'Quận/Huyện' , domain="[('city_id', '=', city_id)]")
    ward_id = fields.Many2one('feosco.ward', 'Phường/Xã', domain="[('district_id', '=', district_id)]")
    check_cancel = fields.Boolean(compute='_check_cancel_order', store=True, copy=False)
    create_manual = fields.Boolean(default=False)
    thu_nhap = fields.Float(digits=(16, 0), store=True)

    @api.multi
    def update_thu_nhap_delivery(self):
        record = self.env['income.inventory'].search([('check_cancel','=', 0)])
        for rec in record:
            if rec.delivery_done_date == False:
                rec.thu_nhap = 0
            elif rec.giao_hang_tang_cuong == 'no':
                if rec.ward_id == False:
                    rec.thu_nhap = 0
                else:
                    thuong_giao_hang = self.env['tts.delivery.scope'].search([('phuong_xa', '=', rec.ward_id.name), (
                    'feosco_district_id', '=', rec.district_id.name)]).thuong_giao_hang
                    if thuong_giao_hang:
                        rec.thu_nhap = rec.kich_thuoc_don_hang.number_sign * thuong_giao_hang
            else:
                thuong_giao_hang = self.env['tts.delivery.scope'].search([('phuong_xa', '=', rec.ward_id.name), (
                'feosco_district_id', '=', rec.district_id.name)]).thuong_giao_hang_tang_ca
                if thuong_giao_hang:
                    rec.thu_nhap = rec.kich_thuoc_don_hang.number_sign * thuong_giao_hang


    @api.depends('source_sale_id.state', 'source_purchase_id.state')
    def _check_cancel_order(self):
        for record in self:
            if record.source_sale_id.state == 'cancel' or record.source_purchase_id.state == 'cancel':
                record.check_cancel = True


    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            if self.partner_id.transport_route_id:
                self.city_id = self.partner_id.transport_route_id.transporter_id.feosco_city_id
                self.district_id = self.partner_id.transport_route_id.transporter_id.feosco_district_id
                self.ward_id = self.partner_id.transport_route_id.transporter_id.phuong_xa
            else:
                eosco_city_id = self.env['feosco.city'].search([('name', '=', 'Hồ Chí Minh')], limit=1)
                self.city_id = eosco_city_id


    @api.depends('partner_id', 'source_sale_id', 'source_purchase_id')
    def get_name(self):
        for record in self:
            if record.partner_id and record.partner_id.customer == True:
                record.income_name = record.source_sale_id.name
            if record.partner_id and record.partner_id.supplier == True:
                record.income_name = record.source_purchase_id.name

    def _get_datetime_utc(self, datetime_val):
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        resuft = datetime.strptime(datetime_val, DEFAULT_SERVER_DATETIME_FORMAT)
        resuft = pytz.utc.localize(resuft).astimezone(user_tz).strftime(
            '%d/%m/%Y %H:%M')
        return resuft

    @api.model
    def search_delivery_user(self, name):
        user_ids = []
        users = self.env['res.users'].search([('name', '=', name)])
        if users:
            user_ids = users.ids
        else:
            self.env.cr.execute("""SELECT users.id, partner.name 
                                            FROM res_users users 
                                            LEFT JOIN res_partner partner ON (users.partner_id = partner.id) 
                                            WHERE LOWER (name) LIKE '%s'""" % ("%" + name.lower() + "%"))
            customers = self.env.cr.fetchall()
            for customer in customers:
                user_ids.append(customer[0])
        return user_ids

    @api.model
    def export_over_data(self, response):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        quotaion_ids = self.env['income.inventory'].search(domain)
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Export Overview')

        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')

        worksheet.set_column('A:N', 20)

        summary_header = ['Nhân viên giao hàng', 'Sale Order', 'Partner', 'Thời gian hoàn tất giao hàng',
                          'Kích thước đơn hàng', 'Giao hàng tăng cường', 'Phương thức giao hàng', 'Phường/Xã giao', 'Quận/Huyện giao',
                          'Tỉnh/Thành phố giao',]

        row = 0

        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for quotaion_id in quotaion_ids:
            row += 1

            giao_hang_tang_cuong = dict(
                self.env['income.inventory'].fields_get(allfields=['giao_hang_tang_cuong'])['giao_hang_tang_cuong'][
                    'selection'])
            delivery_method = dict(
                self.env['income.inventory'].fields_get(allfields=['delivery_method'])['delivery_method'][
                    'selection'])
            delivery_done_date = ''
            if quotaion_id.delivery_done_date:
                delivery_done_date = self._get_datetime_utc(quotaion_id.delivery_done_date)

            worksheet.write(row, 0, quotaion_id.user_delivery_id.name or '', text_style)
            worksheet.write(row, 1, quotaion_id.income_name or '', text_style)
            worksheet.write(row, 2, quotaion_id.partner_id.display_name or '', text_style)
            worksheet.write(row, 3, delivery_done_date or '', text_style)
            worksheet.write(row, 4, quotaion_id.kich_thuoc_don_hang.number_sign or '', text_style)
            worksheet.write(row, 5, giao_hang_tang_cuong.get(quotaion_id.giao_hang_tang_cuong) or '', text_style)
            worksheet.write(row, 6, delivery_method.get(quotaion_id.delivery_method) or '', text_style)
            worksheet.write(row, 7, quotaion_id.ward_id.name or '', text_style)
            worksheet.write(row, 8, quotaion_id.district_id.name or '', text_style)
            worksheet.write(row, 9, quotaion_id.city_id.name or '', text_style)


        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()



