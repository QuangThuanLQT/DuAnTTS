# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import StringIO
import xlsxwriter
import base64

class tuanhuy_stock_check_product(models.Model):
    _name = 'tuanhuy.stock.check_product'

    start_date = fields.Date(required=True)
    end_date = fields.Date()


    def daterange(self, date1, date2):
        result = []
        date1 = datetime.strptime(date1, DEFAULT_SERVER_DATE_FORMAT)
        date2 = datetime.strptime(date2, DEFAULT_SERVER_DATE_FORMAT)
        for n in range(int((date2 - date1).days) + 1):
            dateValue = date1 + timedelta(n)
            result.append(dateValue)
        return result

    def get_previous_date(self, date):
        result = date + timedelta(days=-1)
        result = result.strftime(DEFAULT_SERVER_DATE_FORMAT)
        return result

    def print_excel(self):
        product_ids = self.env['product.template'].search([])
        line = []
        location = False
        i = 1
        data = {
            'dau_ky': {},
            'trong_ky': {}
        }
        for product in product_ids:
            # print i
            first_qty_in = first_qty_out = incoming_qty = outgoing_qty = last_qty = 0
            domain_dauky = []
            domain_dauky.append(('date', '<', self.start_date))
            domain_dauky.append(('product_id', '=', product.product_variant_id.id))
            domain_dauky.append(('state', '=', 'done'))
            domain_dauky_in = domain_dauky + [('location_dest_id.name', '=', 'Stock')]
            domain_dauky_out = domain_dauky + [('location_dest_id.name', '!=', 'Stock')]

            stock_move_in_dau = self.env['stock.move'].search(domain_dauky_in)
            for stock_in_dau in stock_move_in_dau:
                first_qty_in += stock_in_dau.product_uom_qty
            stock_move_out_dau = self.env['stock.move'].search(domain_dauky_out)
            for stock_out_dau in stock_move_out_dau:
                first_qty_out += stock_out_dau.product_uom_qty
            ton_dauky = first_qty_in - first_qty_out
            data['dau_ky'][product] = ton_dauky

            range_date = False
            if self.end_date:
                range_date = self.daterange(self.start_date, self.end_date)
            else:
                now = datetime.now().date().strftime(DEFAULT_SERVER_DATE_FORMAT)
                range_date = self.daterange(self.start_date, now)
            for date in range_date:
                in_qty = 0
                out_qty = 0
                stock_ids = self.env['stock.move'].search([
                    ('date', '=', date),
                    ('product_id', '=', product.product_variant_id.id),
                    ('state', '=', 'done'),
                ])
                for stock in stock_ids:
                    if stock.location_dest_id.name == 'Stock':
                        in_qty += stock.product_uom_qty
                    elif stock.location_dest_id.name != 'Stock':
                        out_qty += stock.product_uom_qty
                date_qty = data['dau_ky'][product] + in_qty - out_qty

    def get_before_quantity(self, product_id, start_date):
        query = """SELECT 
            m.product_id, SUM(m.product_uom_qty) AS total_qty 
        FROM stock_move m 
        INNER JOIN stock_location l
        ON l.id = m.location_dest_id
        WHERE m.product_id = '%s' AND l.name = 'Stock' AND m.date < '%s' AND m.state = 'done'
        GROUP BY m.product_id""" % (product_id, start_date)
        self.env.cr.execute(query)
        lines = self.env.cr.fetchall()

        if lines and len(lines) > 0:
            total_qty_in = lines[0][1]
        else:
            total_qty_in = 0

        query = """SELECT 
            m.product_id, SUM(m.product_uom_qty) AS total_qty 
        FROM stock_move m 
        INNER JOIN stock_location l
        ON l.id = m.location_id
        WHERE m.product_id = '%s' AND l.name = 'Stock' AND m.date < '%s' AND m.state = 'done'
        GROUP BY m.product_id""" % (product_id, start_date)
        self.env.cr.execute(query)
        lines = self.env.cr.fetchall()

        if lines and len(lines):
            total_qty_out = lines[0][1]
        else:
            total_qty_out = 0

        result = total_qty_in - total_qty_out
        return result


    def print_excel_check_product(self):
        end_date = False
        if not self.end_date:
            end_date = datetime.now().date().strftime(DEFAULT_SERVER_DATE_FORMAT)
        else:
            end_date = self.end_date
        product_ids = self.env['product.product'].search([])
        data = {
            'dau_ky': {},
            'trong_ky': {}
        }
        for product in product_ids:
            # print i
            ton_dauky = self.get_before_quantity(product.id, self.start_date)
            data_dauky = {
                'product_name': product.name,
                'product_code': product.default_code,
                'qty': ton_dauky
            }
            data['dau_ky'][product.id] = data_dauky

        stock_ids = self.env['stock.move'].search([
            ('date', '>=', self.start_date),
            ('date', '<=', end_date),
            ('state', '=', 'done'),
        ])
        product_ids = stock_ids.mapped('product_id')
        range_date = self.daterange(self.start_date, end_date)
        for date in range_date:
            date_key = date.strftime(DEFAULT_SERVER_DATE_FORMAT)
            date_start = date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            date_end = date.replace(hour=23, minute=59, second=59).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            data['trong_ky'][date_key] = {}

            for product in product_ids:
                in_qty = out_qty = 0
                stock_in_date = self.env['stock.move'].search([
                    ('date', '>=', date_start),
                    ('date', '<=', date_end),
                    ('product_id', '=', product.id)
                ])
                if stock_in_date:
                    for stock_date in stock_in_date:
                        if stock_date.location_dest_id.name == 'Stock':
                            in_qty += stock_date.product_uom_qty
                        elif stock_date.location_dest_id.name != 'Stock':
                            out_qty += stock_date.product_uom_qty
                    previous_date = self.get_previous_date(date)
                    if previous_date in data['trong_ky'] and product in data['trong_ky'][previous_date]:
                        date_qty = data['trong_ky'][previous_date][product]['qty'] + in_qty - out_qty
                    else:
                        if product.id in data['dau_ky'].keys():
                            date_qty = data['dau_ky'][product.id]['qty'] + in_qty - out_qty
                    stock_date_data = {
                        'product_name': stock_date.product_id.name,
                        'product_code': stock_date.product_id.default_code,
                        'qty': date_qty
                    }
                    data['trong_ky'][date_key].update({
                        product.id: stock_date_data
                    })

        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Kiểm tra Dịch chuyển Sản phẩm')

        worksheet.set_column('A:A', 50)
        worksheet.set_column('B:B', 30)
        worksheet.set_column('C:C', 15)

        title = workbook.add_format(
            {'bold': True, 'font_size': '16', 'align': 'center', 'valign': 'vcenter'})
        header_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '13', 'align': 'center', 'valign': 'vcenter'})
        header_table_color = workbook.add_format(
            {'bold': False, 'border': 1, 'font_size': '8', 'align': 'center', 'valign': 'vcenter',
             'bg_color': 'cce0ff'})
        header_product_body = workbook.add_format(
            {'bold': False, 'border': 0, 'font_size': '13', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '13', 'align': 'right', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')

        body_color_number = workbook.add_format(
            {'bold': True, 'font_size': '13', 'align': 'right', 'valign': 'vcenter', 'bg_color': 'dddddd',
             'border': 0, })
        body_color_number.set_num_format('#,##0')

        header_bold_color_1 = workbook.add_format(
            {'bold': True, 'font_size': '13', 'align': 'left', 'valign': 'vcenter'})

        back_color = 'A1:C1'
        worksheet.merge_range(back_color, unicode("Kiểm tra Dịch chuyển Sản phẩm", "utf-8"), title)
        worksheet.merge_range('A2:C2',
                              unicode(("Từ ngày %s đến ngày %s") % (self.start_date, end_date),
                                      "utf-8"), header_bold_color)

        row = 4
        summary_header = ['Mã hàng', 'Tên hàng', 'Số lượng']
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_table_color) for header_cell in range(0, len(summary_header)) if summary_header[header_cell]]
        keys =  data['dau_ky'].keys()

        for key in keys:
            if data['dau_ky'][key]['qty'] < 0:
                row += 1
                worksheet.write(row, 0, data['dau_ky'][key]['product_name'], header_product_body)
                worksheet.write(row, 1, data['dau_ky'][key]['product_code'], header_product_body)
                worksheet.write(row, 2, data['dau_ky'][key]['qty'], body_bold_color_number)

        range_date = self.daterange(self.start_date, end_date)
        for date in range_date:
            date_key = date.strftime(DEFAULT_SERVER_DATE_FORMAT)
            if data['trong_ky'][date_key] and data['trong_ky'][date_key].keys():
                products = data['trong_ky'][date_key].keys()
                if len(products) > 0:
                    row += 1
                    worksheet.write(row, 0, date_key, header_bold_color_1)
                    product_data = data['trong_ky'][date_key]
                    for product in products:
                        if product_data[product]['qty'] < 0:
                            row += 1
                            worksheet.write(row, 0, product_data[product]['product_name'], header_product_body)
                            worksheet.write(row, 1, product_data[product]['product_code'], header_product_body)
                            worksheet.write(row, 2, product_data[product]['qty'], body_bold_color_number)

        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create(
            {'name': 'Kiểm tra Dịch chuyển Sản phẩm.xlsx', 'datas_fname': 'Kiểm tra Dịch chuyển Sản phẩm.xlsx', 'datas': result})
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return {"type": "ir.actions.act_url",
                "url": str(base_url) + str(download_url)}




