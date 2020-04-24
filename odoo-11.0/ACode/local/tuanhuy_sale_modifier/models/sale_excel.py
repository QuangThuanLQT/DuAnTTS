# -*- coding: utf-8 -*-
from odoo import models, fields, api
import base64
import StringIO
import xlsxwriter
from io import BytesIO
import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import sys
import os
reload(sys)
sys.setdefaultencoding('utf-8')

dir_path = os.path.dirname(os.path.realpath(__file__))

class sale_order(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def printout_sale_excel(self):
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        for record in self:
            sheet_name = record.name
            sheet = workbook.add_worksheet(sheet_name)
            record.write_data_to_sheet(workbook, sheet)
        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create({
            'name': 'BaoGiaExcel.xlsx',
            'datas_fname': 'BaoGiaExcel.xlsx',
            'datas': result
        })
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return {
            'type': 'ir.actions.act_url',
            'url': str(base_url) + str(download_url),
        }

    @api.model
    def write_data_to_sheet(self,workbook,sheet):
        header_fomat = workbook.add_format({
                'border': 1,
                'align' : 'center',
                'font_size': '12',
                'valign': 'vcenter',
                'bold'  : 'True'
            })
        text_header = workbook.add_format({
                'font': 'italic',
                'align' : 'left',
                'font_size': '12',

            })
        border_left = workbook.add_format({
                'align' : 'left',
                'font_size': '12',
                'border': 1,
            })
        border_center = workbook.add_format({
            'align': 'center',
            'font_size': '12',
            'border': 1,
        })
        border_center_bold = workbook.add_format({
            'align': 'center',
            'font_size': '12',
            'border': 1,
            'bold': 'True'
        })
        border_left_bold = workbook.add_format({
            'align': 'left',
            'font_size': '12',
            'border': 1,
            'bold': 'True'
        })
        border_left = workbook.add_format({
            'align': 'left',
            'font_size': '12',
            'border': 1,
        })
        red_bold = workbook.add_format({
            'font_size': '12',
            'font_color': '#FF0000',
        })
        bold_left = workbook.add_format({
            'align': 'left',
            'font_size': '12',
            'bold': 'True'
        })
        center_format = workbook.add_format({
            'align': 'center',
            'font_size': '12',
        })
        sheet.set_column('A:A', 7)
        sheet.set_column('B:B', 25)
        sheet.set_column('C:C', 27)
        sheet.set_column('D:D', 10)
        sheet.set_column('E:E', 12)
        sheet.set_column('F:F', 15)
        sheet.set_column('G:G', 15)
        sheet.set_column('H:H', 15)

        filename = 'header_image.png'

        image_file = open('%s/%s' %(dir_path, filename), 'rb')
        image_data = BytesIO(image_file.read())
        image_file.close()
        # sheet.set_default_row(20)
        sheet.set_row(4,45)
        sheet.set_row(6,30)
        sheet.insert_image('A1', filename, {'image_data': image_data,'x_scale' : 0.95})
        i = 6
        sheet.merge_range('A7:H7', 'BÁO GIÁ', header_fomat)
        sheet.set_row(i, 20)

        sheet.merge_range('A8:C8', 'To: %s'%(self.partner_id.name or ''),border_left)
        sheet.write(i + 1, 3, "Date:" )
        sheet.merge_range('E8:H8', "%s"%(self.date_order and datetime.datetime.strptime(self.date_order,DEFAULT_SERVER_DATETIME_FORMAT).strftime('%d/%m/%Y') or ''),border_left_bold)

        sheet.merge_range('A9:C9', "Attn.:",border_left)
        sheet.write(i + 2, 3, "From:")
        sheet.merge_range('E9:H9', "%s %s"%(self.user_id.partner_id.title.name or '',self.user_id.partner_id.name or ''),border_left_bold)

        sheet.merge_range('A10:C10', "Tel: %s"%(self.partner_id.phone or ''),border_left)
        sheet.write(i + 3, 3, "Mobile:")
        sheet.merge_range('E10:H10', "%s"%(self.user_id.partner_id.mobile or ''),border_left)

        sheet.merge_range('A11:C11', "Fax: %s"%(self.partner_id.fax or ''),border_left)
        sheet.write(i + 4, 3, "Email:")
        sheet.merge_range('E11:H11', "%s"%(self.user_id.partner_id.email or ''),border_left)

        sheet.merge_range('A12:C12', "Email: %s"%(self.partner_id.email or ''),border_left)

        sheet.merge_range('A13:H13', 'Subject: Cung cấp vật tư, thiết bị điện.',border_left)

        sheet.merge_range('A14:H14', 'Công Ty Tuấn Huy chân thành cảm ơn sự quan tâm của quý khách hàng đến sản phẩm của Công Ty chúng tôi !',text_header)
        sheet.merge_range('A15:H15', 'Chúng tôi xin trân trọng gửi đến quý khách hàng bảng giá chi tiết thiết bị như sau:',text_header)

        sheet.merge_range('A16:A17', "STT \n(Number)",header_fomat)
        sheet.merge_range('B16:B17', 'TÊN SẢN PHẨM \n(Product name )',header_fomat)
        sheet.merge_range('C16:C17', 'Mã Hàng \n(Commodity code)',header_fomat)
        sheet.merge_range('D16:D17', 'ĐVT \n(Unit)',header_fomat)
        sheet.merge_range('E16:E17', 'Số Lượng \n(Quantity)',header_fomat)
        sheet.merge_range('F16:F17', 'Đơn Giá \n(Price)',header_fomat)
        sheet.merge_range('G16:G17', 'Thành Tiền \n(Total)',header_fomat)
        sheet.merge_range('H16:H17', 'Xuất Xứ \n(Origin)',header_fomat)

        j = 17
        count = 1
        total = 0
        for line in self.order_line:
            sheet.write(j ,0, count,border_center_bold)
            sheet.write(j ,1, line.product_id.name or '',border_left)
            sheet.write(j ,2, line.product_id.code or '',border_center)
            sheet.write(j ,3, line.product_uom.name or '',border_center)
            sheet.write(j ,4, '{:,}'.format(int(line.product_uom_qty)),border_center)
            sheet.write(j ,5, '{:,}'.format(int(line.last_price_unit)),border_center)
            sheet.write(j ,6, '{:,}'.format(int(line.price_subtotal)),border_center)
            sheet.write(j ,7, line.product_id.brand_name_select.name or '',border_center)
            j +=1
            count +=1
            total += line.price_subtotal
        sheet.merge_range('A%s:F%s'%(j+1,j+1), "Tổng",header_fomat)
        sheet.write(j, 6, '{:,}'.format(int(total)),header_fomat)
        sheet.write(j, 7, '', border_center)

        sheet.merge_range('A%s:F%s' % (j + 2, j + 2), "VAT 10%", header_fomat)
        sheet.write(j+1, 6, '', border_center)
        sheet.write(j+1, 7, '', border_center)

        sheet.merge_range('A%s:F%s' % (j + 3, j + 3), "Tổng cộng", header_fomat)
        sheet.write(j + 2, 6, '{:,}'.format(int(total)), header_fomat)
        sheet.write(j + 2, 7, '', border_center)

        sheet.write(j + 4, 0, '1/Hiệu lực báo giá : đơn giá trên có giá trị  trong vòng 15 ngày', red_bold)
        sheet.write(j + 5, 0, '2/Phương thức thanh toán : chuyển khoản.', red_bold)
        sheet.write(j + 6, 0, '* Điều kiện thanh toán: Ứng 30% giá trị đơn hàng ')
        sheet.write(j + 7, 0, '* Thanh toán 70% giá trị còn lại trước khi nhận thông báo giao hàng và xuất Hoá đơn.')
        sheet.write(j + 8, 0, '3/Phương thức giao hàng :', red_bold)
        sheet.write(j + 9, 0, '* Thời gian giao hàng :  trong vòng 7  ngày kể từ ngày bên bán nhận được tiền tạm ứng .')
        sheet.write(j + 10, 0, ' * Địa điểm giao hàng: Tại chân công trình trong phạm vi TP Đà Nẵng, trên phương tiện bên Bán')
        sheet.write(j + 11, 0, ' * Chất lượng sản phẩm : hàng mới 100%,bảo hành 12 tháng .')
        sheet.write(j + 12, 0, '* Thông tin chuyển khoản :')
        sheet.write(j + 13, 1, ' + Người thụ hưởng:Công ty TNHH điện Tuấn Huy')
        sheet.write(j + 14, 1, ' + Số tài khoản :- 0061019700079. Tại ngân hàng ABBank- CN Đà Nẵng')
        sheet.write(j + 15, 0, 'Rất mong nhận được sự quan tâm của Quý Công Ty.')
        data = self.date_order and datetime.datetime.strptime(self.date_order,DEFAULT_SERVER_DATETIME_FORMAT) or datetime.now()
        sheet.write(j + 15, 5, 'Đà Nẵng, ngày %s tháng %s năm %s'%(data.strftime('%d'),data.strftime('%m'),data.strftime('%Y')))

        sheet.write(j + 17, 0, 'Xác nhận đặt hàng của Quý Công Ty', bold_left)
        sheet.write(j + 17, 5, 'ĐẠI DIỆN CÔNG TY TUẤN HUY', bold_left)
        sheet.merge_range('F%s:G%s'%(j + 19,j + 19), 'Phòng kinh doanh', center_format)
        sheet.merge_range('F%s:G%s'%(j + 20,j + 20), '%s'%(self.user_id.partner_id.name or ''), center_format)
        sheet.merge_range('F%s:G%s'%(j + 21,j + 21), '%s'%(self.user_id.partner_id.phone or ''), center_format)


