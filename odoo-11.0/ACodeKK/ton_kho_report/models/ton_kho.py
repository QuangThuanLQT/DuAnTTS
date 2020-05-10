# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta
import base64
import StringIO
import xlsxwriter
from xlrd import open_workbook


class ton_kho_report(models.TransientModel):
    _name = 'ton.kho.report'

    location_id = fields.Many2one('stock.location', domain=[('usage', '=', 'internal')], string='Location', required=False)
    start_date  = fields.Date(String='Start Date', required=True)
    end_date    = fields.Date(String='End Date')
    product_ids = fields.Many2many('product.product', string='Products')
    product_xls = fields.Binary(string="Tập tin")

    @api.multi
    def print_report(self):
        return self.env['report'].get_action(self, 'ton_kho_report.ton_kho_report_template')

    def get_product_list(self):
        if self.product_xls:
            data = base64.b64decode(self.product_xls)
            wb = open_workbook(file_contents=data)
            sheet = wb.sheet_by_index(0)

            products = []
            for row_no in range(sheet.nrows):
                if row_no < 1:
                    continue
                row       = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                condition = [
                    # '|',
                    ('default_code', '=', row[0].strip()),
                    # ('barcode', '=', row[0].strip())
                ]
                product   = self.env['product.product'].search(condition, limit=1)
                if product and product.id:
                    products.append(product.id)
            return products

    @api.onchange('product_xls')
    def product_xls_import(self):
        # for record in self:
        if self.product_xls:
            products = self.get_product_list()
            self.product_ids = [(6, 0, products)]

    @api.model
    def get_data_report(self):
        self.ensure_one()

        data = {
            'ids': self.ids,
            'model': 'ton.kho.report',
            'lines': [],
        }

        if self.location_id and self.location_id.id:
            self.env.cr.execute("""
                SELECT MIN(id) as id,
                move_id,
                location_id,
                company_id,
                product_id,
                product_categ_id,
                product_name,
                product_template_id,
                SUM(quantity) as quantity,
                date,
                source
                FROM
                ((SELECT
                    stock_move.id AS id,
                    stock_move.id AS move_id,
                    dest_location.id AS location_id,
                    dest_location.company_id AS company_id,
                    stock_move.product_id AS product_id,
                    product_template.id AS product_template_id,
                    product_template.categ_id AS product_categ_id,
                    product_template.name AS product_name,
                    quant.qty AS quantity,
                    stock_move.date AS date,
                    quant.cost as price_unit_on_quant,
                    stock_move.origin AS source
                FROM
                    stock_quant as quant
                JOIN
                    stock_quant_move_rel ON stock_quant_move_rel.quant_id = quant.id
                JOIN
                    stock_move ON stock_move.id = stock_quant_move_rel.move_id
                JOIN
                    stock_location dest_location ON stock_move.location_dest_id = dest_location.id
                JOIN
                    stock_location source_location ON stock_move.location_id = source_location.id
                JOIN
                    product_product ON product_product.id = stock_move.product_id
                JOIN
                    product_template ON product_template.id = product_product.product_tmpl_id
                WHERE quant.qty>0 AND stock_move.state = 'done' AND dest_location.usage in ('internal', 'transit')
                AND (
                    not (source_location.company_id is null and dest_location.company_id is null) or
                    source_location.company_id != dest_location.company_id or
                    source_location.usage not in ('internal', 'transit'))
                ) UNION ALL
                (SELECT
                    (-1) * stock_move.id AS id,
                    stock_move.id AS move_id,
                    source_location.id AS location_id,
                    source_location.company_id AS company_id,
                    stock_move.product_id AS product_id,
                    product_template.id AS product_template_id,
                    product_template.categ_id AS product_categ_id,
                    product_template.name AS product_name,
                    - quant.qty AS quantity,
                    stock_move.date AS date,
                    quant.cost as price_unit_on_quant,
                    stock_move.origin AS source
                FROM
                    stock_quant as quant
                JOIN
                    stock_quant_move_rel ON stock_quant_move_rel.quant_id = quant.id
                JOIN
                    stock_move ON stock_move.id = stock_quant_move_rel.move_id
                JOIN
                    stock_location source_location ON stock_move.location_id = source_location.id
                JOIN
                    stock_location dest_location ON stock_move.location_dest_id = dest_location.id
                JOIN
                    product_product ON product_product.id = stock_move.product_id
                JOIN
                    product_template ON product_template.id = product_product.product_tmpl_id
                WHERE quant.qty>0 AND stock_move.state = 'done' AND source_location.usage in ('internal', 'transit')
                AND (
                    not (dest_location.company_id is null and source_location.company_id is null) or
                    dest_location.company_id != source_location.company_id or
                    dest_location.usage not in ('internal', 'transit'))
                ))
                AS foo
                GROUP BY move_id, location_id, company_id, product_id, product_name, product_categ_id, date, source, product_template_id
            """)
            lines = self.env.cr.fetchall()
            for line in lines:
                data['lines'].append({
                    'product_id': line[4],
                    'product_name': line[6],
                    'quantity': line[8],
                })

        return data

    @api.multi
    def print_report_stock(self):
        self.ensure_one()
        date_from = self.start_date
        date_to = self.end_date
        product_query = """SELECT 
                        pp.id as id,
                        pt.name as name, 
                        pp.default_code as default_code, 
                        uom.name as uom_name
                        FROM product_product pp
                        INNER JOIN product_template pt
                        INNER JOIN product_uom uom
                        ON uom.id = pt.uom_id
                        ON pp.product_tmpl_id = pt.id
                        """
        if self.product_xls:
            product_ids = self.get_product_list()
            product_query += """
            WHERE pp.id in (%s)
            """ %(', '.join(str(id) for id in product_ids))
            product_ids = self.env['product.product'].search([('id','in',product_ids)]).mapped('product_tmpl_id')

        i = 1
        data = {
            'ids': self.ids,
            'model': 'ton.kho.report',
            'lines': [],
        }

        self.env.cr.execute(product_query)
        product_data = self.env.cr.fetchall()


        total_first = total_in = total_out = total_last_qty = 0
        total_first_price = total_in_price = total_out_price = total_last_qty_price = 0
        for product in product_data:
            # print i
            product_id  = product[0]
            product_name = product[1]
            product_code = product[2]
            product_uom  = product[3]

            first_qty_in = first_qty_out = incoming_qty = outgoing_qty = last_qty = 0
            first_qty_in_price = outgoing_price = incoming_price = first_qty_out_price = 0.0

            accounts = self.env['account.account'].search([('code', '=like', '156%')])

            debit_before_query = """SELECT 
                SUM(aml.quantity) as quantity,
                SUM(aml.debit) AS debit, 
                SUM(aml.credit) AS credit
            FROM account_move_line aml 
            WHERE 
                aml.account_id in (%s)
                AND aml.debit > 0
                AND aml.date < '%s' 
                AND aml.product_id = '%s' """ % (', '.join(str(id) for id in accounts.ids), date_from, product_id)
            self.env.cr.execute(debit_before_query)
            move_before = self.env.cr.fetchall()
            if move_before and len(move_before) > 0:
                first_qty_in += move_before[0][0] or 0
                first_qty_in_price += move_before[0][1] or 0

            credit_before_query = """SELECT 
                SUM(aml.quantity) as quantity,
                SUM(aml.debit) AS debit, 
                SUM(aml.credit) AS credit
            FROM account_move_line aml 
            WHERE 
                aml.account_id in (%s)
                AND aml.credit > 0
                AND aml.date < '%s' 
                AND aml.product_id = '%s' """ % (', '.join(str(id) for id in accounts.ids), date_from, product_id)
            self.env.cr.execute(credit_before_query)
            move_before = self.env.cr.fetchall()
            if move_before and len(move_before) > 0:
                first_qty_out += move_before[0][0] or 0
                first_qty_out_price += move_before[0][2] or 0

            ton_dauky = first_qty_in - first_qty_out
            ton_dauky_price = first_qty_in_price - first_qty_out_price

            debit_current_query = """SELECT 
                SUM(aml.quantity) as quantity,
                SUM(aml.debit) AS debit, 
                SUM(aml.credit) AS credit
            FROM account_move_line aml 
            WHERE 
                aml.account_id in (%s)
                AND aml.debit > 0 
                AND aml.date >= '%s'
                AND aml.date <= '%s'
                AND aml.product_id = '%s' """ % (
            ', '.join(str(id) for id in accounts.ids), date_from, date_to, product_id)

            self.env.cr.execute(debit_current_query)
            move_before = self.env.cr.fetchall()
            if move_before and len(move_before) > 0:
                incoming_qty += move_before[0][0] or 0
                incoming_price += move_before[0][1] or 0

            credit_current_query = """SELECT 
                SUM(aml.quantity) as quantity,
                SUM(aml.debit) AS debit, 
                SUM(aml.credit) AS credit
            FROM account_move_line aml 
            WHERE 
                aml.account_id in (%s)
                AND aml.credit > 0
                AND aml.date >= '%s'
                AND aml.date <= '%s'
                AND aml.product_id = '%s' """ % (
            ', '.join(str(id) for id in accounts.ids), date_from, date_to, product_id)
            self.env.cr.execute(credit_current_query)
            move_before = self.env.cr.fetchall()
            if move_before and len(move_before) > 0:
                outgoing_qty += move_before[0][0] or 0
                outgoing_price += move_before[0][2] or 0

            last_qty = ton_dauky + incoming_qty - outgoing_qty
            last_price = ton_dauky_price + incoming_price - outgoing_price

            # res = product.with_context({'location': location, 'from_date': self.start_date, 'to_date': self.end_date})._compute_quantities_dict()
            total_first += ton_dauky
            total_in += incoming_qty
            total_out += outgoing_qty
            total_last_qty += last_qty
            total_first_price += ton_dauky_price
            total_in_price += incoming_price
            total_out_price += outgoing_price
            total_last_qty_price += last_price

            product_data = {
                'name': product_name,
                'default_code': product_code,
                'first_qty': ton_dauky,
                'price_first': ton_dauky_price,
                'incoming_qty': incoming_qty,
                'price_incoming': incoming_price,
                'outgoing_qty': outgoing_qty,
                'price_outgoing': outgoing_price,
                'last_qty': last_qty,
                'price_last': last_price,
            }

            data['lines'].append(product_data)
            i += 1
        data['total'] = {
            'first_qty': total_first,
            'price_first': total_first_price,
            'incoming_qty': total_in,
            'price_incoming': total_in_price,
            'outgoing_qty': total_out,
            'price_outgoing': total_out_price,
            'last_qty': total_last_qty,
            'price_last': total_last_qty_price,
        }
        return data

    @api.multi
    def print_report_excel(self):
        data = self.print_report_stock()
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Bao Cao Ton Kho')
        bold = workbook.add_format({'bold': True})
        merge_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': '16'})
        header_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter'})
        body_bold_color = workbook.add_format(
            {'bold': False, 'font_size': '14', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '14', 'align': 'right', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')
        back_color = 'C2:E2'
        worksheet.merge_range(back_color, unicode("BÁO CÁO TỒN KHO", "utf-8"), merge_format)
        worksheet.write(3, 0, unicode("Kỳ báo cáo:", "utf-8"), body_bold_color)
        worksheet.write(3, 8, self.start_date, body_bold_color)
        if self.end_date:
            worksheet.write(3, 9, self.end_date, body_bold_color)

        worksheet.set_column('A:A', 60)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 20)
        worksheet.set_column('G:G', 20)
        worksheet.set_column('H:H', 20)
        worksheet.set_column('I:I', 20)
        worksheet.set_column('J:J', 20)
        worksheet.set_column('K:K', 20)

        row = 5
        worksheet.merge_range(row, 0, row + 2, 0, unicode("Sản Phẩm", "utf-8"), header_bold_color)
        worksheet.merge_range(row, 1, row + 2, 1, unicode("Mã nội bộ", "utf-8"), header_bold_color)
        count = 0
        col = 2
        summary_header = ['Đầu kỳ', 'Nhập kho', 'Xuất kho', 'Cuối kỳ']
        summary_header_2 = ['Số lượng', 'Giá trị', 'Số lượng', 'Giá trị', 'Số lượng', 'Giá trị', 'Số lượng', 'Giá trị']
        [worksheet.merge_range(row, (2 + header_cell * 2), row, (2 + header_cell * 2 + 1),
                               unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]
        row += 1
        [worksheet.write(row, 2 + header_cell, unicode(summary_header_2[header_cell], "utf-8"), header_bold_color) for
         header_cell in range(0, len(summary_header_2)) if summary_header_2[header_cell]]
        row += 1
        worksheet.write(row, 2, data['total']['first_qty'], body_bold_color_number)
        worksheet.write(row, 3, data['total']['price_first'], body_bold_color_number)
        worksheet.write(row, 4, data['total']['incoming_qty'], body_bold_color_number)
        worksheet.write(row, 5, data['total']['price_incoming'], body_bold_color_number)
        worksheet.write(row, 6, data['total']['outgoing_qty'], body_bold_color_number)
        worksheet.write(row, 7, data['total']['price_outgoing'], body_bold_color_number)
        worksheet.write(row, 8, data['total']['last_qty'], body_bold_color_number)
        worksheet.write(row, 9, data['total']['price_last'], body_bold_color_number)

        for line in data['lines']:
            row += 1
            worksheet.write(row, 0, line['name'], body_bold_color)
            worksheet.write(row, 1, line['default_code'], body_bold_color)
            worksheet.write(row, 2, line['first_qty'], body_bold_color_number)
            worksheet.write(row, 3, line['price_first'], body_bold_color_number)
            worksheet.write(row, 4, line['incoming_qty'], body_bold_color_number)
            worksheet.write(row, 5, line['price_incoming'], body_bold_color_number)
            worksheet.write(row, 6, line['outgoing_qty'], body_bold_color_number)
            worksheet.write(row, 7, line['price_outgoing'], body_bold_color_number)
            worksheet.write(row, 8, line['last_qty'], body_bold_color_number)
            worksheet.write(row, 9, line['price_last'], body_bold_color_number)

        worksheet_vthh = workbook.add_worksheet('SoVatTuHangHoa')
        sheet_vthh = self.create_sheet_vthh(worksheet_vthh, workbook)

        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create(
            {'name': 'Baocaotonkho.xlsx', 'datas_fname': 'Baocaotonkho.xlsx', 'datas': result})
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return {"type": "ir.actions.act_url",
                "url": str(base_url) + str(download_url)}

    @api.multi
    def create_sheet_vthh(self, worksheet, workbook):
        self.ensure_one()

        worksheet.set_column('A:A', 2)
        worksheet.set_column('B:B', 2)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:D', 15)
        worksheet.set_column('E:E', 15)
        worksheet.set_column('F:F', 15)
        worksheet.set_column('G:G', 15)
        worksheet.set_column('H:H', 15)
        worksheet.set_column('I:I', 15)
        worksheet.set_column('J:J', 15)
        worksheet.set_column('K:K', 15)
        worksheet.set_column('M:R', 15)

        title = workbook.add_format(
            {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter'})
        header_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'center', 'valign': 'vcenter'})
        header_table_color = workbook.add_format(
            {'bold': False, 'border': 1, 'font_size': '8', 'align': 'center', 'valign': 'vcenter', 'bg_color': 'cce0ff'})
        header_product_color = workbook.add_format(
            {'bold': True, 'border': 0, 'font_size': '8', 'align': 'left', 'valign': 'vcenter'})
        header_product_body = workbook.add_format(
            {'bold': False, 'border': 0, 'font_size': '8', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '8', 'align': 'right', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')

        body_color_number = workbook.add_format(
            {'bold': False, 'font_size': '8', 'align': 'right', 'valign': 'vcenter', 'bg_color': 'dddddd', 'border': 1,})
        body_color_number.set_num_format('#,##0')

        back_color = 'A1:P1'
        worksheet.merge_range(back_color, unicode("SỔ CHI TIẾT VẬT TƯ HÀNG HÓA", "utf-8"), title)
        worksheet.merge_range('A2:P2',
                              unicode(("Kho: <<Tất cả>>; Từ ngày %s đến ngày %s") % (self.start_date, self.end_date),
                                      "utf-8"), header_bold_color)

        row = 3
        summary_header = ['Mã kho', 'Mã hàng', 'Tên kho', 'Tên hàng', 'Ngày hạch toán', 'Ngày chứng từ', 'Số chứng từ',
                          'Diễn giải', 'ĐVT', 'Đơn giá']
        [worksheet.merge_range(row, (2 + header_cell), row + 1, (2 + header_cell),
                               unicode(summary_header[header_cell], "utf-8"), header_table_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        summary_header_2 = ['Nhập', 'Xuất', 'Tồn']
        [worksheet.merge_range(row, (12 + header_cell * 2), row, (12 + header_cell * 2 + 1),
                               unicode(summary_header_2[header_cell], "utf-8"), header_table_color) for
         header_cell in range(0, len(summary_header_2)) if summary_header_2[header_cell]]

        summary_header_3 = ['Số lượng', 'Giá trị', 'Số lượng', 'Giá trị', 'Số lượng', 'Giá trị']
        row += 1
        [worksheet.write(row, 12 + header_cell, unicode(summary_header_3[header_cell], "utf-8"), header_table_color) for
         header_cell in range(0, len(summary_header_3)) if summary_header_3[header_cell]]
        data = {}
        warehouse_ids = self.env['stock.warehouse'].search([])
        for warehouse in warehouse_ids:
            data[warehouse.id] = {
                'name': warehouse.name,
                'location_id': warehouse.code,
                'data': {}
            }

            conditions = [
                ('date', '>=', self.start_date),
                ('warehouse_id', '=', warehouse.id)
            ]
            if self.end_date:
                conditions.append(('date', '<=', self.end_date))
            product_ids = self.get_product_list()
            if product_ids and len(product_ids) > 0:
                conditions.append(('product_id', 'in', product_ids))
            for product in self.env['stock.move'].search(conditions).mapped('product_id'):
                lines_product = []
                end_date = (
                datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT) - timedelta(days=1)).strftime(
                    DEFAULT_SERVER_DATE_FORMAT)
                start_date = date(
                    (datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT) - timedelta(days=1)).year, 1,
                    1).strftime(DEFAULT_SERVER_DATE_FORMAT)
                if end_date < start_date:
                    start_date = date(
                        (datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT) - timedelta(days=1)).year - 1,
                        1, 1).strftime(DEFAULT_SERVER_DATE_FORMAT)
                stock_dau = self.env['stock.move'].search([
                    ('date', '>=', start_date),
                    ('date', '<=', end_date),
                    ('location_dest_id.name', '=', 'Stock'),
                    ('product_id', '=', product.id),
                    ('state', '=', 'done')
                ])
                stock_cuoi = self.env['stock.move'].search([
                    ('date', '>=', start_date),
                    ('date', '<=', end_date),
                    ('location_dest_id.name', '!=', 'Stock'),
                    ('product_id', '=', product.id),
                    ('state', '=', 'done')
                ])
                tonkho = sum(stock_dau.mapped('product_uom_qty')) if stock_dau else 0 - sum(
                    stock_cuoi.mapped('product_uom_qty')) if stock_dau else 0
                end_date_condition = self.end_date or datetime.now().date()
                for line in self.env['stock.move'].search([
                    ('date', '>=', self.start_date),
                    ('date', '<=', end_date_condition),
                    ('product_id', '=', product.id),
                    ('state', '=', 'done')
                ]):
                    incoming_qty = line.product_uom_qty if line.location_dest_id.name == 'Stock' else 0
                    outgoing_qty = line.product_uom_qty if line.location_dest_id.name != 'Stock' else 0
                    record = {
                        'product_id': line.product_id,
                        'picking_name': line.picking_id.name if line.picking_id else "",
                        'date': line.picking_id.date if line.picking_id else "",
                        'min_date': line.picking_id.min_date if line.picking_id else "",
                        'origin': line.picking_id.origin if line.picking_id else line.name,
                        'standard_price': line.product_id.standard_price,
                        'incoming_qty': incoming_qty,
                        'incoming_price': incoming_qty * line.product_id.standard_price,
                        'outgoing_qty': outgoing_qty,
                        'outgoing_price': outgoing_qty * line.product_id.standard_price
                    }
                    lines_product.append(record)
                data[warehouse.id]['data'][product.default_code] = {
                    'line': lines_product,
                    'qty': len(lines_product),
                    'default_code': product.default_code,
                    'sum_qty_in': sum([x['incoming_qty'] for x in lines_product]),
                    'total_in': sum([x['incoming_qty'] for x in lines_product]) * product.standard_price,
                    'sum_qty_out': sum([x['outgoing_qty'] for x in lines_product]),
                    'total_out': sum([x['outgoing_qty'] for x in lines_product]) * product.standard_price,
                    'ton_kho': tonkho
                }

        for location in data.keys():
            row += 1
            string = "Mã kho : %s (2663 )" % location
            worksheet.write(row, 0, unicode(string, "utf-8"), header_product_color)
            for product in data[location]['data'].keys():
                row += 1
                if data[location]['data'][product]['qty'] > 0:
                    string_product = " Mã hàng : %s (%s )" % (product, data[location]['data'][product]['qty'])
                    worksheet.write(row, 1, string_product, header_product_color)
                    worksheet.write(row, 12, data[location]['data'][product]['sum_qty_in'], body_color_number)
                    worksheet.write(row, 13, data[location]['data'][product]['total_in'], body_color_number)
                    worksheet.write(row, 14, data[location]['data'][product]['sum_qty_out'], body_color_number)
                    worksheet.write(row, 15, data[location]['data'][product]['total_out'], body_color_number)
                    ton_kho = data[location]['data'][product]['ton_kho']
                    for line in sorted(data[location]['data'][product]['line'], key=lambda k: k['date']):
                        ton_kho += line['incoming_qty'] - line['outgoing_qty']
                        row += 1
                        worksheet.write(row, 2, data[location]['location_id'], header_product_body)
                        worksheet.write(row, 3, product, header_product_body)
                        worksheet.write(row, 4, data[location]['name'], header_product_body)
                        worksheet.write(row, 5, line['product_id'].name, header_product_body)
                        worksheet.write(row, 6, line['min_date'], header_product_body)
                        worksheet.write(row, 7, line['date'], header_product_body)
                        worksheet.write(row, 8, line['picking_name'], header_product_body)
                        worksheet.write(row, 9, line['origin'], header_product_body)
                        worksheet.write(row, 10, line['product_id'].uom_id.name, header_product_body)
                        worksheet.write(row, 11, line['standard_price'], body_bold_color_number)
                        worksheet.write(row, 12, line['incoming_qty'], body_bold_color_number)
                        worksheet.write(row, 13, line['incoming_price'], body_bold_color_number)
                        worksheet.write(row, 14, line['outgoing_qty'], body_bold_color_number)
                        worksheet.write(row, 15, line['outgoing_price'], body_bold_color_number)
                        worksheet.write(row, 16, ton_kho, body_bold_color_number)
                        worksheet.write(row, 17, ton_kho * line['standard_price'], body_bold_color_number)