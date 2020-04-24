# -*- coding: utf-8 -*-
import base64
import os
from odoo import models, fields, api
import StringIO
import xlsxwriter
from datetime import datetime

class tuanhuy_print_excel_quotation(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def print_excel_quotation(self):
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        worksheet = workbook.add_worksheet('Bao Gia Ban')
        logo = os.path.abspath(__file__).split('models')[0] + 'static/pic/hearder.jpg'
        footer = os.path.abspath(__file__).split('models')[0] + 'static/pic/Footer.jpg'
        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')
        body_format = workbook.add_format({
            'font_size': '25',
            'align': 'center',
            'valign': 'vcenter',

        })
        format_tab = workbook.add_format({
            'font_size': '12',
            'bottom': 1,
            'right' : 1,
            'left' : 1,
        })
        format_1 = workbook.add_format({
            'font_size': '12',
            'border': 1,
            'bottom': 4,
        })
        format_2 = workbook.add_format({
            'font_size': '12',
            'bottom': 4,
            'right' : 1,
        })
        format_3 = workbook.add_format({
            'font_size': '12',
            'bottom': 1,
            'right' : 1,
        })
        body_format_text_wrap_mr_top = workbook.add_format({
            'font_size': '11',
            'align': 'center',
            'valign': 'top',
            'text_wrap': True,
            'bg_color' : '#B7CF30',
            'border' : 1,
            'bold' : True,
        })
        format_footer = workbook.add_format({
            'bg_color' : 'yellow',
            'align': 'center',
            'border': 1,
            'bold': True,
            'num_format': '##,#0₫',
        })
        table = workbook.add_format({
            'font_size': '10',
            'border': 1,
            'align': 'center',
        })
        table_d = workbook.add_format({
            'font_size': '10',
            'border': 1,
            'num_format': '##,#0₫',
            'align': 'center',
        })
        label = workbook.add_format({
            'italic': True,
        })
        label_footer = workbook.add_format({
            'font_color': '#FE0000',
            'bold': True,
        })
        label_footer1 = workbook.add_format({
            'bold': True,
        })
        label_footer2 = workbook.add_format({
            'bold': True,
            'align': 'center',
            'font_size': '12',
        })
        # worksheet.set_column('A:N', 20)
        worksheet.insert_image('A1', logo, {'y_offset': 8, 'x_scale': 1.22, 'y_scale': 1.1})

        summary_header = ['']
        row = 0
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]



        worksheet.merge_range('A9:H9', unicode("Báo Giá", "utf-8"), body_format)
        worksheet.set_row(8, 35)
        worksheet.set_row(18, 20)
        worksheet.set_column('B:B', 42)
        worksheet.set_column('C:C', 19)
        worksheet.set_column('E:E', 11)
        worksheet.set_column('F:F', 13)
        worksheet.set_column('G:G', 14)
        worksheet.set_column('H:H', 12)

        worksheet.merge_range('A10:C10', unicode("To:", "utf-8"),format_1)
        worksheet.merge_range('A11:C11', unicode("Attn:", "utf-8"),format_2)
        worksheet.merge_range('A12:C12', unicode("Tel:", "utf-8"),format_2)
        worksheet.merge_range('A13:C13', unicode("Fax:", "utf-8"),format_2)
        worksheet.merge_range('A14:C14', unicode("Email:", "utf-8"),format_2)
        worksheet.merge_range('A15:C15', unicode("Subject:", "utf-8"),format_3)

        worksheet.merge_range('D10:H10', unicode("Date:", "utf-8"),format_1)
        worksheet.merge_range('D11:H11', unicode("From:", "utf-8"),format_2)
        worksheet.merge_range('D12:H12', unicode("Mobile:", "utf-8"),format_2)
        worksheet.merge_range('D13:H13', unicode("Email:", "utf-8"),format_2)
        worksheet.merge_range('D14:H14', unicode(""),format_2)
        worksheet.merge_range('D15:H15', unicode(""),format_3)

        worksheet.merge_range('A16:H16', unicode("Công Ty TNHH Thiết Bị Điện 3T chân thành cảm ơn sự quan tâm của quý khách hàng đến sản phẩm của Công Ty chúng tôi !", "utf-8"),label)
        worksheet.merge_range('A17:H17', unicode("Chúng tôi xin trân trọng gửi đến quý khách hàng bảng giá chi tiết thiết bị như sau:", "utf-8"),label)

        worksheet.merge_range('A18:A19', "")
        worksheet.write_rich_string('A18', unicode("STT", "utf-8"),body_format_text_wrap_mr_top,
                                    unicode("\n(Number)", "utf-8"),body_format_text_wrap_mr_top)
        worksheet.write_rich_string('A19', "", format_tab)
        worksheet.merge_range('B18:B19', "")
        worksheet.write_rich_string('B18', unicode("TÊN SẢN PHẨM", "utf-8"),body_format_text_wrap_mr_top,
                                    unicode("\n(Product name)", "utf-8"), body_format_text_wrap_mr_top)
        worksheet.write_rich_string('B19', "", format_tab)
        worksheet.merge_range('C18:C19', "")
        worksheet.write_rich_string('C18', unicode("Mã Hàng", "utf-8"),body_format_text_wrap_mr_top,
                                    unicode("\n(Commodity code)", "utf-8"), body_format_text_wrap_mr_top)
        worksheet.write_rich_string('C19', "", format_tab)
        worksheet.merge_range('D18:D19', "")
        worksheet.write_rich_string('D18', unicode("ĐVT", "utf-8"),body_format_text_wrap_mr_top,
                                    unicode("\n(Unit)", "utf-8"), body_format_text_wrap_mr_top)
        worksheet.write_rich_string('D19', "", format_tab)
        worksheet.merge_range('E18:E19', "")
        worksheet.write_rich_string('E18', unicode("Số Lượng", "utf-8"),body_format_text_wrap_mr_top,
                                    unicode("\n(Quantity)", "utf-8"), body_format_text_wrap_mr_top)
        worksheet.write_rich_string('E19', "", format_tab)
        worksheet.merge_range('F18:F19', "")
        worksheet.write_rich_string('F18', unicode("Đơn Giá", "utf-8"),body_format_text_wrap_mr_top,
                                    unicode("\n(Price)", "utf-8"), body_format_text_wrap_mr_top)
        worksheet.write_rich_string('F19', "", format_tab)
        worksheet.merge_range('G18:G19', "")
        worksheet.write_rich_string('G18', unicode("Thành Tiền", "utf-8"),body_format_text_wrap_mr_top,
                                    unicode("\n(Total)", "utf-8"), body_format_text_wrap_mr_top)
        worksheet.write_rich_string('G19', "", format_tab)
        worksheet.merge_range('H18:H19', "")
        worksheet.write_rich_string('H18', unicode("Xuất Xứ", "utf-8"),body_format_text_wrap_mr_top,
                                    unicode("\n(Origin)", "utf-8"), body_format_text_wrap_mr_top)
        worksheet.write_rich_string('H19', "", format_tab)

        row = 18
        r=0
        for line in self.order_line:
            row += 1
            r += 1
            worksheet.set_row(row, 20)

            worksheet.write(row, 0, r or '',table)
            worksheet.write(row, 1, line.name or '',table)
            worksheet.write(row, 2, line.product_default_code or '',table)
            worksheet.write(row, 3, line.product_uom.name or '',table)
            worksheet.write(row, 4, line.product_uom_qty or '',table)
            worksheet.write(row, 5, line.last_price_unit or '',table_d)
            worksheet.write(row, 6, line.price_subtotal or '',table_d)
            worksheet.write(row, 7, line.product_id.source_select.name or '', table)

        row += 1
        worksheet.write(row, 0, '', table)
        worksheet.write(row, 1, '', table)
        worksheet.write(row, 2, '', table)
        worksheet.write(row, 3, '', table)
        worksheet.write(row, 4, '', table)
        worksheet.write(row, 5, '', table)
        worksheet.write(row, 6, '', table)
        worksheet.write(row, 7, '', table)
        row += 1
        worksheet.write(row, 0, '', table)
        worksheet.write(row, 1, '', table)
        worksheet.write(row, 2, '', table)
        worksheet.write(row, 3, '', table)
        worksheet.write(row, 4, '', table)
        worksheet.write(row, 5, '', table)
        worksheet.write(row, 6, '', table)
        worksheet.write(row, 7, '', table)
        row += 1
        worksheet.merge_range(row,0,row,5, unicode("Tổng cộng", "utf-8"), format_footer)
        worksheet.write(row, 6, self.amount_untaxed  or '', format_footer)
        worksheet.write(row, 7, '', format_footer)
        row += 1
        worksheet.merge_range(row,0,row,5, unicode("VAT 10%", "utf-8"), format_footer)
        worksheet.write(row, 6, self.amount_tax , format_footer)
        worksheet.write(row, 7, '', format_footer)
        row += 1
        worksheet.merge_range(row,0,row,5, unicode("Tổng cộng bao gồm VAT 10%", "utf-8"), format_footer)
        worksheet.write(row, 6, self.amount_total or '', format_footer)
        worksheet.write(row, 7, '', format_footer)

        row += 2
        worksheet.write(row,0, unicode("1/Hiệu lực báo giá : đơn giá trên có giá trị  trong vòng 15 ngày", "utf-8"),label_footer)
        row += 1
        worksheet.write(row,0, unicode("2/Phương thức thanh toán : chuyển khoản.", "utf-8"),label_footer)
        row += 1
        worksheet.write(row,0, unicode("* Điều kiện thanh toán: Thanh toán  100 %  khi  giao hàng và xuất hóa đơn", "utf-8"))
        row += 1
        worksheet.write(row,0, unicode("3/Phương thức giao hàng :", "utf-8"),label_footer)
        row += 1
        worksheet.write(row,0, unicode(" * Thời gian giao hàng :  Trong vòng 2-3  ngày kể từ khi xác nhận .", "utf-8"))
        row += 1
        worksheet.write(row,0, unicode(" * Địa điểm giao hàng: Tại chân công trình trong phạm vi TP Đà Nẵng, trên phương tiện bên Bán", "utf-8"))
        row += 1
        worksheet.write(row,0, unicode(" * Chất lượng sản phẩm : hàng mới 100%,bảo hành 12 tháng .", "utf-8"))
        row += 1
        worksheet.write(row,0, unicode("* Thông tin chuyển khoản :", "utf-8"))
        row += 1
        worksheet.write(row,1, unicode(" + Người thụ hưởng:Công ty TNHH Thiết Bị Điện 3T", "utf-8"))
        row += 1
        worksheet.write(row, 1, unicode(" + Số tài khoản :- 0061019700079. Tại ngân hàng ABBank- CN Đà Nẵng", "utf-8"))
        row += 1
        worksheet.write(row, 0, unicode("Rất mong nhận được sự quan tâm của Quý Công Ty.", "utf-8"))
        worksheet.write(row, 5, unicode("Đà Nẵng, ngày  17  tháng   04  năm 2019", "utf-8"))
        row += 1
        worksheet.write(row, 0, unicode("Xác nhận đặt hàng của Quý Công Ty", "utf-8"),label_footer1)
        worksheet.merge_range(row, 4,row, 7, unicode("ĐẠI DIỆN CÔNG TY TNHH THIẾT BỊ ĐIỆN 3T", "utf-8"),label_footer2)
        row += 1
        worksheet.insert_image(row, 4, footer, {'y_offset': 8, 'x_scale': 1.1, 'y_scale': 1.2})

        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create(
            {'name': 'BGB.xlsx', 'datas_fname': 'BGB.xlsx', 'datas': result})
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return {"type": "ir.actions.act_url",
                "url": str(base_url) + str(download_url)}