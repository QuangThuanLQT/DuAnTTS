# -*- coding: utf-8 -*-

from odoo import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT,DEFAULT_SERVER_DATE_FORMAT
import cStringIO
import base64
import StringIO
import xlsxwriter
from datetime import datetime

class stock_picking_line_report(models.TransientModel):
    _name = 'stock.picking.line.report'

    partner_id = fields.Many2one('res.partner', String="Customer")
    start_date = fields.Date(String='Start Date', required=True)
    end_date = fields.Date(String='End Date')

    def get_picking_out_data(self):
        picking_type_out = self.env.ref('stock.picking_type_out')
        conditions = [('state','=','done'),('picking_type_id','=',picking_type_out.id)]
        if self.start_date:
            conditions.append(('min_date', '>=', self.start_date))
        if self.end_date:
            conditions.append(('min_date', '<=', self.end_date))
        if self.partner_id:
            conditions.append(('partner_id', '=', self.partner_id.id))

        picking_ids = self.env['stock.picking'].search(conditions)
        data = []
        for picking_id in picking_ids:
            for line in picking_id.move_lines:
                so_id = picking_id.sale_select_id or picking_id.sale_id
                price = 0
                if so_id:
                    so_line = so_id.order_line.filtered(lambda l: l.product_id == line.product_id)
                    if so_line:
                        price = so_line[0].last_price_unit
                data.append({
                    'date_base_order' : picking_id.date_base_order,
                    'min_date': picking_id.min_date and picking_id.min_date.split(' ')[0] or '',
                    'sale_order': picking_id.sale_select_id and picking_id.sale_select_id.name or picking_id.sale_id and picking_id.sale_id.name or '',
                    'picking_name': picking_id.name,
                    'note': picking_id.sale_select_id and picking_id.sale_select_id.note or picking_id.sale_id and picking_id.sale_id.note or '',
                    'partner_ref': picking_id.partner_id.ref or '',
                    'partner_name': picking_id.partner_id.name or '',
                    'product_code' : line.product_id.default_code or '',
                    'product_name': line.product_id.name or '',
                    'product_uom': line.product_uom.name or '',
                    'product_uom_qty': line.product_uom_qty or 0,
                    'price': price,
                    'sum' : line.product_uom_qty * price,
                })
        return data

    @api.multi
    def print_report_excel(self):
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('So Chi Tiet Ban Hang')
        bold = workbook.add_format({'bold': True})
        merge_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': '20'})
        header_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter', 'bg_color' : '#ACC7E7'})
        body_bold_color = workbook.add_format(
            {'bold': False, 'font_size': '14', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '14', 'align': 'left', 'valign': 'vcenter','num_format': '#,##0',})
        string_header = "SỔ CHI TIẾT BÁN HÀNG"
        worksheet.merge_range('A1:M1', unicode(string_header, "utf-8"), merge_format)
        start_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT)
        end_date = datetime.strptime(self.end_date, DEFAULT_SERVER_DATE_FORMAT)
        string = "Khách hàng: %s; Từ ngày %s đến ngày %s" % (self.partner_id.name or '', start_date.date() or '', end_date.date() or '')
        worksheet.merge_range('A2:M2', unicode(str(string), "utf-8"), merge_format)

        row = 2
        summary_header = ['Ngày đặt hàng', 'Ngày giao hàng', 'Số đơn hàng', 'Mã dịch chuyển', 'Diễn giải chung', 'Mã khách hàng', 'Tên khách hàng'
            ,'Mã Hàng', 'Tên hàng', 'ĐVT', 'Tổng số lượng bán', 'Đơn giá', 'Doanh số bán']
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        worksheet.set_row(2, 25)

        worksheet.set_column('A:C', 15)
        worksheet.set_column('D:D', 25)
        worksheet.set_column('E:E', 50)
        worksheet.set_column('F:F', 15)
        worksheet.set_column('G:G', 60)
        worksheet.set_column('H:H', 25)
        worksheet.set_column('I:I', 40)
        worksheet.set_column('J:J', 10)
        worksheet.set_column('K:M', 25)

        data = self.get_picking_out_data()
        for line in data:
            row += 1
            worksheet.write(row, 0, line.get('date_base_order'), body_bold_color)
            worksheet.write(row, 1, line.get('min_date'), body_bold_color)
            worksheet.write(row, 2, line.get('sale_order'), body_bold_color)
            worksheet.write(row, 3, line.get('picking_name'), body_bold_color)
            worksheet.write(row, 4, line.get('note'), body_bold_color)
            worksheet.write(row, 5, line.get('partner_ref'), body_bold_color)
            worksheet.write(row, 6, line.get('partner_name'), body_bold_color)
            worksheet.write(row, 7, line.get('product_code'), body_bold_color)
            worksheet.write(row, 8, line.get('product_name'), body_bold_color)
            worksheet.write(row, 9, line.get('product_uom'), body_bold_color)
            worksheet.write(row, 10, line.get('product_uom_qty'), body_bold_color_number)
            worksheet.write(row, 11, line.get('price'), body_bold_color_number)
            worksheet.write(row, 12, line.get('sum'), body_bold_color_number)

        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create(
            {'name': 'SoChiTietBanHang.xlsx', 'datas_fname': 'SoChiTietBanHang.xlsx', 'datas': result})
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return {"type": "ir.actions.act_url",
                "url": str(base_url) + str(download_url)}