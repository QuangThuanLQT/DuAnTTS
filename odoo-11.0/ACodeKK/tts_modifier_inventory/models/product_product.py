# -*- coding: utf-8 -*-

from odoo import models, fields, api
import base64
import StringIO
import xlsxwriter

class product_product_ihr(models.Model):
    _inherit = 'product.product'

    location_ids = fields.Many2many('stock.location', string='Vị trí lưu trữ sản phẩm')

    def _get_domain_locations(self):
        # if 'location' in self._context:
        #     context = self._context.copy()
        #     dict = context.pop('location', None)
        #     self.env.context = context
        res = super(product_product_ihr, self)._get_domain_locations()
        for record in res:
            if 'location_id' in self._context:
                return res
            elif 'not_sellable_product' in self._context:
                domain = ('location_id.not_sellable', '=', True)
            else:
                domain = ('location_id.not_sellable', '=', False)
            record.append(domain)
        return res

    # @api.depends('qty_available', 'virtual_available')
    # def _compute_product(self):
    #     move_obj = self.env['stock.move'].sudo()
    #     dest_location = self.env.ref('stock.stock_location_customers')
    #     for rec in self:
    #         sp_ban_chua_giao = 0
    #         line_order_ids = self.env['sale.order.line'].search(
    #             [('product_id', '=', rec.id), ('order_id.state', 'in', ('sale', 'done'))])
    #         for line in line_order_ids:
    #             pick_ids = line.order_id.picking_ids.filtered(lambda r: r.check_is_pick == True)
    #             if all([pick.state != 'done' for pick in pick_ids]):
    #                 sp_ban_chua_giao += line.product_uom_qty
    #         line_ids = self.env['sale.order.line'].search(
    #             [('product_id', '=', rec.id), ('order_id.state', 'in', ('draft', 'sent'))])
    #         sp_da_bao_gia = sum(line_ids.mapped('product_uom_qty'))
    #         rec.sp_ban_chua_giao = sp_ban_chua_giao
    #         rec.sp_da_bao_gia = sp_da_bao_gia
    #         rec.sp_co_the_ban = rec.qty_available - rec.sp_ban_chua_giao - rec.sp_da_bao_gia

    @api.multi
    def export_detail(self):
        if self.env.context.get('active_ids',False) and self.env.context.get('active_model') == 'product.product':
            products = self.env['product.product'].browse(self.env.context.get('active_ids',False))
            output = StringIO.StringIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            worksheet = workbook.add_worksheet('Export Detail')
            bold = workbook.add_format({'bold': True})

            header_bold_color = workbook.add_format(
                {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter'})
            body_bold_color = workbook.add_format(
                {'bold': False, 'font_size': '14', 'align': 'left', 'valign': 'vcenter'})

            worksheet.set_column('A:A', 7)
            worksheet.set_column('B:B', 30)
            worksheet.set_column('C:C', 30)
            worksheet.set_column('D:D', 30)
            worksheet.set_column('E:E', 15)

            summary_header = ['STT', 'Internal Categories', 'Name Products', 'Attributes', 'Quantity']
            [worksheet.write(0, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
             header_cell in
             range(0, len(summary_header)) if summary_header[header_cell]]
            no = 0
            row = 0
            for line in products:
                no += 1
                row += 1
                worksheet.write(row, 0, no, body_bold_color)
                worksheet.write(row, 1, line.categ_id.display_name or '', body_bold_color)
                worksheet.write(row, 2, line.name, body_bold_color)
                worksheet.write(row, 3, ', '.join([value.display_name for value in line.attribute_value_ids]), body_bold_color)
                worksheet.write(row, 4, line.with_context(not_sellable_product=True).qty_available, body_bold_color)

            workbook.close()
            output.seek(0)
            result = base64.b64encode(output.read())
            attachment_obj = self.env['ir.attachment']
            attachment_id = attachment_obj.create(
                {'name': 'ExportDetail.xlsx', 'datas_fname': 'ExportDetail.xlsx', 'datas': result})
            download_url = '/web/content/' + str(attachment_id.id) + '?download=True'

            return {"type": "ir.actions.act_url",
                    "url": str(download_url)}

    @api.model
    def export_not_sellable_product(self, response):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        product_ids = self.env['product.product'].search(domain)

        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Thông tin chi tiết')

        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'center', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')
        header_bold_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'center', 'valign': 'vcenter'})
        header_bold_number.set_num_format('#,##0')
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})

        worksheet.set_column('A:A', 30)
        worksheet.set_column('B:B', 10)
        worksheet.set_column('C:C', 40)
        worksheet.set_column('D:D', 14)
        worksheet.set_column('E:E', 8)

        summary_header = ['Nhóm sản phẩm', ' Mã biến thể', 'Tên sản phẩm', 'Thuộc tính', 'Quantity on hand']

        row = 0
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for rec in product_ids:
            row += 1

            worksheet.write(row, 0, rec.categ_id.display_name.replace("/", ">>") or '', text_style)
            worksheet.write(row, 1, rec.default_code or '', text_style)
            worksheet.write(row, 2, rec.name or '', text_style)
            worksheet.write(row, 3, ','.join(attrs.name for attrs in rec.attribute_value_ids) or '', text_style)
            worksheet.write(row, 4, rec.with_context({'not_sellable_product': True}).qty_available , text_style)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
