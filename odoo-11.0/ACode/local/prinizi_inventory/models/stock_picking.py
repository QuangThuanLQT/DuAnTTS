# -*- coding: utf-8 -*-

from collections import namedtuple
from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError
from datetime import datetime, date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta
import base64
import StringIO
import xlsxwriter
from io import BytesIO
from PIL import Image
from PIL import ImageEnhance
from random import randrange


class stock_picking(models.Model):
    _inherit = 'stock.picking'

    def _domain_print_user(self):
        group_nv_nhap_hang = self.env.ref('tts_modifier_access_right.group_nv_nhap_hang').users
        group_soan_donggoi = self.env.ref('tts_modifier_access_right.group_soan_donggoi').users
        group_ql_kho = self.env.ref('tts_modifier_access_right.group_ql_kho').users
        group_nv_giao_hang = self.env.ref('tts_modifier_access_right.group_nv_giao_hang').users
        group_nv_kho = self.env.ref('prinizi_modifier_accessright.group_nv_kho').users
        return [
            ('id', 'in', group_nv_kho.ids + group_nv_nhap_hang.ids + group_soan_donggoi.ids + group_ql_kho.ids + group_nv_giao_hang.ids)]

    def _domain_image_user(self):
        group_nv_nhap_hang = self.env.ref('tts_modifier_access_right.group_nv_nhap_hang').users
        group_soan_donggoi = self.env.ref('tts_modifier_access_right.group_soan_donggoi').users
        group_ql_kho = self.env.ref('tts_modifier_access_right.group_ql_kho').users
        group_nv_giao_hang = self.env.ref('tts_modifier_access_right.group_nv_giao_hang').users
        group_nv_kho = self.env.ref('prinizi_modifier_accessright.group_nv_kho').users
        return [
            ('id', 'in', group_nv_kho.ids + group_nv_nhap_hang.ids + group_soan_donggoi.ids + group_ql_kho.ids + group_nv_giao_hang.ids)]

    def _get_domain_user(self):
        group_ql_kho = self.env.ref('tts_modifier_access_right.group_ql_kho').users
        group_soan_donggoi = self.env.ref('tts_modifier_access_right.group_soan_donggoi').users
        group_nv_nhap_hang = self.env.ref('tts_modifier_access_right.group_nv_nhap_hang').users
        group_nv_giao_hang = self.env.ref('tts_modifier_access_right.group_nv_giao_hang').users
        group_nv_kho = self.env.ref('prinizi_modifier_accessright.group_nv_kho').users
        return [('id', 'in', group_ql_kho.ids + group_soan_donggoi.ids + group_nv_nhap_hang.ids + group_nv_giao_hang.ids + group_nv_kho.ids)]

    # def _get_domain_user_delivery(self):
    #     group_ql_kho = self.env.ref('tts_modifier_access_right.group_ql_kho').users
    #     group_nv_giao_hang = self.env.ref('tts_modifier_access_right.group_nv_giao_hang').users
    #     group_nv_kho = self.env.ref('prinizi_modifier_accessright.group_nv_kho').users
    #     return [('id', 'in', group_ql_kho.ids + group_nv_giao_hang.ids + group_nv_kho.ids)]
    #
    def _get_domain_user_receiver(self):
        group_ql_kho = self.env.ref('tts_modifier_access_right.group_ql_kho').users
        group_nv_nhap_hang = self.env.ref('tts_modifier_access_right.group_nv_nhap_hang').users
        group_nv_kho = self.env.ref('prinizi_modifier_accessright.group_nv_kho').users
        return [('id', 'in', group_ql_kho.ids + group_nv_nhap_hang.ids + group_nv_kho.ids)]
    #
    # def _get_user_internal_sale(self):
    #     group_khach_hang = self.env.ref('tts_modifier_access_right.group_khach_hang').users
    #     return [('id', 'not in', group_khach_hang.ids)]

    user_pick_id = fields.Many2one(domain=_get_domain_user)
    user_pack_id = fields.Many2one(domain=_get_domain_user)
    user_delivery_id = fields.Many2one(domain=_get_domain_user)
    receiver = fields.Many2one(domain=_get_domain_user)
    user_checking_id = fields.Many2one(domain=_get_domain_user)

    print_user = fields.Many2one('res.users', string='Nhân viên chuẩn bị tên số', copy=False, domain=_get_domain_user)
    in_tang_cuong = fields.Selection([('no', 'No'), ('yes', 'Yes')], default='no', string='Chuẩn bị tên số tăng cường',
                                     track_visibility='onchange')
    image_user = fields.Many2one('res.users', string='Nhân viên chuẩn bị hình', copy=False, domain=_get_domain_user)
    in_hinh_tang_cuong = fields.Selection([('no', 'No'), ('yes', 'Yes')], default='no',
                                          string='Chuẩn bị hình tăng cường',
                                          track_visibility='onchange')
    kcs1_user = fields.Many2one('res.users', string='Nhân viên KCS1', copy=False, domain=_get_domain_user)
    kcs1_tang_cuong = fields.Selection([('no', 'No'), ('yes', 'Yes')], default='no', string='KCS 1 tăng cường',
                                       track_visibility='onchange')
    kcs2_user = fields.Many2one('res.users', string='Nhân viên KCS2', copy=False, domain=_get_domain_user)
    kcs2_tang_cuong = fields.Selection([('no', 'No'), ('yes', 'Yes')], default='no', string='KCS 2 tăng cường',
                                       track_visibility='onchange')
    ep_user = fields.Many2one('res.users', string='Nhân viên ép tên số', copy=False, domain=_get_domain_user)
    ep_tang_cuong = fields.Selection([('no', 'No'), ('yes', 'Yes')], default='no', string='Ép tên số tăng cường',
                                     track_visibility='onchange')
    thong_tin_its = fields.Many2many('thong.tin.its', compute="get_thong_tin_its")
    thong_tin_them_its_ids = fields.Many2many('thong.tin.them.its', compute="get_thong_tin_its")
    thong_tin_in_hinh_ids = fields.Many2many('thong.tin.in.hinh', compute="get_thong_tin_its")
    config_thong_tin_its_ids = fields.Many2many('config.thong.tin.its', compute="get_thong_tin_its")
    note_image = fields.Text(related='sale_id.note_image', )
    image_print = fields.Many2many('ir.attachment', string="Image", related='sale_id.image_print')
    user_internal_sale = fields.Many2one('res.users', string='Nhân Viên', domain=_get_domain_user)
    internal_sale_note = fields.Text(string='Ghi chú')

    @api.multi
    def get_picking_note(self):
        for rec in self:
            if rec.internal_sale_note:
                rec.picking_note = rec.internal_sale_note
            else:
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

    # @api.multi
    # def write(self, val):
    #     if self.env.user.has_group('prinizi_modifier_accessright.group_nv_kho'):
    #         for rec in self:
    #             if rec.state == 'done':
    #                 raise UserError('Bạn không có quyền thực hiện trên phiếu done.')
    #     res = super(stock_picking, self).write(val)
    #     return res

    @api.multi
    def get_thong_tin_its(self):
        for rec in self:
            if rec.sale_id:
                rec.thong_tin_its = self.env['thong.tin.its'].search([('sale_id', '=', self.sale_id.id)])
                rec.thong_tin_them_its_ids = self.env['thong.tin.them.its'].search([('sale_id', '=', self.sale_id.id)])
                rec.thong_tin_in_hinh_ids = self.env['thong.tin.in.hinh'].search([('sale_id', '=', self.sale_id.id)])
                rec.config_thong_tin_its_ids = self.env['config.thong.tin.its'].search(
                    [('sale_id', '=', self.sale_id.id)])

    # @api.model
    # def get_pick_report_data(self):
    #     pick_data = []
    #     for line in self.move_lines:
    #         if line.product_id.default_code in list(map(lambda x: x['product_code'], pick_data)):
    #             for line_data in pick_data:
    #                 if line.product_id.default_code == line_data.get('product_code', False):
    #                     line_data['product_uom_qty'] += int(line.product_uom_qty)
    #         else:
    #             variants = [line.product_id.name]
    #             # size = ''
    #             # mau = ''
    #             for attr in line.product_id.attribute_value_ids:
    #                 if attr.attribute_id.name in ('Size', 'size'):
    #                     variants.append(('Size ' + attr.name))
    #                     # size = attr.name
    #                 else:
    #                     variants.append((attr.name))
    #                     # mau = attr.name
    #
    #             product_name = ' - '.join(variants)
    #             # product_name = line.product_id.name
    #             data = {
    #                 'product_code': line.product_id.default_code,
    #                 'product_name': product_name,
    #                 # 'mau': mau,
    #                 # 'size': size,
    #                 'product_uom_qty': int(line.product_uom_qty),
    #                 'print_qty': int(line.print_qty),
    #                 'row_span_x': 1,
    #                 'row_span_y': 1,
    #             }
    #             if line.product_id.location_ids:
    #                 data.update({
    #                     'x': line.product_id.location_ids[0].posx,
    #                     'y': line.product_id.location_ids[0].posy,
    #                     'location_name': line.product_id.location_ids[0].name,
    #                     'location_display_name': line.product_id.location_ids[0].display_name
    #                 })
    #             else:
    #                 data.update({
    #                     'x': 0,
    #                     'y': 0,
    #                     'location_name': '',
    #                     'location_display_name': '',
    #                 })
    #             pick_data.append(data)
    #     pick_data = sorted(pick_data, key=lambda elem: "%02d %02d %s" % (elem['x'], elem['y'], elem['location_name']))
    #     for i in range(0, len(pick_data)):
    #         row_span_y = 1
    #         for j in range(i + 1, len(pick_data)):
    #             if pick_data[i].get('x', False) == pick_data[j].get('x', False):
    #                 if pick_data[i].get('y', False) and pick_data[i].get('y', False) == pick_data[j].get('y', False):
    #                     pick_data[j].update({
    #                         'y': -1
    #                     })
    #                     row_span_y += 1
    #                 else:
    #                     break
    #             else:
    #                 break
    #         if row_span_y != 1:
    #             pick_data[i].update({
    #                 'row_span_y': row_span_y
    #             })
    #
    #     for i in range(0, len(pick_data)):
    #         row_span_x = 1
    #         for j in range(i + 1, len(pick_data)):
    #             if pick_data[i].get('x', False) and pick_data[i].get('x', False) == pick_data[j].get('x', False):
    #                 pick_data[j].update({
    #                     'x': -1
    #                 })
    #                 row_span_x += 1
    #             else:
    #                 break
    #         if row_span_x != 1:
    #             pick_data[i].update({
    #                 'row_span_x': row_span_x
    #             })
    #
    #     return pick_data

    def _prepare_pack_ops(self, quants, forced_qties):
        result = super(stock_picking, self)._prepare_pack_ops(quants, forced_qties)
        for val in result:
            product_id = self.move_lines.filtered(lambda s: s.product_id.id == val.get('product_id'))
            val.update({
                'print_qty': sum(product_id.mapped('print_qty'))
            })
        return result

    @api.multi
    def do_new_transfer(self):
        res = super(stock_picking, self).do_new_transfer()
        for rec in self:
            if not rec.is_picking_return and rec.check_print:
                kcs2_id = rec.mapped('move_lines').mapped('move_dest_id').mapped('picking_id')
                if kcs2_id:
                    kcs2_id.action_assign()
                    kcs2_id.write({
                        'kcs2_state': 'ready',
                    })
            elif not rec.is_picking_return and rec.check_kcs1:
                print_id = rec.mapped('move_lines').mapped('move_dest_id').mapped('picking_id')
                if print_id:
                    print_id.action_assign()
                    print_id.write({
                        'print_state': 'ready_print',
                    })

            elif not rec.is_picking_return and rec.check_kcs2:
                pack_id = rec.mapped('move_lines').mapped('move_dest_id').mapped('picking_id')
                if pack_id:
                    pack_id.write({
                        'state_pack': 'waiting_pack',
                    })
            elif not rec.is_picking_return and rec.check_is_pick:
                kcs1_id = rec.mapped('move_lines').mapped('move_dest_id').mapped('picking_id')
                product_name = rec.sale_id.picking_ids.filtered(lambda r: r.check_produce_name == True)
                product_image = rec.sale_id.picking_ids.filtered(lambda r: r.check_produce_image == True)
                if product_name.state == 'done' and product_image.state == 'done':
                    if kcs1_id:
                        kcs1_id.action_assign()
                        kcs1_id.write({
                            'kcs1_state': 'ready',
                        })
        return res

    # Report

    def create_product_sheet(self, worksheet, workbook):
        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 30)
        worksheet.set_column('C:C', 10)
        worksheet.set_column('D:D', 10)
        worksheet.set_column('E:E', 10)
        worksheet.set_column('F:F', 10)
        worksheet.set_column('G:K', 10)

        header_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'center', 'valign': 'vcenter'})
        header_bold_color.set_text_wrap(1)
        body_bold_color = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'right', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')
        row = 0
        summary_header = ['STT', 'Sản phẩm', 'Size', 'Lưng trên', 'Lưng giữa', 'Lưng dưới', 'In hình']

        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]
        stt = 1
        for line in self.thong_tin_its:
            row += 1
            worksheet.write(row, 0, stt, body_bold_color)
            worksheet.write(row, 1, line.product_id.name, body_bold_color)
            worksheet.write(row, 2, line.size or '', body_bold_color)
            worksheet.write(row, 3, line.lung_tren or '', body_bold_color_number)
            worksheet.write(row, 4, line.lung_giua or '', body_bold_color)
            worksheet.write(row, 5, line.lung_duoi or '', body_bold_color_number)
            worksheet.write(row, 6, 'Có' if line.in_hinh else 'Không', body_bold_color_number)
            stt += 1

    def create_print_sheet(self, worksheet, workbook):
        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 40)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:D', 15)
        worksheet.set_column('E:E', 15)
        worksheet.set_column('F:F', 10)
        worksheet.set_column('G:G', 10)

        header_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'center', 'valign': 'vcenter'})
        header_bold_color.set_text_wrap(1)
        body_bold_color = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'right', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')
        row = 0
        summary_header = ['STT', 'Sản phẩm', 'Vị trí in hình', 'Chất liệu in hình', 'Kích thước in hình', 'Tên hình', 'Số lượng']

        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]
        stt = 1
        for line in self.thong_tin_in_hinh_ids:
            row += 1
            temp = self.thong_tin_its.filtered(lambda r: r.product_id == line.product_id and r.in_hinh == True)
            worksheet.write(row, 0, stt, body_bold_color)
            worksheet.write(row, 1, line.product_id.name or '', body_bold_color)
            worksheet.write(row, 2, line.vi_tri_in.name or '', body_bold_color)
            worksheet.write(row, 3, line.chat_lieu_in_hinh.name or '', body_bold_color)
            worksheet.write(row, 4, line.kich_thuot_in or '', body_bold_color)
            worksheet.write(row, 5, line.ten_hinh or '', body_bold_color)
            worksheet.write(row, 6, len(temp), body_bold_color_number)
            stt += 1

    def create_image_sheet(self, worksheet, workbook):
        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 50)


        header_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'center', 'valign': 'vcenter'})
        header_bold_color.set_text_wrap(1)
        body_bold_color = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'right', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')
        row = 0
        summary_header = ['STT', 'HinhAnh']

        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        row = 1
        stt = 1
        width_row = 200
        for line in self.image_print:
            worksheet.set_row(row, width_row)

            image_stream = StringIO.StringIO(line.datas.decode('base64'))
            image = Image.open(image_stream)
            height = image.size[1]
            rate = float(width_row) / float(height)
            path = line._full_path(line.store_fname)
            fh = open(path, "rb")
            data = fh.read()

            buf_image = BytesIO(base64.b64decode(line.datas))

            worksheet.write(row, 0, stt, body_bold_color)
            worksheet.insert_image(row, 1, path, {'x_scale': rate, 'y_scale': rate, 'x_offset': 10, 'y_offset': 10,})

            stt += 1
            row += 1


        return worksheet

    def export_print_data(self):
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('ThongTinSanPham')
        self.create_product_sheet(worksheet, workbook)

        sheet_phprint = workbook.add_worksheet('PhieuInHinh')
        self.create_print_sheet(sheet_phprint, workbook)

        sheet_image = workbook.add_worksheet('HinhAnh')
        self.create_image_sheet(sheet_image, workbook)

        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create({
            'name': '%s - Thong tin in hinh.xlsx' % (self.sale_id.name or self.origin),
            'datas_fname': '%s - Thong tin in hinh.xlsx' % (self.sale_id.name or self.origin),
            'datas': result
        })
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        return {
            'type': 'ir.actions.act_url',
            'url': str(download_url),
        }

    # ______________

    def create_datinttenso_sheet(self, worksheet, workbook):
        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 40)
        worksheet.set_column('C:C', 10)
        worksheet.set_column('D:D', 10)
        worksheet.set_column('E:E', 10)
        worksheet.set_column('F:F', 10)
        worksheet.set_column('G:K', 15)
        worksheet.set_column('L:L', 15)
        worksheet.set_column('M:M', 15)
        worksheet.set_column('N:N', 15)
        worksheet.set_column('O:O', 10)
        worksheet.set_column('P:P', 10)
        worksheet.set_column('Q:Q', 15)

        header_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'center', 'valign': 'vcenter'})
        header_bold_color.set_text_wrap(1)
        body_bold_color = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'right', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')
        row = 0
        summary_header = ['STT', 'Sản phẩm', 'Size', 'Lưng trên', 'Lưng giữa', 'Lưng dưới', 'Font chư/ Số',
                          'Chất liệu lưng áo', 'Màu in lưng áo', 'Chất liệu in quần', 'Màu in quần', 'In hình']

        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]
        stt = 1
        for line in self.thong_tin_its:
            row += 1
            temp = self.config_thong_tin_its_ids.filtered(lambda r: r.product_id == line.product_id)
            worksheet.write(row, 0, stt, body_bold_color)
            worksheet.write(row, 1, line.product_id.name or '', body_bold_color)
            worksheet.write(row, 2, line.size or '', body_bold_color)
            worksheet.write(row, 3, line.lung_tren or '', body_bold_color)
            worksheet.write(row, 4, line.lung_giua or '', body_bold_color)
            worksheet.write(row, 5, line.lung_duoi or '', body_bold_color)
            worksheet.write(row, 6, temp.font_chu_so.name or '', body_bold_color)
            worksheet.write(row, 7, temp.lung_ao_chat_lieu_its.name or '', body_bold_color)
            worksheet.write(row, 8, temp.lung_ao_mau_its.name or '', body_bold_color)
            worksheet.write(row, 9, temp.ong_quan_chat_lieu_its.name or '', body_bold_color)
            worksheet.write(row, 10, temp.ong_quan_mau_its.name or '' or '', body_bold_color)
            worksheet.write(row, 11, 'Có' if line.in_hinh else 'Không', body_bold_color)
            stt += 1

    def create_datinthemtenso_sheet(self, worksheet, workbook):
        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 30)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:D', 15)
        worksheet.set_column('E:E', 15)
        worksheet.set_column('F:F', 15)
        worksheet.set_column('G:K', 15)


        header_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'center', 'valign': 'vcenter'})
        header_bold_color.set_text_wrap(1)
        body_bold_color = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'right', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')
        row = 0
        summary_header = ['STT', 'Sản phẩm', 'Vị trí in', 'Kích thước in', 'Nội dung in', 'Chất liệu in tên số',
                          'Màu in tên số']

        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        stt = 1
        for line in self.thong_tin_them_its_ids:
            row += 1
            temp = self.config_thong_tin_its_ids.filtered(lambda r: r.product_id == line.product_id)

            nguc_phai = self.env.ref('prinizi_sale_product_print.mat_truoc_ao_nguc_phai')
            nguc_trai = self.env.ref('prinizi_sale_product_print.mat_truoc_ao_nguc_trai')
            bung = self.env.ref('prinizi_sale_product_print.mat_truoc_ao_bung')

            ong_tay_trai = self.env.ref('prinizi_sale_product_print.tay_ao_trai')
            ong_tay_phai = self.env.ref('prinizi_sale_product_print.tay_ao_phai')

            quan_trai = self.env.ref('prinizi_sale_product_print.ong_quan_trai')
            quan_phai = self.env.ref('prinizi_sale_product_print.ong_quan_phai')

            lung_tren = self.env.ref('prinizi_sale_product_print.lung_ao_tren')
            lung_giua = self.env.ref('prinizi_sale_product_print.lung_ao_giua')
            lung_duoi = self.env.ref('prinizi_sale_product_print.lung_ao_duoi')

            if line.vi_tri_in in [nguc_phai, nguc_trai, bung]:
                f = temp.mat_truoc_ao_chat_lieu_its
                g = temp.mat_truoc_ao_mau_its
            elif line.vi_tri_in in [ong_tay_trai, ong_tay_phai]:
                f = temp.tay_ao_chat_lieu_its
                g = temp.tay_ao_mau_its
            elif line.vi_tri_in in [quan_trai, quan_phai]:
                f = temp.ong_quan_chat_lieu_its
                g = temp.ong_quan_mau_its
            elif line.vi_tri_in in [lung_tren, lung_giua, lung_duoi]:
                f = temp.lung_ao_chat_lieu_its
                g = temp.lung_ao_mau_its

            worksheet.write(row, 0, stt, body_bold_color)
            worksheet.write(row, 1, line.product_id.name or '', body_bold_color)
            worksheet.write(row, 2, line.vi_tri_in.name or '', body_bold_color)
            worksheet.write(row, 3, line.kich_thuot_in or '', body_bold_color)
            worksheet.write(row, 4, line.noi_dung_in or '', body_bold_color)
            worksheet.write(row, 5, f.name or '', body_bold_color)
            worksheet.write(row, 6, g.name or '', body_bold_color)
            stt += 1

    def create_datinhinh_sheet(self, worksheet, workbook):
        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 30)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 15)
        worksheet.set_column('G:K', 15)

        header_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'center', 'valign': 'vcenter'})
        header_bold_color.set_text_wrap(1)
        body_bold_color = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'right', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')
        row = 0
        summary_header = ['STT', 'Sản phẩm', 'Vị trí in hình', 'Chất liệu in hình', 'Kích thước in hình', 'Tên hình',
                          'Số lượng']

        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        stt = 1
        for line in self.thong_tin_in_hinh_ids:
            row += 1
            temp = self.thong_tin_its.filtered(lambda r: r.product_id == line.product_id and r.in_hinh == True)

            worksheet.write(row, 0, stt, body_bold_color)
            worksheet.write(row, 1, line.product_id.name or '', body_bold_color)
            worksheet.write(row, 2, line.vi_tri_in.name or '', body_bold_color)
            worksheet.write(row, 3, line.chat_lieu_in_hinh.name or '', body_bold_color)
            worksheet.write(row, 4, line.kich_thuot_in or '', body_bold_color)
            worksheet.write(row, 5, line.ten_hinh or '', body_bold_color)
            worksheet.write(row, 6, len(temp), body_bold_color_number)

            stt += 1

    def export_thongtin_its_h(self):
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        worksheet = workbook.add_worksheet('ĐẶT IN TÊN SỐ')
        self.create_datinttenso_sheet(worksheet, workbook)

        sheet_datinthemtenso = workbook.add_worksheet('ĐẶT IN THÊM TÊN SỐ')
        self.create_datinthemtenso_sheet(sheet_datinthemtenso, workbook)

        sheet_datinhinh = workbook.add_worksheet('ĐẶT IN HÌNH')
        self.create_datinhinh_sheet(sheet_datinhinh, workbook)

        sheet_image = workbook.add_worksheet('HinhAnh')
        self.create_image_sheet(sheet_image, workbook)

        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create({
            'name': '%s - Thong tin in hinh.xlsx' % (self.sale_id.name or self.origin),
            'datas_fname': '%s - Thong tin in hinh.xlsx' % (self.sale_id.name or self.origin),
            'datas': result
        })
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        return {
            'type': 'ir.actions.act_url',
            'url': str(download_url),
        }

    def export_product_name(self):
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        worksheet = workbook.add_worksheet('ĐẶT IN TÊN SỐ')
        self.create_datinttenso_sheet(worksheet, workbook)

        sheet_datinthemtenso = workbook.add_worksheet('ĐẶT IN THÊM TÊN SỐ')
        self.create_datinthemtenso_sheet(sheet_datinthemtenso, workbook)

        sheet_image = workbook.add_worksheet('HinhAnh')
        self.create_image_sheet(sheet_image, workbook)

        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create({
            'name': '%s - Thong tin in hinh.xlsx' % (self.sale_id.name or self.origin),
            'datas_fname': '%s - Thong tin in hinh.xlsx' % (self.sale_id.name or self.origin),
            'datas': result
        })
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        return {
            'type': 'ir.actions.act_url',
            'url': str(download_url),
        }
