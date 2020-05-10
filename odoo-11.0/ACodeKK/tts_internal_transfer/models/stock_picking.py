# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT
import StringIO
import xlsxwriter
from lxml import etree
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class stock_picking(models.Model):
    _inherit = 'stock.picking'

    delivery_done_date = fields.Datetime('Thời gian hoàn tất giao hàng')
    city_id = fields.Many2one('feosco.city', 'Tỉnh/Thành Phố', related='sale_id.delivery_scope_id.feosco_city_id')
    district_id = fields.Many2one('feosco.district', 'Quận/Huyện',
                                  related='sale_id.delivery_scope_id.feosco_district_id')
    ward_id = fields.Many2one('feosco.ward', 'Phường/Xã', related='sale_id.delivery_scope_id.phuong_xa')
    picking_note = fields.Char(compute='get_picking_note', string='Diễn giải')
    delivery_method = fields.Selection(
        [('warehouse', 'Tới kho lấy hàng'),
         ('delivery', 'Giao tới tận nơi'),
         ('transport', 'Giao tới nhà xe'), ], string='Phương thức giao hàng', related='sale_id.delivery_method')

    don_hang_exported = fields.Char('Đơn hàng')
    export_confirm_order_sub = fields.Datetime('Thời gian xác nhận')
    receipt_confirm_order = fields.Datetime('Thời gian xác nhận')
    receipt_id = fields.Many2one('stock.picking', "Phieu Kiem Hang", store=True)
    export_confirm_order = fields.Datetime('Thời gian xác nhận', compute='get_total_order')
    total_dh_export = fields.Float('Tổng tiền', compute='get_total_order')
    export_user_pick = fields.Many2one('res.users', compute='get_total_order', string='Nhân viên lấy hàng')
    export_kiem_hang_tc = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Lấy hàng tăng cường',
                                           compute='get_total_order')
    export_user_pack = fields.Many2one('res.users', compute='get_total_order', string='Nhân viên đóng gói')
    export_dong_goi_tc = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Đóng gói tăng cường',
                                          compute='get_total_order')
    income_name = fields.Char(string='name', compute='get_income_name')

    phuong_thuc_giao_hang = fields.Selection(
        [('warehouse', 'Tới kho lấy hàng'),
         ('delivery', 'Giao tới tận nơi'),
         ('transport', 'Giao tới nhà xe'), ], compute='get_thong_tin_ptgh', readonly=True)
    dia_chi_giao_hang = fields.Char(compute='get_thong_tin_ptgh', readonly=True)
    nha_xe = fields.Char(compute='get_thong_tin_ptgh', readonly=True)
    thoi_gian_nhan_hang = fields.Char(compute='get_thong_tin_ptgh', readonly=True)

    time_accept = fields.Datetime(readonly=True)

    sum_qty_product = fields.Integer(string='Tổng số lượng', compute='get_sum_qty_product')

    user_comfirm_id = fields.Many2one('res.users', compute='get_user_comfirm_id', store=True)

    @api.depends('sale_id.confirm_user_id', 'purchase_id.validate_by')
    def get_user_comfirm_id(self):
        for rec in self:
            if rec.origin and 'RT' in rec.origin:
                user = self.env['sale.order'].search([('name','=', rec.origin_sub)]).confirm_user_id
                rec.user_comfirm_id = user.id
            if rec.origin and 'PO' in rec.origin:
                user = self.env['purchase.order'].search([('name','=', rec.origin_sub)]).validate_by
                rec.user_comfirm_id = user.id
            if rec.origin and 'SO' in rec.origin:
                user = self.env['sale.order'].search([('name','=', rec.origin_sub)]).confirm_user_id
                rec.user_comfirm_id = user.id
            if rec.origin and 'RTP' in rec.origin:
                user = self.env['purchase.order'].search([('name','=', rec.origin_sub)]).validate_by
                rec.user_comfirm_id = user.id

    @api.multi
    def get_thong_tin_ptgh(self):
        for rec in self:
            if rec.origin and 'SO' in rec.origin:
                rec.phuong_thuc_giao_hang = rec.sale_id.delivery_method
                rec.dia_chi_giao_hang = rec.sale_id.payment_address
                rec.nha_xe = rec.sale_id.transport_route_id.transporter_name
                rec.thoi_gian_nhan_hang = rec.sale_id.transport_route_id.transporter_id.time_receive
            if rec.origin and  'RTP' in rec.origin:
                rec.phuong_thuc_giao_hang = rec.purchase_id.delivery_method
                rec.dia_chi_giao_hang = rec.purchase_id.payment_address
                rec.nha_xe = rec.purchase_id.transport_route_id.transporter_name
                rec.thoi_gian_nhan_hang = rec.purchase_id.transport_route_id.transporter_id.time_receive

    @api.multi
    def get_sum_qty_product(self):
        for rec in self:
            rec.sum_qty_product = sum(rec.pack_operation_product_ids.mapped('product_qty'))

    @api.multi
    def update_time_accept(self):
        so_list = self.env['sale.order'].search([('state', 'not in', ('draft', 'sent'))])
        po_list = self.env['purchase.order'].search([('state','in',('draft','sent','bid','cancel', 'confirmed','purchase'))])
        for record_so in so_list:
            for rec_so in record_so.mapped('picking_ids'):
                rec_so.write({
                        'time_accept': record_so.confirmation_date,
                    })
        for record_po in po_list:
            for rec_po in record_po.mapped('picking_ids'):
                rec_po.write({
                        'time_accept': record_po.confirmation_date,
                    })

    @api.multi
    def _get_date_order(self):
        for record in self:
            if record.sale_id:
                record.date_base_order = record.sale_id.confirmation_date
            if record.purchase_id:
                record.date_base_order = record.purchase_id.confirmation_date

    @api.model
    def create(self, val):
        res = super(stock_picking, self).create(val)
        if res.origin:
            if 'SO' in res.origin:
                sale_id = self.env['sale.order'].search([('name', '=', res.origin_sub)], limit=1)
                if sale_id and sale_id.sale_order_return == False:
                    res.write({
                        'export_confirm_order_sub': sale_id.confirmation_date,
                        'time_accept': sale_id.confirmation_date,
                        'picking_note': sale_id.note
                    })
            if 'RTP' in res.origin:
                purchase_id = self.env['purchase.order'].search([('name', '=', res.origin_sub)], limit=1)
                if purchase_id and purchase_id.purchase_order_return == True:
                    res.write({
                        'export_confirm_order_sub': purchase_id.confirmation_date,
                        'time_accept': purchase_id.confirmation_date,
                        'picking_note': purchase_id.notes
                    })
            if 'RT0' in res.origin:
                sale_id = self.env['sale.order'].search([('name', '=', res.origin_sub)], limit=1)
                if sale_id and sale_id.sale_order_return == True:
                    res.write({
                        'receipt_confirm_order': sale_id.confirmation_date,
                        'total_dh_receipt': sale_id.amount_total,
                        'time_accept': sale_id.confirmation_date,
                        'picking_note': sale_id.note
                    })
                    if res.picking_type_code == 'internal' and res.is_internal_transfer == True:
                        sale_id.picking_ids.filtered(lambda p: p.picking_type_code == 'incoming').write({
                            'receipt_id': res.id
                        })
            if 'PO' in res.origin:
                purchase_id = self.env['purchase.order'].search([('name', '=', res.origin_sub)], limit=1)
                if purchase_id and purchase_id.purchase_order_return == False:
                    res.write({
                        'receipt_confirm_order': purchase_id.confirmation_date,
                        'total_dh_receipt': purchase_id.amount_total,
                        'time_accept': purchase_id.confirmation_date,
                        'picking_note': purchase_id.notes
                    })
                    if res.picking_type_code == 'internal' and res.is_internal_transfer == True:
                        purchase_id.picking_ids.filtered(lambda p: p.picking_type_code == 'incoming').write({
                            'receipt_id': res.id
                        })
        if res.check_is_delivery == True and res.picking_type_code == 'outgoing':
            income_data = {
                'picking_id': res.id,
                'partner_id': res.partner_id.id,
                'giao_hang_tang_cuong': res.giao_hang_tang_cuong,
                'kich_thuoc_don_hang': res.kich_thuoc_don_hang.id,
                'user_delivery_id': res.user_delivery_id.id,
            }
            if 'SO' in res.origin:
                sale_id = self.env['sale.order'].search([('name', '=', res.origin)], limit=1)
                if sale_id and sale_id.sale_order_return == False:
                    income_data.update({
                        'source_sale_id': sale_id.id,
                        'income_name': sale_id.name,
                        'delivery_method': sale_id.delivery_method
                    })
                    if sale_id.delivery_method == 'delivery':
                        income_data.update({
                            'city_id': sale_id.partner_id.feosco_city_id.id,
                            'district_id': sale_id.partner_id.feosco_district_id.id,
                            'ward_id': sale_id.partner_id.feosco_ward_id.id,
                        })
                    elif sale_id.delivery_method == 'transport':
                        if sale_id.transport_route_id:
                            income_data.update({
                                'city_id': sale_id.transport_route_id.transporter_id.feosco_city_id.id,
                                'district_id': sale_id.transport_route_id.transporter_id.feosco_district_id.id,
                                'ward_id': sale_id.transport_route_id.transporter_id.phuong_xa.id,
                            })
            if 'RTP' in res.origin:
                purchase_id = self.env['purchase.order'].search([('name', '=', res.origin)], limit=1)
                if purchase_id and purchase_id.purchase_order_return == True:
                    # income_data['source_purchase_id'] = purchase_id.id
                    income_data.update({
                        'source_purchase_id': purchase_id.id,
                        'income_name': purchase_id.name,
                        'delivery_method': res.partner_id.delivery_method
                    })
                    if res.partner_id.delivery_method == 'delivery':
                        income_data.update({
                            'city_id': purchase_id.partner_id.feosco_city_id.id,
                            'district_id': purchase_id.partner_id.feosco_district_id.id,
                            'ward_id': purchase_id.partner_id.feosco_ward_id.id,
                        })
                    elif res.partner_id.delivery_method == 'transport':
                        if res.partner_id.transport_route_id:
                            income_data.update({
                                'city_id': res.partner_id.transport_route_id.transporter_id.feosco_city_id.id,
                                'district_id': res.partner_id.transport_route_id.transporter_id.feosco_district_id.id,
                                'ward_id': res.partner_id.transport_route_id.transporter_id.phuong_xa.id,
                            })
            income_id = self.env['income.inventory'].search([('income_name', '=', income_data.get('income_name'))])
            if not income_id:
                income_id = self.env['income.inventory'].create(income_data)
            else:
                income_id.write(income_data)

        return res

    @api.multi
    def write(self, vals):
        res = super(stock_picking, self).write(vals)
        for record in self:
            income_id = self.env['income.inventory'].search([('picking_id', '=', record.id)])
            if income_id:
                income_id.write({
                    'giao_hang_tang_cuong': record.giao_hang_tang_cuong,
                    'kich_thuoc_don_hang': record.kich_thuoc_don_hang.id,
                    'user_delivery_id': record.user_delivery_id.id,
                })
        return res

    @api.multi
    def get_income_name(self):
        for rec in self:
            if rec.sale_id:
                rec.income_name = rec.sale_id.name
            elif rec.purchase_id:
                rec.income_name = rec.purchase_id.name

    @api.multi
    def get_total_order(self):
        for record in self:
            if record.sale_id:
                record.total_dh_export = record.sale_id.amount_total
                record.export_confirm_order = record.sale_id.confirmation_date
                # record.export_confirm_order_sub = record.sale_id.confirmation_date
                pick = record.sale_id.picking_ids.filtered(lambda p: p.check_is_pick)
                for p in pick:
                    record.export_user_pick = p.user_pick_id
                    record.export_kiem_hang_tc = p.kiem_hang_tang_cuong
                pack_ids = record.sale_id.picking_ids.filtered(lambda p: p.check_is_pack)
                for pack in pack_ids:
                    record.export_user_pack = pack.user_pack_id
                    record.export_dong_goi_tc = pack.dong_goi_tang_cuong
            elif record.purchase_id:
                record.total_dh_export = record.purchase_id.amount_total
                record.export_confirm_order = record.purchase_id.confirmation_date
                # record.export_confirm_order_sub = record.purchase_id.confirmation_date
                pick = record.purchase_id.picking_ids.filtered(lambda p: p.check_is_pick)
                for p in pick:
                    record.export_user_pick = p.user_pick_id
                    record.export_kiem_hang_tc = p.kiem_hang_tang_cuong
                pack_ids = record.purchase_id.picking_ids.filtered(lambda p: p.check_is_pack)
                for pack in pack_ids:
                    record.export_user_pack = pack.user_pack_id
                    record.export_dong_goi_tc = pack.dong_goi_tang_cuong

    @api.multi
    def get_picking_note(self):
        for rec in self:
            if rec.sale_id:
                rec.picking_note = rec.sale_id.note
            elif rec.purchase_id:
                rec.picking_note = rec.purchase_id.notes
            elif rec.group_id:
                dh_name = rec.group_id.name
                if dh_name and 'PO' in dh_name:
                    purchase_id = self.env['purchase.order'].search([('name', '=', dh_name)], limit=1)
                    if purchase_id:
                        rec.picking_note = purchase_id.notes
                if dh_name and 'SO' in dh_name:
                    sale_id = self.env['sale.order'].search([('name', '=', dh_name)], limit=1)
                    if sale_id:
                        rec.picking_note = sale_id.note

    @api.multi
    def delivery_action_do_new_transfer(self):
        res = super(stock_picking, self).delivery_action_do_new_transfer()
        for rec in self:
            income_id = self.env['income.inventory'].search([('picking_id', '=', rec.id)])
            if income_id:
                income_id.write({
                    'delivery_done_date': datetime.now()
                })
        return res

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

    @api.multi
    def get_purchase_id(self):
        data = {}
        value = False
        if self.purchase_id:
            value = self.purchase_id
            data['name'] = value.name
            data['notes'] = value.notes
            data['partner_name'] = value.partner_id.name or ''
            data['user_name'] = value.validate_by.name or ''
        else:
            purchase_id = self.env['purchase.order'].search([('group_id', '=', self.group_id.id)])
            if purchase_id:
                value = purchase_id[0]
                data['name'] = value.name
                data['notes'] = value.notes
                data['partner_name'] = value.partner_id.name or ''
                data['user_name'] = value.validate_by.name or ''
        if self.sale_id:
            value = self.sale_id
            data['name'] = value.name
            data['notes'] = value.note
            data['partner_name'] = value.partner_id.name or ''
            data['user_name'] = value.user_create_return.name or ''
        return data

    def _get_datetime_utc(self, datetime_val):
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        resuft = datetime.strptime(datetime_val, DEFAULT_SERVER_DATETIME_FORMAT)
        resuft = pytz.utc.localize(resuft).astimezone(user_tz).strftime(
            '%d/%m/%Y %H:%M')
        return resuft

    @api.multi
    def update_confirm_date(self):
        picking_ids = self.search(
            ['|', ('origin', '=like', 'PO%'), ('origin', '=like', 'RT%'), ('picking_type_code', '=', 'incoming')])
        for picking in picking_ids:
            if 'RT0' in picking.origin and picking.sale_id and picking.sale_id.sale_order_return == True:
                sale_id = picking.sale_id
                if sale_id and sale_id.sale_order_return == True:
                    picking.write({
                        'receipt_confirm_order': sale_id.confirmation_date,
                        'total_dh_receipt': sale_id.amount_total,
                        'receipt_id': sale_id.picking_ids.filtered(lambda p: p.is_internal_transfer) and
                                      sale_id.picking_ids.filtered(lambda p: p.is_internal_transfer)[0].id
                    })
            if 'PO' in picking.origin:
                purchase_id = self.env['purchase.order'].search([('name', '=', picking.origin)], limit=1)
                if purchase_id and purchase_id.purchase_order_return == False:
                    picking.write({
                        'receipt_confirm_order': purchase_id.confirmation_date,
                        'total_dh_receipt': purchase_id.amount_total,
                        'receipt_id': purchase_id.picking_ids.filtered(lambda p: p.is_internal_transfer) and
                                      purchase_id.picking_ids.filtered(lambda p: p.is_internal_transfer)[0].id
                    })

    # Export Data

    @api.model
    def export_over_data(self, response):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        quotaion_ids = self.env['stock.picking'].search(domain)
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

        summary_header = ['Nhân viên giao hàng', 'Sale Order', 'Thời gian hoàn tất giao hàng',
                          'Kích thước đơn hàng', 'Giao hàng tăng cường', 'Phường/Xã giao', 'Quận/Huyện giao',
                          'Tỉnh/Thành phố giao']

        row = 0

        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for quotaion_id in quotaion_ids:
            # user_tz = self.env.user.tz or self._context.get('tz', False) or pytz.utc
            # local = pytz.timezone(user_tz)
            # date_planned = datetime.strftime(
            #     pytz.utc.localize(datetime.strptime(quotaion_id.date_planned, DT)).astimezone(local), DT)
            row += 1

            giao_hang_tang_cuong = dict(
                self.env['stock.picking'].fields_get(allfields=['giao_hang_tang_cuong'])['giao_hang_tang_cuong'][
                    'selection'])
            delivery_done_date = ''
            if quotaion_id.delivery_done_date:
                delivery_done_date = self._get_datetime_utc(quotaion_id.delivery_done_date)

            worksheet.write(row, 0, quotaion_id.user_delivery_id.name or '', text_style)
            worksheet.write(row, 1, quotaion_id.income_name or '', text_style)
            worksheet.write(row, 2, delivery_done_date or '', text_style)
            worksheet.write(row, 3, quotaion_id.kich_thuoc_don_hang.number_sign or '', text_style)
            worksheet.write(row, 4, giao_hang_tang_cuong.get(quotaion_id.giao_hang_tang_cuong) or '', text_style)
            worksheet.write(row, 5, quotaion_id.city_id.name or '', text_style)
            worksheet.write(row, 6, quotaion_id.district_id.name or '', text_style)
            worksheet.write(row, 7, quotaion_id.ward_id.name or '', text_style)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    @api.model
    def print_exported_overview(self, response):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        quotaion_ids = self.env['stock.picking'].search(domain)
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

        summary_header = ['Đơn hàng', 'Thời gian xác nhận', 'Tổng tiền', 'Nhân viên lấy hàng', 'Lấy hàng tăng cường',
                          'Nhân viên đóng gói', 'Đóng gói tăng cường', 'Nhân viên giao hàng', 'Giao hàng tăng cường']

        row = 0

        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for quotaion_id in quotaion_ids:
            # user_tz = self.env.user.tz or self._context.get('tz', False) or pytz.utc
            # local = pytz.timezone(user_tz)
            # date_planned = datetime.strftime(
            #     pytz.utc.localize(datetime.strptime(quotaion_id.date_planned, DT)).astimezone(local), DT)
            row += 1

            export_kiem_hang_tc = dict(
                self.env['stock.picking'].fields_get(allfields=['kiem_hang_tang_cuong'])['kiem_hang_tang_cuong'][
                    'selection'])
            export_dong_goi_tc = dict(
                self.env['stock.picking'].fields_get(allfields=['dong_goi_tang_cuong'])['dong_goi_tang_cuong'][
                    'selection'])
            giao_hang_tang_cuong = dict(
                self.env['stock.picking'].fields_get(allfields=['giao_hang_tang_cuong'])['giao_hang_tang_cuong'][
                    'selection'])
            export_confirm_order_sub = ''
            if quotaion_id.export_confirm_order_sub:
                export_confirm_order_sub = self._get_datetime_utc(quotaion_id.export_confirm_order_sub)
            worksheet.write(row, 0, quotaion_id.origin or '', text_style)
            worksheet.write(row, 1, export_confirm_order_sub or '', text_style)
            worksheet.write(row, 2, quotaion_id.total_dh_export or '', body_bold_color_number)
            worksheet.write(row, 3, quotaion_id.export_user_pick.name or '', text_style)
            worksheet.write(row, 4, export_kiem_hang_tc.get(quotaion_id.export_kiem_hang_tc) or '', text_style)

            worksheet.write(row, 5, quotaion_id.export_user_pack.name or '', text_style)
            worksheet.write(row, 6, export_dong_goi_tc.get(quotaion_id.export_dong_goi_tc) or '', text_style)

            worksheet.write(row, 7, quotaion_id.user_delivery_id.name or '', text_style)
            worksheet.write(row, 8, giao_hang_tang_cuong.get(quotaion_id.giao_hang_tang_cuong) or '', text_style)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()


class inventory_package_size(models.Model):
    _inherit = "inventory.package.size"

    @api.multi
    def name_get(self):
        if not self._context.get('show_numbersign', False):  # TDE FIXME: not used
            return [(value.id, str(value.name)) for value in self]
        return [(value.id, str(value.number_sign)) for value in self]
