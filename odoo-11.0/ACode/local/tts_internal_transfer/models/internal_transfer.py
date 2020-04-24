# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import StringIO
import xlsxwriter
from lxml import etree
import base64
import pytz


class stock_picking_ihr(models.Model):
    _inherit = 'stock.picking'

    is_internal_transfer = fields.Boolean(compute='check_is_internal_transfer')
    user_checking_id = fields.Many2one('res.users', string='Nhân viên kiểm hàng', track_visibility='onchange')
    kiem_hang_tang_cuong = fields.Selection([('no', 'No'), ('yes', 'Yes')], default='no', string='Soạn hàng tăng cường',
                                            track_visibility='onchange')
    dong_goi_tang_cuong = fields.Selection([('no', 'No'), ('yes', 'Yes')], default='no', string='Đóng Gói tăng cường',
                                           track_visibility='onchange')
    giao_hang_tang_cuong = fields.Selection([('no', 'No'), ('yes', 'Yes')], default='no', string='Giao hàng tăng cường',
                                            track_visibility='onchange')
    user_purchase_id = fields.Many2one('res.users', string='Nhân viên mua hàng', compute='get_user_purchase_id')
    kho_luu_tru = fields.Selection([('normal', 'Kho bình thường'), ('error', 'Hàng Lỗi')], string='Kho lưu trữ',
                                   default='normal')
    internal_transfer_state = fields.Selection([('draft', 'Bản thảo'), ('waiting_another', 'Chờ hoạt động khác'),
                                                ('waiting', 'Chờ kiểm hàng'), ('checking', 'Đang kiểm hàng'),
                                                ('done', 'Hoàn thành'), ('cancel', 'Cancel')], default='draft')
    stock_picking_log_ids = fields.One2many('stock.picking.log', 'picking_id', string='History Log')

    receiver = fields.Many2one('res.users', 'Nhân viên nhận hàng', track_visibility='onchange')
    receive_increase = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Nhận hàng tăng cường', default='no',
                                        track_visibility='onchange')
    receipt_state = fields.Selection(
        [('draft', 'Bản thảo'), ('reveive', 'Nhận hàng'), ('done', 'Hoàn thành'), ('cancel', 'Cancel')],
        default='draft')

    is_orther_picking = fields.Boolean(compute='check_is_orther_picking')
    picking_state_show = fields.Char(string='Trạng thái', compute='get_picking_state_show')
    don_hang_receipt = fields.Char(compute='_get_don_hang_receipt', string='Đơn hàng')
    total_dh_receipt = fields.Float(string='Tổng tiền', store=True, compute=False)
    user_checking_receipt = fields.Char(compute='_get_don_hang_receipt', string='Nhân viên kiểm hàng', store=True)
    checking_increase_receipt = fields.Char(compute='_get_don_hang_receipt', string='Kiểm hàng tăng cường', store=True)

    @api.multi
    def _compute_sale_order(self):
        for record in self:
            for move in record.move_lines:
                if move.group_id and move.group_id.id:
                    sale_id = self.env['sale.order'].search([
                        ('procurement_group_id', '=', move.group_id.id),
                    ], limit=1)
                    record.sale_id = sale_id
                    break

    @api.multi
    def action_cancel(self):
        res = super(stock_picking_ihr, self).action_cancel()
        for rec in self:
            if rec.state == 'cancel':
                if rec.check_is_pick:
                    rec.state_pick = 'cancel'
                elif rec.check_is_pack:
                    rec.state_pack = 'cancel'
                elif rec.check_is_delivery:
                    rec.state_delivery = 'cancel'
                elif rec.is_internal_transfer:
                    rec.internal_transfer_state = 'cancel'
                elif rec.is_orther_picking:
                    pass
                else:
                    rec.receipt_state = 'cancel'
        return res

    @api.depends('receipt_id.user_checking_id', 'receipt_id.kiem_hang_tang_cuong')
    def _get_don_hang_receipt(self):
        for rec in self:
            if rec.receipt_id:
                rec.user_checking_receipt = rec.receipt_id.user_checking_id.name or ''
                rec.checking_increase_receipt = 'No' if rec.receipt_id.kiem_hang_tang_cuong == 'no' else 'Yes'
                # if rec.picking_type_code == 'incoming':
                #     if rec.sale_id:
                #         rec.don_hang_receipt = rec.sale_id.name
                #         # rec.total_dh_receipt = rec.sale_id.amount_total
                #         picking_ids = rec.sale_id.picking_ids.filtered(lambda p: p.is_internal_transfer)
                #         if picking_ids:
                #             rec.user_checking_receipt = picking_ids[0].user_checking_id.name or ''
                #             rec.checking_increase_receipt = 'No' if picking_ids[0].kiem_hang_tang_cuong == 'no' else 'Yes'
                #     elif rec.purchase_id:
                #         rec.don_hang_receipt = rec.purchase_id.name
                #         # rec.total_dh_receipt = rec.purchase_id.amount_total
                #         picking_ids = rec.purchase_id.picking_ids.filtered(lambda p: p.is_internal_transfer)
                #         if picking_ids:
                #             rec.user_checking_receipt = picking_ids[0].user_checking_id.name or ''
                #             rec.checking_increase_receipt = 'No' if picking_ids[0].kiem_hang_tang_cuong == 'no' else 'Yes'
                #     elif rec.group_id:
                #         dh_name = rec.group_id.name
                #         if dh_name and 'PO' in dh_name:
                #             purchase_id = self.env['purchase.order'].search([('name','=',dh_name)],limit=1)
                #             if purchase_id:
                #                 rec.don_hang_receipt = purchase_id.name
                #                 # rec.total_dh_receipt = purchase_id.amount_total
                #         if dh_name and 'SO' in dh_name:
                #             sale_id = self.env['sale.order'].search([('name', '=', dh_name)], limit=1)
                #             if sale_id:
                #                 rec.don_hang_receipt = sale_id.name
                #                 # rec.total_dh_receipt = sale_id.amount_total

    @api.multi
    def get_picking_state_show(self):
        for rec in self:
            if rec.check_is_pick:
                state_pick = dict(self.fields_get(['state_pick'])['state_pick']['selection'])
                rec.picking_state_show = state_pick[rec.state_pick]
            elif rec.check_is_pack:
                state_pack = dict(self.fields_get(['state_pack'])['state_pack']['selection'])
                if rec.state_pack == 'waiting_pick':
                    rec.picking_state_show = state_pack['waiting_pack']
                else:
                    rec.picking_state_show = state_pack[rec.state_pack]
            elif rec.check_is_delivery:
                state_delivery = dict(self.fields_get(['state_delivery'])['state_delivery']['selection'])
                rec.picking_state_show = state_delivery[rec.state_delivery]
            elif rec.is_internal_transfer:
                internal_transfer_state = dict(
                    self.fields_get(['internal_transfer_state'])['internal_transfer_state']['selection'])
                rec.picking_state_show = internal_transfer_state[rec.internal_transfer_state]
            elif rec.picking_type_code == 'incoming':
                receipt_state = dict(self.fields_get(['receipt_state'])['receipt_state']['selection'])
                rec.picking_state_show = receipt_state[rec.receipt_state]
            else:
                state = dict(self.fields_get(['state'])['state']['selection'])
                rec.picking_state_show = state[rec.state]

    @api.multi
    def get_user_purchase_id(self):
        for rec in self:
            if rec.purchase_id:
                rec.user_purchase_id = rec.purchase_id.validate_by
            else:
                if rec.group_id:
                    purchase_id = self.env['purchase.order'].search([('group_id', '=', rec.group_id.id)])
                    rec.user_purchase_id = purchase_id.validate_by

    @api.onchange('picking_type_id')
    def check_is_orther_picking(self):
        for rec in self:
            if not rec.is_internal_transfer and not rec.check_is_pick and not rec.check_is_pack and not rec.check_is_delivery and rec.picking_type_code != 'incoming':
                rec.is_orther_picking = True
            else:
                rec.is_orther_picking = False

    @api.multi
    def do_new_transfer(self):
        res = super(stock_picking_ihr, self).do_new_transfer()
        for rec in self:
            if rec.picking_type_code == 'incoming':
                internal_id = rec.mapped('move_lines').mapped('move_dest_id').mapped('picking_id')
                if internal_id:
                    internal_id[0].internal_transfer_state = 'waiting'
            if rec.is_orther_picking == True:
                rec.write({
                    'time_accept': fields.Datetime.now(),
                    'user_comfirm_id': self.env.uid,
                })
        return res

    @api.model
    def create(self, val):
        res = super(stock_picking_ihr, self).create(val)
        origin = res.origin or ''
        if res.is_internal_transfer:
            res.internal_transfer_state = 'waiting_another'
        elif res.picking_type_code == 'incoming' and ('PO' in origin or 'RT' in origin):
            res.receipt_state = 'reveive'
        return res

    # TODO button picking receipt
    @api.multi
    def receipt_action_confirm(self):
        for rec in self:
            if rec.receipt_state == 'draft':
                rec.receipt_state = 'reveive'
                rec.action_confirm()

    @api.multi
    def receipt_action_do_new_transfer(self):
        for rec in self:
            if rec.state == 'assigned':
                rec.do_new_transfer()
                rec.receipt_state = 'done'
            else:
                rec.action_assign()
                if rec.state == 'assigned':
                    rec.do_new_transfer()
                    rec.receipt_state = 'done'

    # TODO button picking receipt
    @api.multi
    def internal_action_confirm(self):
        for rec in self:
            if rec.internal_transfer_state == 'draft':
                rec.action_confirm()
                rec.internal_transfer_state = 'waiting'

    @api.multi
    def internal_action_assign(self):
        for rec in self:
            if rec.internal_transfer_state == 'waiting':
                rec.internal_transfer_state = 'checking'

    @api.multi
    def internal_action_do_new_transfer(self):
        for rec in self:
            if rec.state == 'assigned':
                rec.do_new_transfer()
                rec.internal_transfer_state = 'done'
            else:
                rec.action_assign()
                if rec.state == 'assigned':
                    rec.do_new_transfer()
                    rec.internal_transfer_state = 'done'

    def _get_datetime_utc(self, datetime_val):
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        resuft = datetime.strptime(datetime_val, DEFAULT_SERVER_DATETIME_FORMAT)
        resuft = pytz.utc.localize(resuft).astimezone(user_tz).strftime(
            '%Y/%m/%d %H:%M')
        return resuft

    @api.multi
    def print_receipt_history_excel(self, response):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        domain.append(('picking_type_id.code', '=', 'incoming'))
        picking_ids = self.env['stock.picking'].search(domain)
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Lich su nhan hang')

        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter', 'text_wrap': True})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')

        worksheet.set_column('A:G', 20)

        summary_header = ['Đơn hàng', 'Thời gian xác nhận', 'Tổng tiền', 'Nhân viên nhận hàng',
                          'Nhận hàng tăng cường',
                          'Nhân viên kiểm hàng',
                          'Kiểm hàng tăng cường', ]
        row = 0
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for picking_id in picking_ids:
            row += 1
            receipt_confirm_order = ''
            if picking_id.receipt_confirm_order:
                receipt_confirm_order = self._get_datetime_utc(picking_id.receipt_confirm_order)
            worksheet.write(row, 0, picking_id.origin or '', text_style)
            worksheet.write(row, 1, receipt_confirm_order or '', text_style)
            worksheet.write(row, 2, picking_id.total_dh_receipt or '', body_bold_color_number)
            worksheet.write(row, 3, picking_id.receiver.name or '', text_style)
            worksheet.write(row, 4, 'No' if picking_id.receive_increase == 'no' else 'Yes', text_style)
            worksheet.write(row, 5, picking_id.user_checking_receipt or '', text_style)
            worksheet.write(row, 6, picking_id.checking_increase_receipt or '', text_style)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    @api.multi
    def print_picking_receipt_excel(self, response):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        domain.append(('picking_type_id.code', '=', 'incoming'))
        picking_ids = self.env['stock.picking'].search(domain)
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Export Receipt time log')

        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter', 'text_wrap': True})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')

        worksheet.set_column('A:I', 20)

        summary_header = ['Mã đơn hàng mua', 'Mã đơn trả hàng bán', 'Thời gian tạo Purchase Quotation',
                          'Thời gian chuyển từ Quotation sang Purchase Order',
                          'Thời gian tạo phiếu Nhận hàng có Receive status = Waiting',
                          'Thời gian tạo phiếu Kiểm hàng có Check & Storage status = Waiting',
                          'Thời gian tạo phiếu Kiểm hàng có Check & Storage status = Checking',
                          'Thời gian tạo phiếu Kiểm hàng có Check & Storage status = Done',
                          'Trạng thái đơn hàng']
        row = 0
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for picking_id in picking_ids:
            if (picking_id.sale_id or picking_id.purchase_id) and not picking_id.check_is_pick and not picking_id.check_is_pack:
                row += 1
                row_0 = row_1 = row_2 = row_3 = row_4 = row_5 = row_6 = row_7 = row_8 = ''
                if picking_id.sale_id:
                    row_1 = picking_id.sale_id.name
                    row_2 = self._get_datetime_utc(picking_id.sale_id.date_order)
                    row_3 = self._get_datetime_utc(picking_id.time_accept)
                    picking_transfer = picking_id.sale_id.picking_ids.filtered(lambda p: p.is_internal_transfer)
                    if picking_transfer:
                        picking_transfer = picking_transfer[0]
                        for line in picking_transfer.stock_picking_log_ids:
                            if line.status_changed:
                                state = line.status_changed.split('->')[1].strip()
                                if state == 'Chờ kiểm hàng':
                                    row_5 = self._get_datetime_utc(line.time_log)
                                elif state == 'Đang kiểm hàng':
                                    row_6 = self._get_datetime_utc(line.time_log)
                                elif state == 'Hoàn thành':
                                    row_7 = self._get_datetime_utc(line.time_log)
                    if picking_id.sale_id.trang_thai_dh:
                        row_8 = dict(picking_id.sale_id.fields_get(['trang_thai_dh'])['trang_thai_dh']['selection'])[
                            picking_id.sale_id.trang_thai_dh]
                elif picking_id.purchase_id:
                    row_0 = picking_id.purchase_id.name
                    row_2 = self._get_datetime_utc(picking_id.purchase_id.date_order)
                    row_3 = self._get_datetime_utc(
                        picking_id.time_accept) if picking_id.time_accept else ''
                    picking_transfer = picking_id.purchase_id.picking_ids.filtered(lambda p: p.is_internal_transfer)
                    if picking_transfer:
                        picking_transfer = picking_transfer[0]
                        for line in picking_transfer.stock_picking_log_ids:
                            if line.status_changed:
                                state = line.status_changed.split('->')[1].strip()
                                if state == 'Chờ kiểm hàng':
                                    row_5 = self._get_datetime_utc(line.time_log)
                                elif state == 'Đang kiểm hàng':
                                    row_6 = self._get_datetime_utc(line.time_log)
                                elif state == 'Hoàn thành':
                                    row_7 = self._get_datetime_utc(line.time_log)
                    if picking_id.purchase_id.operation_state:
                        row_8 = \
                            dict(
                                picking_id.purchase_id.fields_get(['operation_state'])['operation_state']['selection'])[
                                picking_id.purchase_id.operation_state]

                for line in picking_id.stock_picking_log_ids:
                    if line.status_changed:
                        state = line.status_changed.split('->')[1].strip()
                        if state == 'Nhận hàng':
                            row_4 = self._get_datetime_utc(line.time_log)

                # state = dict(self.env['sale.order'].fields_get(allfields=['state'])['state'][
                #                  'selection'])
                worksheet.write(row, 0, row_0, text_style)
                worksheet.write(row, 1, row_1, text_style)
                worksheet.write(row, 2, row_2, text_style)
                worksheet.write(row, 3, row_3, text_style)
                worksheet.write(row, 4, row_4, text_style)
                worksheet.write(row, 5, row_5, text_style)
                worksheet.write(row, 6, row_6, text_style)
                worksheet.write(row, 7, row_7, text_style)
                worksheet.write(row, 8, row_8, text_style)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    @api.multi
    def print_delivery_export_excel(self, response):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        domain.append(('picking_type_id.code', '=', 'outgoing'))
        domain.append(('state', '!=', 'cancel'))
        picking_ids = self.env['stock.picking'].search(domain)
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Export Delivery time log')

        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter', 'text_wrap': True})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')

        worksheet.set_column('A:L', 20)

        summary_header = ['Mã đơn hàng bán (SO)', 'Mã đơn trả hàng NCC (Return)', 'Thời gian tạo Sale Quotation',
                          'Thời gian tạo phiếu Pick có Pick status = Waiting',
                          'Thời gian tạo phiếu Pick có Pick status =  Ready',
                          'Thời gian tạo phiếu Pick có Pick status = Picking',
                          'Thời gian tạo phiếu Pack có Pack status = Waiting',
                          'Thời gian tạo phiếu Pack có Pack status = Packing',
                          'Thời gian tạo phiếu Delivery có Delivery status = Waiting',
                          'Thời gian tạo phiếu Delivery có Delivery status = Delivering',
                          'Thời gian tạo phiếu Delivery có Delivery status = Done',
                          'Trạng thái đơn hàng']
        row = 0
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for picking_id in picking_ids:
            if (
                        picking_id.sale_id or picking_id.purchase_id) and not picking_id.check_is_pick and not picking_id.check_is_pack:
                row += 1
                row_0 = row_1 = row_2 = row_3 = row_4 = row_5 = row_6 = row_7 = row_8 = row_9 = row_10 = row_11 = ''
                if picking_id.sale_id:
                    row_0 = picking_id.sale_id.name
                    row_2 = self._get_datetime_utc(picking_id.sale_id.date_order)
                    picking_pick = picking_id.sale_id.picking_ids.filtered(lambda p: p.check_is_pick)
                    if picking_pick:
                        picking_pick = picking_pick[0]
                        for line in picking_pick.stock_picking_log_ids:
                            if line.status_changed:
                                state = line.status_changed.split('->')[1].strip()
                                row_3 = self._get_datetime_utc(picking_pick.sale_id.confirmation_date)
                                if state == 'Waiting':
                                    row_3 = self._get_datetime_utc(line.time_log)
                                elif state == 'Ready':
                                    row_4 = self._get_datetime_utc(line.time_log)
                                elif state == 'Done':
                                    row_5 = self._get_datetime_utc(line.time_log)

                    picking_pack = picking_id.sale_id.picking_ids.filtered(lambda p: p.check_is_pack)
                    if picking_pack:
                        picking_pack = picking_pack[0]
                        for line in picking_pack.stock_picking_log_ids:
                            if line.status_changed:
                                state = line.status_changed.split('->')[1].strip()
                                if state == 'Waiting':
                                    row_6 = self._get_datetime_utc(line.time_log)
                                elif state == 'Packing':
                                    row_7 = self._get_datetime_utc(line.time_log)

                    for line in picking_id.stock_picking_log_ids:
                        if line.status_changed:
                            state = line.status_changed.split('->')[1].strip()
                            if state == 'Waiting':
                                row_8 = self._get_datetime_utc(line.time_log)
                            elif state == 'Delivering':
                                row_9 = self._get_datetime_utc(line.time_log)
                            elif state == 'Done':
                                row_10 = self._get_datetime_utc(line.time_log)

                    state = dict(self.env['sale.order'].fields_get(['trang_thai_dh'])['trang_thai_dh']['selection'])
                    if picking_id.sale_id.trang_thai_dh:
                        row_11 = state[picking_id.sale_id.trang_thai_dh]
                    else:
                        row_11 = ''
                elif picking_id.purchase_id:
                    row_1 = picking_id.purchase_id.name
                    row_2 = self._get_datetime_utc(picking_id.purchase_id.date_order)
                    picking_pick = picking_id.purchase_id.picking_ids.filtered(lambda p: p.check_is_pick)
                    if picking_pick:
                        picking_pick = picking_pick[0]
                        for line in picking_pick.stock_picking_log_ids:
                            if line.status_changed:
                                state = line.status_changed.split('->')[1].strip()
                                row_3 = self._get_datetime_utc(picking_pick.purchase_id.confirmation_date)
                                if state == 'Waiting':
                                    row_3 = self._get_datetime_utc(line.time_log)
                                elif state == 'Ready':
                                    row_4 = self._get_datetime_utc(line.time_log)
                                elif state == 'Done':
                                    row_5 = self._get_datetime_utc(line.time_log)

                    picking_pack = picking_id.purchase_id.picking_ids.filtered(lambda p: p.check_is_pack)
                    if picking_pack:
                        picking_pack = picking_pack[0]
                        for line in picking_pack.stock_picking_log_ids:
                            if line.status_changed:
                                state = line.status_changed.split('->')[1].strip()
                                if state == 'Waiting':
                                    row_6 = self._get_datetime_utc(line.time_log)
                                elif state == 'Packing':
                                    row_7 = self._get_datetime_utc(line.time_log)

                    for line in picking_id.stock_picking_log_ids:
                        if line.status_changed:
                            state = line.status_changed.split('->')[1].strip()
                            if state == 'Waiting':
                                row_8 = self._get_datetime_utc(line.time_log)
                            elif state == 'Delivering':
                                row_9 = self._get_datetime_utc(line.time_log)
                            elif state == 'Done':
                                row_10 = self._get_datetime_utc(line.time_log)
                    if picking_id.purchase_id.operation_state:
                        row_11 = dict(
                            picking_id.purchase_id.fields_get(['operation_state'])['operation_state']['selection'])[
                            picking_id.purchase_id.operation_state]

                # state = dict(self.env['sale.order'].fields_get(allfields=['state'])['state'][
                #                  'selection'])
                worksheet.write(row, 0, row_0, text_style)
                worksheet.write(row, 1, row_1, text_style)
                worksheet.write(row, 2, row_2, text_style)
                worksheet.write(row, 3, row_3, text_style)
                worksheet.write(row, 4, row_4, text_style)
                worksheet.write(row, 5, row_5, text_style)
                worksheet.write(row, 6, row_6, text_style)
                worksheet.write(row, 7, row_7, text_style)
                worksheet.write(row, 8, row_8, text_style)
                worksheet.write(row, 9, row_9, text_style)
                worksheet.write(row, 10, row_10, text_style)
                worksheet.write(row, 11, row_11, text_style)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    @api.multi
    def print_internal_product_data(self):
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Phieu Noi Bo')
        body_bold_color = workbook.add_format({'bold': True})
        worksheet.set_column('A:A', 15)
        worksheet.set_column('B:B', 50)
        worksheet.set_column('C:C', 15)

        row = 0
        summary_header = ['Mã sản phẩm', 'Tên sản phẩm', 'Số lượng']
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color)
         for
         header_cell in
         range(0, len(summary_header)) if summary_header[header_cell]]
        row += 1
        for line in self.pack_operation_product_ids:
            variable_attributes = line.product_id.attribute_line_ids.filtered(lambda l: len(l.value_ids) >= 1).mapped(
                'attribute_id')
            variant = line.product_id.attribute_value_ids._variant_name(variable_attributes)

            name = variant and "%s (%s)" % (line.product_id.name, variant) or line.product_id.name
            worksheet.write(row, 0, line.product_id.default_code, )
            worksheet.write(row, 1, name, )
            worksheet.write(row, 2, line.product_qty, )
            row += 1

        name_sheet = '%s - %s.xlsx' % (self.origin, self.partner_id.display_name)
        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create(
            {'name': name_sheet, 'datas_fname': name_sheet, 'datas': result})
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        return {"type": "ir.actions.act_url",
                "url": str(download_url)}

    @api.multi
    def write(self, val):
        if 'kho_luu_tru' in val:
            for rec in self:
                if val.get('kho_luu_tru', False) == 'normal':
                    location_dest_id = rec.picking_type_id.default_location_dest_id.id
                else:
                    location_dest_id = self.env['stock.location'].search(
                        [('usage', '=', 'internal'), ('not_sellable', '=', True)], limit=1)
                if location_dest_id and rec.check_return_picking and rec.is_internal_transfer and rec.state != 'done':
                    rec.location_dest_id = location_dest_id
                    for line in rec.move_lines:
                        line.location_dest_id = location_dest_id
                    rec.do_unreserve()
                    rec.force_assign()
                    rec.action_assign()

        if 'internal_transfer_state' in val:
            for rec in self:
                old_state = rec.internal_transfer_state
                new_state = val.get('internal_transfer_state')
                state = dict(self.fields_get(['internal_transfer_state'])['internal_transfer_state']['selection'])
                status_changed = "%s -> %s" % (state[old_state], state[new_state])
                history_data = {
                    'status_changed': status_changed,
                    'time_log': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    'picking_id': rec.id,
                }
                self.env['stock.picking.log'].create(history_data)
        if 'receipt_state' in val:
            for rec in self:
                old_state = rec.receipt_state
                new_state = val.get('receipt_state')
                state = dict(self.fields_get(['receipt_state'])['receipt_state']['selection'])
                status_changed = "%s -> %s" % (state[old_state], state[new_state])
                history_data = {
                    'status_changed': status_changed,
                    'time_log': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    'picking_id': rec.id,
                }
                self.env['stock.picking.log'].create(history_data)
        if 'state_pick' in val:
            for rec in self:
                old_state = rec.state_pick
                new_state = val.get('state_pick')
                state = dict(self.fields_get(['state_pick'])['state_pick']['selection'])
                status_changed = "%s -> %s" % (state[old_state], state[new_state])
                history_data = {
                    'status_changed': status_changed,
                    'time_log': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    'picking_id': rec.id,
                }
                self.env['stock.picking.log'].create(history_data)
        if 'state_pack' in val:
            for rec in self:
                old_state = rec.state_pack
                new_state = val.get('state_pack')
                state = dict(self.fields_get(['state_pack'])['state_pack']['selection'])
                status_changed = "%s -> %s" % (state[old_state], state[new_state])
                history_data = {
                    'status_changed': status_changed,
                    'time_log': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    'picking_id': rec.id,
                }
                self.env['stock.picking.log'].create(history_data)
        if 'state_delivery' in val:
            for rec in self:
                old_state = rec.state_delivery
                new_state = val.get('state_delivery')
                state = dict(self.fields_get(['state_delivery'])['state_delivery']['selection'])
                status_changed = "%s -> %s" % (state[old_state], state[new_state])
                history_data = {
                    'status_changed': status_changed,
                    'time_log': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    'picking_id': rec.id,
                }
                self.env['stock.picking.log'].create(history_data)
        res = super(stock_picking_ihr, self).write(val)
        return res

    @api.onchange('picking_type_id')
    def check_is_internal_transfer(self):
        for rec in self:
            origin = rec.origin or ''
            if rec.picking_type_id.code == 'internal' and not rec.check_is_pick and not rec.check_is_pack and (
                            rec.group_id or 'PO' in origin or 'RT' in origin):
                rec.is_internal_transfer = True
            else:
                rec.is_internal_transfer = False

    @api.model
    def default_get(self, fields):
        res = super(stock_picking_ihr, self).default_get(fields)
        res['move_type'] = 'one'
        if self._context.get('default_picking_type_id', False):
            res['picking_type_id'] = self._context.get('default_picking_type_id')
        else:
            internal_picking = self.env['stock.picking.type'].search([('code', '=', 'internal')], limit=1)
            res['picking_type_id'] = internal_picking.id
        return res

    @api.model
    def get_location_list(self):
        location_ids = self.env['stock.location'].search([]).sorted('display_name', reverse=False).mapped(
            'display_name')
        return location_ids

    @api.model
    def get_inv_state_list(self):
        return [['state', 'Status']], [
            ['draft', 'Draft'],
            ['open', 'Open'],
            ['paid', 'Paid'],
            ['cancel', 'Cancel']]

    @api.model
    def get_state_list(self, active_id):
        picking_type_id = self.env['stock.picking.type'].search([('id', '=', active_id)])
        location_pack_zone = self.env.ref('stock.location_pack_zone')
        stock_location_output = self.env.ref('stock.stock_location_output')
        type = False
        if 'PICK' in picking_type_id.sequence_id.prefix or picking_type_id.default_location_dest_id == location_pack_zone:
            type = 'pick'
        elif 'PACK' in picking_type_id.sequence_id.prefix or picking_type_id.default_location_src_id == location_pack_zone:
            type = 'pack'
        elif 'OUT' in picking_type_id.sequence_id.prefix and picking_type_id.default_location_src_id == stock_location_output:
            type = 'delivery'
        elif picking_type_id.code == 'internal':
            type = 'internal'
        elif picking_type_id.code == 'incoming':
            type = 'receipt'

        if type == 'pick':
            return [['state_pick', 'Status']], [
                ['draft', 'Draft'],
                ['waiting_pick', 'Waiting'],
                ['ready_pick', 'Ready'],
                ['picking', 'Picking'],
                ['done', 'Done'],
                ['cancel', 'Cancel']]
        elif type == 'pack':
            return [['state_pack', 'Status']], \
                   [['draft', 'Draft'],
                    ['waiting_another_operation', 'Waiting another operation'],
                    ['waiting_pack', 'Waiting'],
                    ['packing', 'Packing'],
                    ['done', 'Done'],
                    ['cancel', 'Cancel']]
        elif type == 'delivery':
            return [['state_delivery', 'Status']], \
                   [['draft', 'Draft'],
                    ['waiting_another_operation', 'Waiting another operation'],
                    ['waiting_delivery', 'Waiting'],
                    ['delivery', 'Delivering'],
                    ['done', 'Done'],
                    ['cancel', 'Cancel']]
        elif type == 'internal':
            return [['internal_transfer_state', 'Status']], \
                   [['draft', 'Bản thảo'],
                    ['waiting_another', 'Chờ hoạt động khác'],
                    ['waiting', 'Chờ kiểm hàng'],
                    ['checking', 'Đang kiểm hàng'],
                    ['done', 'Hoàn thành']]
        elif type == 'receipt':
            return [['receipt_state', 'Status']], \
                   [['draft', 'Bản thảo'],
                    ['reveive', 'Nhận hàng'],
                    ['done', 'Hoàn thành']]
        else:
            return False, False

    @api.model
    def get_picking_search(self, location, type):
        if location:
            location_list = location.split('/')
            parent_id = False
            for location in location_list:
                domain = [('name', '=', location.strip())]
                if not parent_id:
                    locaiton_id = self.env['stock.location'].search(domain)
                    if not locaiton_id:
                        break
                    parent_id = locaiton_id
                else:
                    domain.append(('location_id', '=', parent_id.id))
                    locaiton_id = self.env['stock.location'].search(domain)
                    if not locaiton_id:
                        break
                    parent_id = locaiton_id

            if parent_id:
                if type == 'source':
                    picking_ids = self.env['stock.picking'].search([('location_id', '=', parent_id.id)])
                    return picking_ids.ids
                else:
                    picking_ids = self.env['stock.picking'].search([('location_dest_id', '=', parent_id.id)])
                    return picking_ids.ids
            else:
                return []


class stock_picking_log(models.Model):
    _name = 'stock.picking.log'

    status_changed = fields.Char(string='Status Changed')
    time_log = fields.Datetime(string='Time')
    picking_id = fields.Many2one('stock.picking')
    status_changed_sub_for_po = fields.Char(string='Status Changed', compute='get_status_changed_sub')

    @api.multi
    def get_status_changed_sub(self):
        for rec in self:
            first_string = ""
            if rec.picking_id.is_internal_transfer:
                first_string = 'Internal Transfer : '
            elif rec.picking_id.picking_type_id.code == 'incoming':
                if rec.picking_id.is_picking_return:
                    first_string = 'Reversed Receipt : '
                else:
                    first_string = 'Receipt : '
            rec.status_changed_sub_for_po = first_string + rec.status_changed


class purchase_order_ihr(models.Model):
    _inherit = 'purchase.order'

    stock_picking_log_ids = fields.Many2many('stock.picking.log', compute='get_stock_picking_log_ids')

    @api.multi
    def get_stock_picking_log_ids(self):
        for rec in self:
            if rec.picking_ids:
                log_list = rec.picking_ids.mapped('stock_picking_log_ids')
                rec.stock_picking_log_ids = log_list
