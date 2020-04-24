# -*- coding: utf-8 -*-

from odoo import models, fields, api
import json
import base64
import StringIO
import xlsxwriter

class stock_picking_ihr(models.Model):
    _inherit = 'stock.picking'

    print_user_history = fields.Many2one('res.users', string='Nhân viên chuẩn bị tên số', compute='_get_print_history')
    in_tang_cuong_history = fields.Selection([('no', 'No'), ('yes', 'Yes')], string='Chuẩn bị tên số tăng cường', compute='_get_print_history')

    image_user_history = fields.Many2one('res.users', string='Nhân viên chuẩn bị hình ảnh', compute='_get_print_history')
    in_hinh_tang_cuong_history = fields.Selection([('no', 'No'), ('yes', 'Yes')],string='Chuẩn bị hình ảnh tăng cường', compute='_get_print_history')

    kcs1_user_history = fields.Many2one('res.users', string='Nhân viên KCS1', compute='_get_print_history')
    kcs1_tang_cuong_history = fields.Selection([('no', 'No'), ('yes', 'Yes')], string='KCS1 tăng cường', compute='_get_print_history')

    # ep_user_history = fields.Many2one('res.users', string='Nhân viên ép tên số')
    # ep_tang_cuong_history = fields.Selection([('no', 'No'), ('yes', 'Yes')], string='Ép tên số tăng cường')

    kcs2_user_history = fields.Many2one('res.users', string='Nhân viên KCS2', compute='_get_print_history')
    kcs2_tang_cuong_history = fields.Selection([('no', 'No'), ('yes', 'Yes')], string='KCS2 tăng cường', compute='_get_print_history')

    @api.multi
    def _get_print_history(self):
        for rec in self:
            if rec.sale_id and rec.check_print:
                picking_produce_name = rec.sale_id.picking_ids.filtered(lambda p: p.check_produce_name)
                if picking_produce_name:
                    picking_produce_name = picking_produce_name[0]
                    rec.print_user_history = picking_produce_name.print_user
                    rec.in_tang_cuong_history = picking_produce_name.in_tang_cuong

                picking_image_state = rec.sale_id.picking_ids.filtered(lambda p: p.check_produce_image)
                if picking_image_state:
                    picking_image_state = picking_image_state[0]
                    rec.image_user_history = picking_image_state.image_user
                    rec.in_hinh_tang_cuong_history = picking_image_state.in_hinh_tang_cuong

                picking_kcs1_state = rec.sale_id.picking_ids.filtered(lambda p: p.check_kcs1)
                if picking_kcs1_state:
                    picking_kcs1_state = picking_kcs1_state[0]
                    rec.kcs1_user_history = picking_kcs1_state.kcs1_user
                    rec.kcs1_tang_cuong_history = picking_kcs1_state.kcs1_tang_cuong

                picking_kcs2_state = rec.sale_id.picking_ids.filtered(lambda p: p.check_kcs2)
                if picking_kcs2_state:
                    picking_kcs2_state = picking_kcs2_state[0]
                    rec.kcs2_user_history = picking_kcs2_state.kcs2_user
                    rec.kcs2_tang_cuong_history = picking_kcs2_state.kcs2_tang_cuong
            if rec.purchase_id and rec.check_print:
                picking_produce_name = rec.purchase_id.picking_ids.filtered(lambda p: p.check_produce_name)
                if picking_produce_name:
                    picking_produce_name = picking_produce_name[0]
                    rec.print_user_history = picking_produce_name.print_user
                    rec.in_tang_cuong_history = picking_produce_name.in_tang_cuong

                picking_image_state = rec.purchase_id.picking_ids.filtered(lambda p: p.check_produce_image)
                if picking_image_state:
                    picking_image_state = picking_image_state[0]
                    rec.image_user_history = picking_image_state.image_user
                    rec.in_hinh_tang_cuong_history = picking_image_state.in_hinh_tang_cuong

                picking_kcs1_state = rec.purchase_id.picking_ids.filtered(lambda p: p.check_kcs1)
                if picking_kcs1_state:
                    picking_kcs1_state = picking_kcs1_state[0]
                    rec.kcs1_user_history = picking_kcs1_state.kcs1_user
                    rec.kcs1_tang_cuong_history = picking_kcs1_state.kcs1_tang_cuong

                picking_kcs2_state = rec.purchase_id.picking_ids.filtered(lambda p: p.check_kcs2)
                if picking_kcs2_state:
                    picking_kcs2_state = picking_kcs2_state[0]
                    rec.kcs2_user_history = picking_kcs2_state.kcs2_user
                    rec.kcs2_tang_cuong_history = picking_kcs2_state.kcs2_tang_cuong

    @api.model
    def report_lich_su_in_excel(self, response):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        picking_ids = self.env['stock.picking'].search(domain)
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Lich su in')

        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'border': 1})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter', 'border': 1})

        worksheet.set_column('A:C', 20)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('G:G', 20)
        worksheet.set_column('I:I', 20)
        worksheet.set_column('K:K', 20)

        row = 0
        summary_header = ['Đơn hàng', 'Thời gian xác nhận', 'Nhân viên chuẩn bị tên số', 'Chuẩn bị tên số tăng cường', 'Nhân viên chuẩn bị hình ảnh', 'Chuẩn bị hình ảnh tăng cường',
                          'Nhân viên KCS1', 'KCS1 tăng cường', 'Nhân viên ép tên số', 'Ép tên số tăng cường', 'Nhân viên KCS2', 'KCS2 tăng cường']
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for picking_id in picking_ids:
            row += 1
            export_confirm_order_sub = ''
            if picking_id.export_confirm_order_sub:
                export_confirm_order_sub = self._get_datetime_utc(picking_id.export_confirm_order_sub)
            worksheet.write(row, 0, picking_id.origin, text_style)
            worksheet.write(row, 1, export_confirm_order_sub, text_style)
            worksheet.write(row, 2, picking_id.print_user_history.name or '', text_style)
            worksheet.write(row, 3, 'No' if picking_id.in_tang_cuong_history == 'no' else 'Yes', text_style)
            worksheet.write(row, 4, picking_id.image_user_history.name or '', text_style)
            worksheet.write(row, 5, 'No' if picking_id.in_hinh_tang_cuong_history == 'no' else 'Yes', text_style)
            worksheet.write(row, 6, picking_id.kcs1_user_history.name or '', text_style)
            worksheet.write(row, 7, 'No' if picking_id.kcs1_tang_cuong_history == 'no' else 'Yes', text_style)
            worksheet.write(row, 8, picking_id.ep_user.name or '', text_style)
            worksheet.write(row, 9, 'No' if picking_id.ep_tang_cuong == 'no' else 'Yes', text_style)
            worksheet.write(row, 10, picking_id.kcs2_user_history.name or '', text_style)
            worksheet.write(row, 11, 'No' if picking_id.kcs2_tang_cuong_history == 'no' else 'Yes', text_style)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()