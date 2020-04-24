# -*- coding: utf-8 -*-
import xlsxwriter
import StringIO
from odoo import models, fields, api
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

class vieterp_product(models.Model):
    _inherit = 'product.product'

    sp_ban_chua_giao = fields.Integer(compute='_compute_product', string="SL bán chưa giao")
    sp_da_bao_gia    = fields.Integer(compute='_compute_product', string="SL đã báo giá")
    sp_co_the_ban    = fields.Integer(compute='_compute_product', string="SL có thể bán")

    @api.model
    def get_categ_list(self):
        categ_ids = self.env['product.category'].search([]).sorted('display_name', reverse=False).with_context({
            'lang': self.env.user.lang or 'vi_VN'
        }).mapped('display_name')
        categ_list = []
        for categ_id in categ_ids:
            categ_list.append(categ_id.replace("/", ">>"))
        return categ_list

    @api.model
    def get_categ_name_search(self, categ_name):
        if categ_name:
            categ_list = categ_name.split('>>')
            parent_id = False
            for categ in categ_list:
                domain = [('name', '=', categ.strip())]
                if not parent_id:
                    categ_id = self.env['product.category'].search(domain)
                    if not categ_id:
                        break
                    parent_id = categ_id
                else:
                    domain.append(('parent_id', '=', parent_id.id))
                    categ_id = self.env['product.category'].search(domain)
                    if not categ_id:
                        break
                    parent_id = categ_id

            if parent_id:
                product_ids = self.env['product.product'].search([('categ_id', '=', parent_id.id)])
                return product_ids.ids
            else:
                return []


    @api.depends('qty_available', 'virtual_available')
    def _compute_product(self):
        for rec in self:
            move_obj = self.env['sale.order.line'].sudo()

            sale_line_ids = move_obj.search([('product_id', '=', rec.id),('state', 'in', ['sale'])])
            sp_ban_chua_giao = 0
            for line in sale_line_ids:
                if not line.order_id.picking_ids:
                    sp_ban_chua_giao += line.product_uom_qty
                elif not all(state in ['done', 'cancel']  for state in  line.order_id.picking_ids.mapped('state')):
                    sp_ban_chua_giao += line.product_uom_qty

            rec.sp_ban_chua_giao = sp_ban_chua_giao

            rec.sp_co_the_ban = 0

            rec.sp_da_bao_gia = sum(move_obj.search([
                ('product_id', '=', rec.id),
                ('state', 'in', ['draft', 'sent'])
            ]).mapped('product_uom_qty'))
            rec.sp_co_the_ban = rec.qty_available - rec.sp_ban_chua_giao - rec.sp_da_bao_gia

    @api.model
    def print_product_excel(self, response):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        product_ids = self.env['product.product'].search(domain)
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Biến thể sản phẩm')

        body_bold_color = workbook.add_format({'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        text_style = workbook.add_format({'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format({'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')

        worksheet.set_column('A:N', 20)
        attribute_list = product_ids.mapped('attribute_value_ids').mapped('attribute_id').mapped('name')

        summary_header = ['Nhóm sản phẩm', 'Mã biến thể (variant)', 'Tên sản phẩm'] + attribute_list + [
                'Giá bán', 'Giá vốn', 'SL tổng TK', 'SL bán chưa giao', 'SL đã báo giá', 'SL có thể bán']

        row = 0
        [worksheet.write(row, header_cell, unicode(str(summary_header[header_cell]), "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for product_id in product_ids:
            row += 1
            # thuoc_tinh_1 = ''
            # thuoc_tinh_2 = ''
            # if len(product_id.attribute_value_ids) >= 1:
            #     thuoc_tinh_1 = product_id.attribute_value_ids[0].display_name
            # if len(product_id.attribute_value_ids) >= 2:
            #     thuoc_tinh_2 = product_id.attribute_value_ids[1].display_name
            thuoc_tinh_list = []
            for attribute in attribute_list:
                check = False
                for product_attribute in product_id.attribute_value_ids:
                    if attribute == product_attribute.attribute_id.name:
                        thuoc_tinh_list.append(product_attribute.name)
                        check = True
                        break
                if not check:
                    thuoc_tinh_list.append('')
            col = 2
            worksheet.write(row, 0, product_id.categ_id.display_name.replace("/", ">>"), text_style)
            worksheet.write(row, 1, product_id.default_code if product_id.default_code else '', text_style)
            worksheet.write(row, 2, product_id.name, text_style)
            # worksheet.write(row, 3, thuoc_tinh_1, text_style)
            # worksheet.write(row, 4, thuoc_tinh_2, text_style)
            for thuoc_tinh in thuoc_tinh_list:
                col += 1
                worksheet.write(row, col, thuoc_tinh or '', text_style)
            col += 1
            worksheet.write(row, col, product_id.lst_price, body_bold_color_number)
            # if self.check_group_show_cost():
            #     col += 1
            #     worksheet.write(row, col, product_id.standard_price, body_bold_color_number)
            col += 1
            worksheet.write(row, col, product_id.standard_price, body_bold_color_number)
            col += 1
            worksheet.write(row, col, product_id.qty_available, body_bold_color_number)
            col += 1
            worksheet.write(row, col, product_id.sp_ban_chua_giao, body_bold_color_number)
            col += 1
            worksheet.write(row, col, product_id.sp_da_bao_gia, body_bold_color_number)
            col += 1
            worksheet.write(row, col, product_id.sp_co_the_ban, body_bold_color_number)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()