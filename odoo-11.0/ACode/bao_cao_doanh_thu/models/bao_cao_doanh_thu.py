# -*- coding: utf-8 -*-

from odoo import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
# import cStringIO
import base64
from io import StringIO
import xlsxwriter
from datetime import datetime


class sale_order_line_report(models.TransientModel):
    _name = 'bao.cao.doanh.thu'

    start_date = fields.Date(String='Start Date', required=True)
    end_date = fields.Date(String='End Date')

    def get_data_report(self):
        data_report = {}
        data_doanh_thu_chi_tiet = []
        kh_gian_tiep = []
        kh_truc_tiep = []
        hang_ls = []
        hang_th = []
        hang_sp = []
        hang_ms = []
        hang_sh = []
        hang_day_dien = []
        tong_hop = []

        doanh_thu_sum_1 = 0.0
        schneider_sum_1 = 0.0
        ls_sum_1 = 0.0
        th_sum_1 = 0.0
        sp_sum_1 = 0.0
        day_dien_1 = 0.0
        mitsubishi_1 = 0.0
        sp_khac_1 = 0.0

        doanh_thu_sum_2 = 0.0
        schneider_sum_2 = 0.0
        ls_sum_2 = 0.0
        th_sum_2 = 0.0
        sp_sum_2 = 0.0
        day_dien_2 = 0.0
        mitsubishi_2 = 0.0
        sp_khac_2 = 0.0

        doanh_thu_sum_3 = 0.0
        schneider_sum_3 = 0.0
        ls_sum_3 = 0.0
        th_sum_3 = 0.0
        sp_sum_3 = 0.0
        day_dien_3 = 0.0
        mitsubishi_3 = 0.0
        sp_khac_3 = 0.0

        doanh_thu_sum_4 = 0.0
        schneider_sum_4 = 0.0
        ls_sum_4 = 0.0
        th_sum_4 = 0.0
        sp_sum_4 = 0.0
        day_dien_4 = 0.0
        mitsubishi_4 = 0.0
        sp_khac_4 = 0.0

        doanh_thu_sum_5 = 0.0
        schneider_sum_5 = 0.0
        ls_sum_5 = 0.0
        th_sum_5 = 0.0
        sp_sum_5 = 0.0
        day_dien_5 = 0.0
        mitsubishi_5 = 0.0
        sp_khac_5 = 0.0

        doanh_thu_tyle_2 = 0.0
        schneider_tyle_2 = 0.0
        ls_tyle_2 = 0.0
        day_tyle_2 = 0.0
        mitsubishi_tyle_2 = 0.0
        sp_khac_tyle_2 = 0.0

        doanh_thu_tyle_3 = 0.0
        schneider_tyle_3 = 0.0
        ls_tyle_3 = 0.0
        day_tyle_3 = 0.0
        mitsubishi_tyle_3 = 0.0
        sp_khac_tyle_3 = 0.0

        conditions = [('order_id.state', 'in', ['sale', 'done'])]
        if self.start_date:
            conditions.append(('date_order', '>=', self.start_date))
        if self.end_date:
            conditions.append(('date_order', '<=', self.end_date))

        order_line_ids = self.env['sale.order.line'].search(conditions, order='date_order asc')

        for order_line in order_line_ids:
            doanh_thu_sum_1 += order_line.price_subtotal
            if order_line.order_partner_id.group_kh2_id.name == 'TUẤN HUY':
                doanh_thu_sum_2 += order_line.price_subtotal
            elif order_line.order_partner_id.group_kh2_id.name == 'CTY':
                doanh_thu_sum_3 += order_line.price_subtotal
            elif order_line.order_partner_id.group_kh2_id.name == 'KHÁCH LẺ':
                doanh_thu_sum_4 += order_line.price_subtotal
            elif order_line.order_partner_id.group_kh2_id.name == 'CỬA HÀNG':
                doanh_thu_sum_5 += order_line.price_subtotal

            data_doanh_thu_chi_tiet.append({
                'date_order': datetime.strptime(order_line.date_order, DEFAULT_SERVER_DATETIME_FORMAT).strftime(
                    "%d/%m/%Y"),
                'order_name': order_line.order_id.name,
                'partner_name': order_line.order_partner_id.name,
                'default_code': order_line.product_id.default_code,
                'product_name': order_line.product_id.name,
                'uom': order_line.product_uom.name,
                'qty': order_line.product_uom_qty,
                'price_unit': order_line.final_price,
                'price_subtotal': order_line.price_subtotal,
            })

            if order_line.order_partner_id.group_kh1_id.name == 'TT':
                doanh_thu_tyle_3 += order_line.price_subtotal
                kh_truc_tiep.append({
                    'date_order': datetime.strptime(order_line.date_order, DEFAULT_SERVER_DATETIME_FORMAT).strftime(
                        "%d/%m/%Y"),
                    'order_name': order_line.order_id.name,
                    'partner_name': order_line.order_partner_id.name,
                    'default_code': order_line.product_id.default_code,
                    'product_name': order_line.product_id.name,
                    'uom': order_line.product_uom.name,
                    'qty': order_line.product_uom_qty,
                    'price_unit': order_line.final_price,
                    'price_subtotal': order_line.price_subtotal,
                })
            else:
                doanh_thu_tyle_2 += order_line.price_subtotal if not order_line.sale_order_return else -order_line.price_subtotal
                kh_gian_tiep.append({
                    'date_order': datetime.strptime(order_line.date_order, DEFAULT_SERVER_DATETIME_FORMAT).strftime(
                        "%d/%m/%Y"),
                    'order_name': order_line.order_id.name,
                    'partner_name': order_line.order_partner_id.name,
                    'default_code': order_line.product_id.default_code,
                    'product_name': order_line.product_id.name,
                    'uom': order_line.product_uom.name,
                    'qty': order_line.product_uom_qty,
                    'price_unit': order_line.final_price,
                    'price_subtotal': order_line.price_subtotal,
                })
            if order_line.product_id.default_code and order_line.product_id.default_code[0:3] == 'LS-':
                ls_sum_1 += order_line.price_subtotal
                if order_line.order_partner_id.group_kh2_id.name == 'TUẤN HUY':
                    ls_sum_2 += order_line.price_subtotal
                elif order_line.order_partner_id.group_kh2_id.name == 'CTY':
                    ls_sum_3 += order_line.price_subtotal
                elif order_line.order_partner_id.group_kh2_id.name == 'KHÁCH LẺ':
                    ls_sum_4 += order_line.price_subtotal
                elif order_line.order_partner_id.group_kh2_id.name == 'CỬA HÀNG':
                    ls_sum_5 += order_line.price_subtotal
                hang_ls.append({
                    'date_order': datetime.strptime(order_line.date_order, DEFAULT_SERVER_DATETIME_FORMAT).strftime(
                        "%d/%m/%Y"),
                    'order_name': order_line.order_id.name,
                    # 'partner_name': order_line.order_partner_id.name,
                    'default_code': order_line.product_id.default_code,
                    'product_name': order_line.product_id.name,
                    'uom': order_line.product_uom.name,
                    'qty': order_line.product_uom_qty,
                    'price_unit': order_line.final_price,
                    'price_subtotal': order_line.price_subtotal,
                    'discount': order_line.discount,
                })
            if order_line.product_id.default_code and order_line.product_id.default_code[0:3] == 'TH-':
                th_sum_1 += order_line.price_subtotal
                if order_line.order_partner_id.group_kh2_id.name == 'TUẤN HUY':
                    th_sum_2 += order_line.price_subtotal
                elif order_line.order_partner_id.group_kh2_id.name == 'CTY':
                    th_sum_3 += order_line.price_subtotal
                elif order_line.order_partner_id.group_kh2_id.name == 'KHÁCH LẺ':
                    th_sum_4 += order_line.price_subtotal
                elif order_line.order_partner_id.group_kh2_id.name == 'CỬA HÀNG':
                    th_sum_5 += order_line.price_subtotal
                hang_th.append({
                    'date_order': datetime.strptime(order_line.date_order, DEFAULT_SERVER_DATETIME_FORMAT).strftime(
                        "%d/%m/%Y"),
                    'order_name': order_line.order_id.name,
                    # 'partner_name': order_line.order_partner_id.name,
                    'default_code': order_line.product_id.default_code,
                    'product_name': order_line.product_id.name,
                    'uom': order_line.product_uom.name,
                    'qty': order_line.product_uom_qty,
                    'price_unit': order_line.final_price,
                    'price_subtotal': order_line.price_subtotal,
                    'discount': order_line.discount,
                })
            if order_line.product_id.default_code and order_line.product_id.default_code[0:3] == 'SP-':
                sp_sum_1 += order_line.price_subtotal
                if order_line.order_partner_id.group_kh2_id.name == 'TUẤN HUY':
                    sp_sum_2 += order_line.price_subtotal
                elif order_line.order_partner_id.group_kh2_id.name == 'CTY':
                    sp_sum_3 += order_line.price_subtotal
                elif order_line.order_partner_id.group_kh2_id.name == 'KHÁCH LẺ':
                    sp_sum_4 += order_line.price_subtotal
                elif order_line.order_partner_id.group_kh2_id.name == 'CỬA HÀNG':
                    sp_sum_5 += order_line.price_subtotal
                hang_sp.append({
                    'date_order': datetime.strptime(order_line.date_order, DEFAULT_SERVER_DATETIME_FORMAT).strftime(
                        "%d/%m/%Y"),
                    'order_name': order_line.order_id.name,
                    # 'partner_name': order_line.order_partner_id.name,
                    'default_code': order_line.product_id.default_code,
                    'product_name': order_line.product_id.name,
                    'uom': order_line.product_uom.name,
                    'qty': order_line.product_uom_qty,
                    'price_unit': order_line.final_price,
                    'price_subtotal': order_line.price_subtotal,
                    'discount': order_line.discount,
                })
            if order_line.product_id.default_code and (
                    order_line.product_id.default_code[0:3] in ['CV-', 'TS-'] or order_line.product_id.default_code[
                                                                                 0:4] in ['CDV-',
                                                                                          'CDS-'] or 'LIONDAP-' in order_line.product_id.default_code):
                day_dien_1 += order_line.price_subtotal
                if order_line.order_partner_id.group_kh2_id.name == 'TUẤN HUY':
                    day_dien_2 += order_line.price_subtotal
                elif order_line.order_partner_id.group_kh2_id.name == 'CTY':
                    day_dien_3 += order_line.price_subtotal
                elif order_line.order_partner_id.group_kh2_id.name == 'KHÁCH LẺ':
                    day_dien_4 += order_line.price_subtotal if not order_line.sale_order_return else -order_line.price_subtotal
                elif order_line.order_partner_id.group_kh2_id.name == 'CỬA HÀNG':
                    day_dien_5 += order_line.price_subtotal if not order_line.sale_order_return else -order_line.price_subtotal
                hang_day_dien.append({
                    'date_order': datetime.strptime(order_line.date_order, DEFAULT_SERVER_DATETIME_FORMAT).strftime(
                        "%d/%m/%Y"),
                    'order_name': order_line.order_id.name,
                    # 'partner_name': order_line.order_partner_id.name,
                    'default_code': order_line.product_id.default_code,
                    'product_name': order_line.product_id.name,
                    'uom': order_line.product_uom.name,
                    'qty': order_line.product_uom_qty if not order_line.sale_order_return else -order_line.product_uom_qty,
                    'price_unit': order_line.final_price if not order_line.sale_order_return else -order_line.final_price,
                    'price_subtotal': order_line.price_subtotal if not order_line.sale_order_return else -order_line.price_subtotal,
                    'discount': order_line.discount,
                })
            if 'MS-' in order_line.product_id.default_code:
                mitsubishi_1 += order_line.price_subtotal if not order_line.sale_order_return else -order_line.price_subtotal
                if order_line.order_partner_id.group_kh2_id.name == 'TUẤN HUY':
                    mitsubishi_2 += order_line.price_subtotal if not order_line.sale_order_return else -order_line.price_subtotal
                elif order_line.order_partner_id.group_kh2_id.name == 'CTY':
                    mitsubishi_3 += order_line.price_subtotal if not order_line.sale_order_return else -order_line.price_subtotal
                elif order_line.order_partner_id.group_kh2_id.name == 'KHÁCH LẺ':
                    mitsubishi_4 += order_line.price_subtotal if not order_line.sale_order_return else -order_line.price_subtotal
                elif order_line.order_partner_id.group_kh2_id.name == 'CỬA HÀNG':
                    mitsubishi_5 += order_line.price_subtotal if not order_line.sale_order_return else -order_line.price_subtotal
                hang_ms.append({
                    'date_order': datetime.strptime(order_line.date_order, DEFAULT_SERVER_DATETIME_FORMAT).strftime(
                        "%d/%m/%Y"),
                    'order_name': order_line.order_id.name,
                    # 'partner_name': order_line.order_partner_id.name,
                    'default_code': order_line.product_id.default_code,
                    'product_name': order_line.product_id.name,
                    'uom': order_line.product_uom.name,
                    'qty': order_line.product_uom_qty if not order_line.sale_order_return else -order_line.product_uom_qty,
                    'price_unit': order_line.final_price if not order_line.sale_order_return else -order_line.final_price,
                    'price_subtotal': order_line.price_subtotal if not order_line.sale_order_return else -order_line.price_subtotal,
                    'discount': order_line.discount,
                })
            if 'SH-' in order_line.product_id.default_code:
                schneider_sum_1 += order_line.price_subtotal if not order_line.sale_order_return else -order_line.price_subtotal
                if order_line.order_partner_id.group_kh2_id.name == 'TUẤN HUY':
                    schneider_sum_2 += order_line.price_subtotal if not order_line.sale_order_return else -order_line.price_subtotal
                elif order_line.order_partner_id.group_kh2_id.name == 'CTY':
                    schneider_sum_3 += order_line.price_subtotal if not order_line.sale_order_return else -order_line.price_subtotal
                elif order_line.order_partner_id.group_kh2_id.name == 'KHÁCH LẺ':
                    schneider_sum_4 += order_line.price_subtotal if not order_line.sale_order_return else -order_line.price_subtotal
                elif order_line.order_partner_id.group_kh2_id.name == 'CỬA HÀNG':
                    schneider_sum_5 += order_line.price_subtotal if not order_line.sale_order_return else -order_line.price_subtotal
                hang_sh.append({
                    'date_order': datetime.strptime(order_line.date_order, DEFAULT_SERVER_DATETIME_FORMAT).strftime(
                        "%d/%m/%Y"),
                    'order_name': order_line.order_id.name,
                    # 'partner_name': order_line.order_partner_id.name,
                    'default_code': order_line.product_id.default_code,
                    'product_name': order_line.product_id.name,
                    'uom': order_line.product_uom.name,
                    'qty': order_line.product_uom_qty if not order_line.sale_order_return else -order_line.product_uom_qty,
                    'price_unit': order_line.final_price if not order_line.sale_order_return else -order_line.final_price,
                    'price_subtotal': order_line.price_subtotal if not order_line.sale_order_return else -order_line.price_subtotal,
                    'discount': order_line.discount,
                })

        start_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT)
        tong_hop.append({
            'STT': False,
            'dien_giai_chung': "TỔNG DOANH THU tháng %s NĂM %s" % (start_date.month, start_date.year),
            'doanh_thu': doanh_thu_sum_1,
            'schneider': schneider_sum_1,
            'ls': ls_sum_1,
            'th': th_sum_1,
            'sp': sp_sum_1,
            'day_dien': day_dien_1,
            'mitsubishi': mitsubishi_1,
            'khac': doanh_thu_sum_1 - schneider_sum_1 - ls_sum_1 - day_dien_1 - mitsubishi_1 - th_sum_1,
        })

        tong_hop.append({
            'STT': "I",
            'dien_giai_chung': "CÔNG TY TNHH CƠ ĐIỆN TUẤN HUY",
            'doanh_thu': doanh_thu_sum_2,
            'schneider': schneider_sum_2,
            'ls': ls_sum_2,
            'th': th_sum_2,
            'sp': sp_sum_2,
            'day_dien': day_dien_2,
            'mitsubishi': mitsubishi_2,
            'khac': doanh_thu_sum_2 - schneider_sum_2 - ls_sum_2 - day_dien_2 - mitsubishi_2 - th_sum_2,
        })

        tong_hop.append({
            'STT': "II",
            'dien_giai_chung': "CÔNG TY KHÁC",
            'doanh_thu': doanh_thu_sum_3,
            'schneider': schneider_sum_3,
            'ls': ls_sum_3,
            'th': th_sum_3,
            'sp': sp_sum_3,
            'day_dien': day_dien_3,
            'mitsubishi': mitsubishi_3,
            'khac': doanh_thu_sum_3 - schneider_sum_3 - ls_sum_3 - day_dien_3 - mitsubishi_3 - th_sum_3,
        })

        tong_hop.append({
            'STT': "III",
            'dien_giai_chung': "KHÁCH LẺ",
            'doanh_thu': doanh_thu_sum_4,
            'schneider': schneider_sum_4,
            'ls': ls_sum_4,
            'th': th_sum_4,
            'sp': sp_sum_4,
            'day_dien': day_dien_4,
            'mitsubishi': mitsubishi_4,
            'khac': doanh_thu_sum_4 - schneider_sum_4 - ls_sum_4 - day_dien_4 - mitsubishi_4 - th_sum_4,
        })

        tong_hop.append({
            'STT': "IV",
            'dien_giai_chung': "CÁC CỬA HÀNG",
            'doanh_thu': doanh_thu_sum_5,
            'schneider': schneider_sum_5,
            'ls': ls_sum_5,
            'th': th_sum_5,
            'sp': sp_sum_5,
            'day_dien': day_dien_5,
            'mitsubishi': mitsubishi_5,
            'khac': doanh_thu_sum_5 - schneider_sum_5 - ls_sum_5 - day_dien_5 - mitsubishi_5 - th_sum_5,
        })
        diff = doanh_thu_sum_1 - schneider_sum_1 - ls_sum_1 - day_dien_1 - mitsubishi_1 - th_sum_5
        tong_hop.append({
            'STT': False,
            'dien_giai_chung': "TỶ LỆ",
            'doanh_thu': "",
            'schneider': '{0:,.2f}'.format(
                schneider_sum_1 / doanh_thu_sum_1 * 100) + " %" if schneider_sum_1 and doanh_thu_sum_1 else '0.00 %',
            'ls': '{0:,.2f}'.format(
                ls_sum_1 / doanh_thu_sum_1 * 100) + " %" if ls_sum_1 and doanh_thu_sum_1 else '0.00 %',
            'th': '{0:,.2f}'.format(
                th_sum_1 / doanh_thu_sum_1 * 100) + " %" if th_sum_1 and doanh_thu_sum_1 else '0.00 %',
            'sp': '{0:,.2f}'.format(
                sp_sum_1 / doanh_thu_sum_1 * 100) + " %" if sp_sum_1 and doanh_thu_sum_1 else '0.00 %',
            'day_dien': '{0:,.2f}'.format(
                day_dien_1 / doanh_thu_sum_1 * 100) + " %" if day_dien_1 and doanh_thu_sum_1 else '0.00 %',
            'mitsubishi': '{0:,.2f}'.format(
                mitsubishi_1 / doanh_thu_sum_1 * 100) + " %" if mitsubishi_1 and doanh_thu_sum_1 else '0.00 %',
            'khac': '{0:,.2f}'.format(diff / doanh_thu_sum_1 * 100) + " %" if diff and doanh_thu_sum_1 else '0.00 %',
        })

        tong_hop.append({
            'STT': "I",
            'dien_giai_chung': "Khách hàng gián tiếp",
            'doanh_thu': doanh_thu_tyle_2,
            'schneider': '{0:,.2f}'.format(
                doanh_thu_tyle_2 / doanh_thu_sum_1 * 100) + " %" if doanh_thu_tyle_2 and doanh_thu_sum_1 else '0.00 %',
            'ls': False,
            'th': False,
            'sp': False,
            'day_dien': False,
            'mitsubishi': False,
            'khac': False,
        })

        tong_hop.append({
            'STT': "II",
            'dien_giai_chung': "Khách hàng trực tiếp",
            'doanh_thu': doanh_thu_tyle_3,
            'schneider': '{0:,.2f}'.format(
                doanh_thu_tyle_3 / doanh_thu_sum_1 * 100) + " %" if doanh_thu_tyle_3 and doanh_thu_sum_1 else '0.00 %',
            'ls': False,
            'th': False,
            'sp': False,
            'day_dien': False,
            'mitsubishi': False,
            'khac': False,
        })

        data_report.update({
            'data_doanh_thu_chi_tiet': data_doanh_thu_chi_tiet,
            'kh_gian_tiep': kh_gian_tiep,
            'kh_truc_tiep': kh_truc_tiep,
            'hang_ls': hang_ls,
            'hang_th': hang_th,
            'hang_sp': hang_sp,
            'hang_day_dien': hang_day_dien,
            'hang_ms': hang_ms,
            'hang_sh': hang_sh,
            'tong_hop': tong_hop,
        })
        return data_report

    @api.multi
    def print_excel(self):
        output = StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        bold = workbook.add_format({'bold': True})
        merge_format = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': '16', 'border': 1})
        header1_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter', 'border': 1,
             'num_format': '#,##0'})
        header_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter', 'border': 1,
             'num_format': '#,##0', 'bg_color': 'cce0ff'})
        footer_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter', 'border': 1,
             'num_format': '#,##0', })
        body_bold_color = workbook.add_format(
            {'bold': False, 'font_size': '12', 'align': 'left', 'valign': 'vcenter', 'border': 1,
             'num_format': '#,##0', })
        body_bold_color_green = workbook.add_format(
            {'bold': False, 'font_size': '12', 'align': 'left', 'valign': 'vcenter', 'border': 1,
             'num_format': '#,##0', 'bg_color': '33CC66'})
        data_report = self.get_data_report()

        # TODO TONG HOP
        back_color = 'A1:H1'
        worksheet = workbook.add_worksheet('TONG HOP')
        worksheet.set_row(0, 25)
        worksheet.set_row(2, 20)
        worksheet.set_row(3, 20)
        worksheet.set_row(8, 20)
        start_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT)
        string = "BẢNG TỔNG HỢP THÁNG %s Năm %s" % (start_date.month, start_date.year)
        worksheet.merge_range(back_color, unicode(string, "utf-8"), merge_format)

        worksheet.set_column('A:A', 10)
        worksheet.set_column('B:B', 65)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 20)
        worksheet.set_column('G:G', 20)
        worksheet.set_column('H:H', 20)
        worksheet.set_column('I:I', 20)
        worksheet.set_column('J:J', 25)

        row = 2
        summary_header = ['STT', 'Diễn giải chung', 'DOANH THU', 'SCHNEIDER', 'LS',
                          'DÂY ĐIỆN', 'MITSUBISHI', 'TH', 'SP', 'CÁC SP KHÁC']
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in
         range(0, len(summary_header)) if summary_header[header_cell]]

        tong_hop = data_report.get('tong_hop', False)
        sum_doanh_so = 0.0
        for line in tong_hop:
            row += 1
            if row not in [3, 8]:
                worksheet.write(row, 0, line.get('STT', '') or '', body_bold_color)
                worksheet.write(row, 1, line.get('dien_giai_chung', '') or '', body_bold_color)
                # worksheet.write(row, 2, line.get('partner_name', False), body_bold_color)
                worksheet.write(row, 2, line.get('doanh_thu', '') or '', body_bold_color)
                worksheet.write(row, 3, line.get('schneider', '') or '', body_bold_color)
                worksheet.write(row, 4, line.get('ls', '') or '', body_bold_color)
                worksheet.write(row, 5, line.get('day_dien', '') or '', body_bold_color)
                worksheet.write(row, 6, line.get('mitsubishi', '') or '', body_bold_color)
                worksheet.write(row, 7, line.get('th', '') or '', body_bold_color)
                worksheet.write(row, 8, line.get('sp', '') or '', body_bold_color)
                worksheet.write(row, 9, line.get('khac', '') or '', body_bold_color)
            else:
                worksheet.write(row, 0, line.get('STT', '') or '', body_bold_color_green)
                worksheet.write(row, 1, line.get('dien_giai_chung', '') or '', body_bold_color_green)
                # worksheet.write(row, 2, line.get('partner_name', False), body_bold_color)
                worksheet.write(row, 2, line.get('doanh_thu', '') or '', body_bold_color_green)
                worksheet.write(row, 3, line.get('schneider', '') or '', body_bold_color_green)
                worksheet.write(row, 4, line.get('ls', '') or '', body_bold_color_green)
                worksheet.write(row, 5, line.get('day_dien', '') or '', body_bold_color_green)
                worksheet.write(row, 6, line.get('mitsubishi', '') or '', body_bold_color_green)
                worksheet.write(row, 7, line.get('th', '') or '', body_bold_color_green)
                worksheet.write(row, 8, line.get('sp', '') or '', body_bold_color_green)
                worksheet.write(row, 9, line.get('khac', '') or '', body_bold_color_green)

        # TODO DOANH THU CHI TIET
        back_color = 'A2:I2'
        back_color_date = 'A3:I3'
        worksheet1 = workbook.add_worksheet('Doanh thu chi tiet')
        worksheet1.set_row(1, 25)
        worksheet1.set_row(2, 18)
        worksheet1.merge_range(back_color, unicode("SỔ CHI TIẾT BÁN HÀNG TỔNG HỢP", "utf-8"), merge_format)
        start_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT).strftime("%d/%m/%Y")
        end_date = datetime.strptime(self.end_date, DEFAULT_SERVER_DATE_FORMAT).strftime(
            "%d/%m/%Y") if self.end_date else datetime.today().strftime("%d/%m/%Y")
        string = "Từ ngày %s đến ngày %s" % (start_date, end_date)
        worksheet1.merge_range(back_color_date, unicode(string, "utf-8"), header1_bold_color)

        worksheet1.set_column('A:A', 20)
        worksheet1.set_column('B:B', 20)
        worksheet1.set_column('C:C', 60)
        worksheet1.set_column('D:D', 30)
        worksheet1.set_column('E:E', 65)
        worksheet1.set_column('F:F', 10)
        worksheet1.set_column('G:G', 22)
        worksheet1.set_column('H:H', 15)
        worksheet1.set_column('I:I', 20)

        row = 4
        summary_header = ['Ngày lập đơn', 'Số đơn hàng', 'Tên khách hàng', 'Mã nội bộ', 'Tên hàng', 'ĐVT',
                          'Tổng số lượng', 'Đơn giá', 'Tổng tiền']
        [worksheet1.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in
         range(0, len(summary_header)) if summary_header[header_cell]]

        data_doanh_thu_chi_tiet = data_report.get('data_doanh_thu_chi_tiet', False)
        sum_doanh_so = 0.0
        for line in data_doanh_thu_chi_tiet:
            row += 1
            worksheet1.write(row, 0, line.get('date_order', False), body_bold_color)
            worksheet1.write(row, 1, line.get('order_name', False), body_bold_color)
            worksheet1.write(row, 2, line.get('partner_name', False), body_bold_color)
            worksheet1.write(row, 3, line.get('default_code', False), body_bold_color)
            worksheet1.write(row, 4, line.get('product_name', False), body_bold_color)
            worksheet1.write(row, 5, line.get('uom', False), body_bold_color)
            worksheet1.write(row, 6, line.get('qty', False), body_bold_color)
            worksheet1.write(row, 7, line.get('price_unit', False), body_bold_color)
            worksheet1.write(row, 8, line.get('price_subtotal', False), body_bold_color)
            sum_doanh_so += line.get('price_subtotal', False)
        row += 1
        worksheet1.write(row, 7, "Tổng doanh số", footer_bold_color)
        worksheet1.write(row, 8, sum_doanh_so, footer_bold_color)

        # TODO KH GIAN TIEP
        worksheet2 = workbook.add_worksheet('Khach hang gian tiep')

        worksheet2.set_column('A:A', 20)
        worksheet2.set_column('B:B', 20)
        worksheet2.set_column('C:C', 60)
        worksheet2.set_column('D:D', 30)
        worksheet2.set_column('E:E', 65)
        worksheet2.set_column('F:F', 10)
        worksheet2.set_column('G:G', 22)
        worksheet2.set_column('H:H', 15)
        worksheet2.set_column('I:I', 20)

        row = 0
        summary_header = ['Ngày lập đơn', 'Số đơn hàng', 'Tên khách hàng', 'Mã nội bộ', 'Tên hàng', 'ĐVT',
                          'Tổng số lượng', 'Đơn giá', 'Tổng tiền']
        [worksheet2.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in
         range(0, len(summary_header)) if summary_header[header_cell]]

        kh_gian_tiep = data_report.get('kh_gian_tiep', False)
        sum_doanh_so = 0.0
        for line in kh_gian_tiep:
            row += 1
            worksheet2.write(row, 0, line.get('date_order', False), body_bold_color)
            worksheet2.write(row, 1, line.get('order_name', False), body_bold_color)
            worksheet2.write(row, 2, line.get('partner_name', False), body_bold_color)
            worksheet2.write(row, 3, line.get('default_code', False), body_bold_color)
            worksheet2.write(row, 4, line.get('product_name', False), body_bold_color)
            worksheet2.write(row, 5, line.get('uom', False), body_bold_color)
            worksheet2.write(row, 6, line.get('qty', False), body_bold_color)
            worksheet2.write(row, 7, line.get('price_unit', False), body_bold_color)
            worksheet2.write(row, 8, line.get('price_subtotal', False), body_bold_color)
            sum_doanh_so += line.get('price_subtotal', False)
        row += 1
        worksheet2.write(row, 7, "Tổng doanh số", footer_bold_color)
        worksheet2.write(row, 8, sum_doanh_so, footer_bold_color)

        # TODO KH TRUC TIEP
        worksheet3 = workbook.add_worksheet('Khach hang truc tiep')

        worksheet3.set_column('A:A', 20)
        worksheet3.set_column('B:B', 20)
        worksheet3.set_column('C:C', 60)
        worksheet3.set_column('D:D', 30)
        worksheet3.set_column('E:E', 65)
        worksheet3.set_column('F:F', 10)
        worksheet3.set_column('G:G', 22)
        worksheet3.set_column('H:H', 15)
        worksheet3.set_column('I:I', 20)

        row = 0
        summary_header = ['Ngày lập đơn', 'Số đơn hàng', 'Tên khách hàng', 'Mã nội bộ', 'Tên hàng', 'ĐVT',
                          'Tổng số lượng', 'Đơn giá', 'Tổng tiền']
        [worksheet3.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in
         range(0, len(summary_header)) if summary_header[header_cell]]

        kh_truc_tiep = data_report.get('kh_truc_tiep', False)
        sum_doanh_so = 0.0
        for line in kh_truc_tiep:
            row += 1
            worksheet3.write(row, 0, line.get('date_order', False), body_bold_color)
            worksheet3.write(row, 1, line.get('order_name', False), body_bold_color)
            worksheet3.write(row, 2, line.get('partner_name', False), body_bold_color)
            worksheet3.write(row, 3, line.get('default_code', False), body_bold_color)
            worksheet3.write(row, 4, line.get('product_name', False), body_bold_color)
            worksheet3.write(row, 5, line.get('uom', False), body_bold_color)
            worksheet3.write(row, 6, line.get('qty', False), body_bold_color)
            worksheet3.write(row, 7, line.get('price_unit', False), body_bold_color)
            worksheet3.write(row, 8, line.get('price_subtotal', False), body_bold_color)
            sum_doanh_so += line.get('price_subtotal', False)
        row += 1
        worksheet3.write(row, 7, "Tổng doanh số", footer_bold_color)
        worksheet3.write(row, 8, sum_doanh_so, footer_bold_color)

        # TODO HANG LS
        back_color = 'A1:I1'
        back_color_date = 'A2:I2'
        worksheet4 = workbook.add_worksheet('HANG LS')
        worksheet4.set_row(0, 25)
        worksheet4.set_row(1, 18)
        worksheet4.merge_range(back_color, unicode("SỔ CHI TIẾT BÁN HÀNG THEO MÃ QUY CÁCH", "utf-8"), merge_format)
        start_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT).strftime("%d/%m/%Y")
        end_date = datetime.strptime(self.end_date, DEFAULT_SERVER_DATE_FORMAT).strftime(
            "%d/%m/%Y") if self.end_date else datetime.today().strftime("%d/%m/%Y")
        string = "Từ ngày %s đến ngày %s" % (start_date, end_date)
        worksheet4.merge_range(back_color_date, unicode(string, "utf-8"), header1_bold_color)

        worksheet4.set_column('A:A', 20)
        worksheet4.set_column('B:B', 20)
        worksheet4.set_column('C:C', 30)
        worksheet4.set_column('D:D', 65)
        worksheet4.set_column('E:E', 10)
        worksheet4.set_column('F:F', 22)
        worksheet4.set_column('G:G', 15)
        worksheet4.set_column('H:H', 20)
        worksheet4.set_column('I:I', 10)

        row = 2
        summary_header = ['Ngày chứng từ', 'Số chứng từ', 'Mã hàng', 'Tên hàng', 'ĐVT',
                          'Tổng số lượng', 'Đơn giá', 'Doanh số bán', 'Chiết khấu']
        [worksheet4.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in
         range(0, len(summary_header)) if summary_header[header_cell]]

        hang_ls = data_report.get('hang_ls', False)
        sum_doanh_so = 0.0
        for line in hang_ls:
            row += 1
            worksheet4.write(row, 0, line.get('date_order', False), body_bold_color)
            worksheet4.write(row, 1, line.get('order_name', False), body_bold_color)
            # worksheet4.write(row, 2, line.get('partner_name', False), body_bold_color)
            worksheet4.write(row, 2, line.get('default_code', False), body_bold_color)
            worksheet4.write(row, 3, line.get('product_name', False), body_bold_color)
            worksheet4.write(row, 4, line.get('uom', False), body_bold_color)
            worksheet4.write(row, 5, line.get('qty', False), body_bold_color)
            worksheet4.write(row, 6, line.get('price_unit', False), body_bold_color)
            worksheet4.write(row, 7, line.get('price_subtotal', False), body_bold_color)
            worksheet4.write(row, 8, line.get('discount', False), body_bold_color)
            sum_doanh_so += line.get('price_subtotal', False)
        row += 1
        worksheet4.write(row, 6, "Tổng doanh số", footer_bold_color)
        worksheet4.write(row, 7, sum_doanh_so, footer_bold_color)

        # TODO HANG DAY DIEN
        back_color = 'A1:I1'
        back_color_date = 'A2:I2'
        worksheet5 = workbook.add_worksheet('DAY DIEN')
        worksheet5.set_row(0, 25)
        worksheet5.set_row(1, 18)
        worksheet5.merge_range(back_color, unicode("SỔ CHI TIẾT BÁN HÀNG THEO MÃ QUY CÁCH", "utf-8"), merge_format)
        start_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT).strftime("%d/%m/%Y")
        end_date = datetime.strptime(self.end_date, DEFAULT_SERVER_DATE_FORMAT).strftime(
            "%d/%m/%Y") if self.end_date else datetime.today().strftime("%d/%m/%Y")
        string = "Từ ngày %s đến ngày %s" % (start_date, end_date)
        worksheet5.merge_range(back_color_date, unicode(string, "utf-8"), header1_bold_color)

        worksheet5.set_column('A:A', 20)
        worksheet5.set_column('B:B', 20)
        worksheet5.set_column('C:C', 30)
        worksheet5.set_column('D:D', 65)
        worksheet5.set_column('E:E', 10)
        worksheet5.set_column('F:F', 22)
        worksheet5.set_column('G:G', 15)
        worksheet5.set_column('H:H', 20)
        worksheet5.set_column('I:I', 10)

        row = 2
        summary_header = ['Ngày chứng từ', 'Số chứng từ', 'Mã hàng', 'Tên hàng', 'ĐVT',
                          'Tổng số lượng', 'Đơn giá', 'Doanh số bán', 'Chiết khấu']
        [worksheet5.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in
         range(0, len(summary_header)) if summary_header[header_cell]]

        hang_day_dien = data_report.get('hang_day_dien', False)
        sum_doanh_so = 0.0
        for line in hang_day_dien:
            row += 1
            worksheet5.write(row, 0, line.get('date_order', False), body_bold_color)
            worksheet5.write(row, 1, line.get('order_name', False), body_bold_color)
            # worksheet5.write(row, 2, line.get('partner_name', False), body_bold_color)
            worksheet5.write(row, 2, line.get('default_code', False), body_bold_color)
            worksheet5.write(row, 3, line.get('product_name', False), body_bold_color)
            worksheet5.write(row, 4, line.get('uom', False), body_bold_color)
            worksheet5.write(row, 5, line.get('qty', False), body_bold_color)
            worksheet5.write(row, 6, line.get('price_unit', False), body_bold_color)
            worksheet5.write(row, 7, line.get('price_subtotal', False), body_bold_color)
            worksheet5.write(row, 8, line.get('discount', False), body_bold_color)
            sum_doanh_so += line.get('price_subtotal', False)
        row += 1
        worksheet5.write(row, 6, "Tổng doanh số", footer_bold_color)
        worksheet5.write(row, 7, sum_doanh_so, footer_bold_color)

        # TODO MITSUBISHI
        back_color = 'A1:I1'
        back_color_date = 'A2:I2'
        worksheet6 = workbook.add_worksheet('MITSUBISHI')
        worksheet6.set_row(0, 25)
        worksheet6.set_row(1, 18)
        worksheet6.merge_range(back_color, unicode("SỔ CHI TIẾT BÁN HÀNG THEO MÃ QUY CÁCH", "utf-8"), merge_format)
        start_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT).strftime("%d/%m/%Y")
        end_date = datetime.strptime(self.end_date, DEFAULT_SERVER_DATE_FORMAT).strftime(
            "%d/%m/%Y") if self.end_date else datetime.today().strftime("%d/%m/%Y")
        string = "Từ ngày %s đến ngày %s" % (start_date, end_date)
        worksheet6.merge_range(back_color_date, unicode(string, "utf-8"), header1_bold_color)

        worksheet6.set_column('A:A', 20)
        worksheet6.set_column('B:B', 20)
        worksheet6.set_column('C:C', 30)
        worksheet6.set_column('D:D', 65)
        worksheet6.set_column('E:E', 10)
        worksheet6.set_column('F:F', 22)
        worksheet6.set_column('G:G', 15)
        worksheet6.set_column('H:H', 20)
        worksheet6.set_column('I:I', 10)

        row = 2
        summary_header = ['Ngày chứng từ', 'Số chứng từ', 'Mã hàng', 'Tên hàng', 'ĐVT',
                          'Tổng số lượng', 'Đơn giá', 'Doanh số bán', 'Chiết khấu']
        [worksheet6.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in
         range(0, len(summary_header)) if summary_header[header_cell]]

        hang_ms = data_report.get('hang_ms', False)
        sum_doanh_so = 0.0
        for line in hang_ms:
            row += 1
            worksheet6.write(row, 0, line.get('date_order', False), body_bold_color)
            worksheet6.write(row, 1, line.get('order_name', False), body_bold_color)
            # worksheet6.write(row, 2, line.get('partner_name', False), body_bold_color)
            worksheet6.write(row, 2, line.get('default_code', False), body_bold_color)
            worksheet6.write(row, 3, line.get('product_name', False), body_bold_color)
            worksheet6.write(row, 4, line.get('uom', False), body_bold_color)
            worksheet6.write(row, 5, line.get('qty', False), body_bold_color)
            worksheet6.write(row, 6, line.get('price_unit', False), body_bold_color)
            worksheet6.write(row, 7, line.get('price_subtotal', False), body_bold_color)
            worksheet6.write(row, 8, line.get('discount', False), body_bold_color)
            sum_doanh_so += line.get('price_subtotal', False)
        row += 1
        worksheet6.write(row, 6, "Tổng doanh số", footer_bold_color)
        worksheet6.write(row, 7, sum_doanh_so, footer_bold_color)

        # TODO SCHNEIDER
        back_color = 'A1:I1'
        back_color_date = 'A2:I2'
        worksheet7 = workbook.add_worksheet('SCHNEIDER')
        worksheet7.set_row(0, 25)
        worksheet7.set_row(1, 18)
        worksheet7.merge_range(back_color, unicode("SỔ CHI TIẾT BÁN HÀNG THEO MÃ QUY CÁCH", "utf-8"), merge_format)
        start_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT).strftime("%d/%m/%Y")
        end_date = datetime.strptime(self.end_date, DEFAULT_SERVER_DATE_FORMAT).strftime(
            "%d/%m/%Y") if self.end_date else datetime.today().strftime("%d/%m/%Y")
        string = "Từ ngày %s đến ngày %s" % (start_date, end_date)
        worksheet7.merge_range(back_color_date, unicode(string, "utf-8"), header1_bold_color)

        worksheet7.set_column('A:A', 20)
        worksheet7.set_column('B:B', 20)
        worksheet7.set_column('C:C', 30)
        worksheet7.set_column('D:D', 65)
        worksheet7.set_column('E:E', 10)
        worksheet7.set_column('F:F', 22)
        worksheet7.set_column('G:G', 15)
        worksheet7.set_column('H:H', 20)
        worksheet7.set_column('I:I', 10)

        row = 2
        summary_header = ['Ngày chứng từ', 'Số chứng từ', 'Mã hàng', 'Tên hàng', 'ĐVT',
                          'Tổng số lượng', 'Đơn giá', 'Doanh số bán', 'Chiết khấu']
        [worksheet7.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in
         range(0, len(summary_header)) if summary_header[header_cell]]

        hang_sh = data_report.get('hang_sh', False)
        sum_doanh_so = 0.0
        for line in hang_sh:
            row += 1
            worksheet7.write(row, 0, line.get('date_order', False), body_bold_color)
            worksheet7.write(row, 1, line.get('order_name', False), body_bold_color)
            # worksheet7.write(row, 2, line.get('partner_name', False), body_bold_color)
            worksheet7.write(row, 2, line.get('default_code', False), body_bold_color)
            worksheet7.write(row, 3, line.get('product_name', False), body_bold_color)
            worksheet7.write(row, 4, line.get('uom', False), body_bold_color)
            worksheet7.write(row, 5, line.get('qty', False), body_bold_color)
            worksheet7.write(row, 6, line.get('price_unit', False), body_bold_color)
            worksheet7.write(row, 7, line.get('price_subtotal', False), body_bold_color)
            worksheet7.write(row, 8, line.get('discount', False), body_bold_color)
            sum_doanh_so += line.get('price_subtotal', False)
        row += 1
        worksheet7.write(row, 6, "Tổng doanh số", footer_bold_color)
        worksheet7.write(row, 7, sum_doanh_so, footer_bold_color)

        # TODO HANG TH
        back_color = 'A1:I1'
        back_color_date = 'A2:I2'
        worksheet4 = workbook.add_worksheet('HANG TH')
        worksheet4.set_row(0, 25)
        worksheet4.set_row(1, 18)
        worksheet4.merge_range(back_color, unicode("SỔ CHI TIẾT BÁN HÀNG THEO MÃ QUY CÁCH", "utf-8"), merge_format)
        start_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT).strftime("%d/%m/%Y")
        end_date = datetime.strptime(self.end_date, DEFAULT_SERVER_DATE_FORMAT).strftime(
            "%d/%m/%Y") if self.end_date else datetime.today().strftime("%d/%m/%Y")
        string = "Từ ngày %s đến ngày %s" % (start_date, end_date)
        worksheet4.merge_range(back_color_date, unicode(string, "utf-8"), header1_bold_color)

        worksheet4.set_column('A:A', 20)
        worksheet4.set_column('B:B', 20)
        worksheet4.set_column('C:C', 30)
        worksheet4.set_column('D:D', 65)
        worksheet4.set_column('E:E', 10)
        worksheet4.set_column('F:F', 22)
        worksheet4.set_column('G:G', 15)
        worksheet4.set_column('H:H', 20)
        worksheet4.set_column('I:I', 10)

        row = 2
        summary_header = ['Ngày chứng từ', 'Số chứng từ', 'Mã hàng', 'Tên hàng', 'ĐVT',
                          'Tổng số lượng', 'Đơn giá', 'Doanh số bán', 'Chiết khấu']
        [worksheet4.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in
         range(0, len(summary_header)) if summary_header[header_cell]]

        hang_th = data_report.get('hang_th', False)
        sum_doanh_so = 0.0
        for line in hang_th:
            row += 1
            worksheet4.write(row, 0, line.get('date_order', False), body_bold_color)
            worksheet4.write(row, 1, line.get('order_name', False), body_bold_color)
            # worksheet4.write(row, 2, line.get('partner_name', False), body_bold_color)
            worksheet4.write(row, 2, line.get('default_code', False), body_bold_color)
            worksheet4.write(row, 3, line.get('product_name', False), body_bold_color)
            worksheet4.write(row, 4, line.get('uom', False), body_bold_color)
            worksheet4.write(row, 5, line.get('qty', False), body_bold_color)
            worksheet4.write(row, 6, line.get('price_unit', False), body_bold_color)
            worksheet4.write(row, 7, line.get('price_subtotal', False), body_bold_color)
            worksheet4.write(row, 8, line.get('discount', False), body_bold_color)
            sum_doanh_so += line.get('price_subtotal', False)
        row += 1
        worksheet4.write(row, 6, "Tổng doanh số", footer_bold_color)
        worksheet4.write(row, 7, sum_doanh_so, footer_bold_color)

        # TODO HANG SP
        back_color = 'A1:I1'
        back_color_date = 'A2:I2'
        worksheet4 = workbook.add_worksheet('HANG SP')
        worksheet4.set_row(0, 25)
        worksheet4.set_row(1, 18)
        worksheet4.merge_range(back_color, unicode("SỔ CHI TIẾT BÁN HÀNG THEO MÃ QUY CÁCH", "utf-8"), merge_format)
        start_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT).strftime("%d/%m/%Y")
        end_date = datetime.strptime(self.end_date, DEFAULT_SERVER_DATE_FORMAT).strftime(
            "%d/%m/%Y") if self.end_date else datetime.today().strftime("%d/%m/%Y")
        string = "Từ ngày %s đến ngày %s" % (start_date, end_date)
        worksheet4.merge_range(back_color_date, unicode(string, "utf-8"), header1_bold_color)

        worksheet4.set_column('A:A', 20)
        worksheet4.set_column('B:B', 20)
        worksheet4.set_column('C:C', 30)
        worksheet4.set_column('D:D', 65)
        worksheet4.set_column('E:E', 10)
        worksheet4.set_column('F:F', 22)
        worksheet4.set_column('G:G', 15)
        worksheet4.set_column('H:H', 20)
        worksheet4.set_column('I:I', 10)

        row = 2
        summary_header = ['Ngày chứng từ', 'Số chứng từ', 'Mã hàng', 'Tên hàng', 'ĐVT',
                          'Tổng số lượng', 'Đơn giá', 'Doanh số bán', 'Chiết khấu']
        [worksheet4.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in
         range(0, len(summary_header)) if summary_header[header_cell]]

        hang_sp = data_report.get('hang_sp', False)
        sum_doanh_so = 0.0
        for line in hang_sp:
            row += 1
            worksheet4.write(row, 0, line.get('date_order', False), body_bold_color)
            worksheet4.write(row, 1, line.get('order_name', False), body_bold_color)
            # worksheet4.write(row, 2, line.get('partner_name', False), body_bold_color)
            worksheet4.write(row, 2, line.get('default_code', False), body_bold_color)
            worksheet4.write(row, 3, line.get('product_name', False), body_bold_color)
            worksheet4.write(row, 4, line.get('uom', False), body_bold_color)
            worksheet4.write(row, 5, line.get('qty', False), body_bold_color)
            worksheet4.write(row, 6, line.get('price_unit', False), body_bold_color)
            worksheet4.write(row, 7, line.get('price_subtotal', False), body_bold_color)
            worksheet4.write(row, 8, line.get('discount', False), body_bold_color)
            sum_doanh_so += line.get('price_subtotal', False)
        row += 1
        worksheet4.write(row, 6, "Tổng doanh số", footer_bold_color)
        worksheet4.write(row, 7, sum_doanh_so, footer_bold_color)

        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create(
            {'name': 'BAO CAO DOANH THU.xlsx', 'datas_fname': 'BAO CAO DOANH THU.xlsx', 'datas': result})
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return {"type": "ir.actions.act_url",
                "url": str(base_url) + str(download_url)}
