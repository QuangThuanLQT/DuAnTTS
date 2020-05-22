# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
import base64
from xlrd import open_workbook
from odoo.exceptions import UserError
import base64
import StringIO
import xlsxwriter

import sys

reload(sys)
sys.setdefaultencoding('utf-8')


class product_template_inherit(models.Model):
    _inherit = "product.template"

    def cron_update_product_barcode(self):
        query = """SELECT id FROM product_template WHERE active = TRUE and is_manual_barcode = TRUE"""
        self.env.cr.execute(query)
        product_ids = self.env.cr.fetchall()
        count = 0
        for product_id in product_ids:
            product_id = self.browse(product_id[0])
            if product_id.default_code and 'SH-' not in product_id.default_code and 'LS-' not in product_id.default_code:
                product_id.barcode = None
                product_id.fill_multi_barcode()
                count += 1
                print
                "------------%s" % (count)
            if not product_id.default_code:
                product_id.fill_multi_barcode()
                count += 1
                print
                "------------%s" % (count)


class import_purchase_order(models.Model):
    _name = 'import.product.template'

    import_data = fields.Binary(string="File Import")
    update_group_sale = fields.Boolean(string="update group sale",
                                       help="Nhap nhom ban hang vao sp. Col 0: default_code, Col 3: Ten nhom")
    update_product = fields.Boolean(string="update product")
    update_partner = fields.Boolean(string="update partner")
    update_unit_price = fields.Boolean(string="Update unit price")
    update_sale_tax = fields.Boolean(string="Update sale tax")
    update_brand_name = fields.Boolean(string="Import thương hiệu")
    import_by_cron = fields.Boolean()
    user_email = fields.Char(string="email")
    row_next = fields.Integer(default=1)

    @api.onchange('update_group_sale')
    def onchange_update_group_sale(self):
        for record in self:
            if record.update_group_sale:
                record.update_partner = False
                record.update_unit_price = False

    @api.onchange('update_partner')
    def onchange_update_partner(self):
        for record in self:
            if record.update_partner:
                record.update_group_sale = False
                record.update_unit_price = False

    @api.onchange('update_unit_price')
    def onchange_update_unit_price(self):
        for record in self:
            if record.update_unit_price:
                record.update_partner = False
                record.update_group_sale = False

    @api.multi
    def use_import_by_cron(self):
        data = base64.b64decode(self.import_data)
        wb = open_workbook(file_contents=data)
        sheet = wb.sheet_by_index(0)

        for row_no in range(sheet.nrows):
            if row_no == 0:
                continue
            line = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(
                row.value), sheet.row(row_no)))
            list_price_error = []
            try:
                a = line[7].strip() and float(line[7].strip()) or 0
                b = line[8].strip() and float(line[8].strip()) or 0
            except:
                list_price_error.append(row_no + 1)
            if list_price_error:
                error_warning = "Lỗi định dạng giá tại các dòng: "
                for error in list_price_error:
                    error_warning += "%s ," % (error)
                raise UserError(_(error_warning))
        self.import_by_cron = True
        self.row_next = 1

    @api.model
    def cron_import_by_cron(self):
        import_product_ids = self.search([('import_by_cron', '=', True)])
        for import_product_id in import_product_ids:
            try:
                import_product_id.import_xls()
                import_product_id.import_by_cron = False
            except:
                import_product_id.import_by_cron = False

    @api.multi
    def export_format(self):
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        if self.update_unit_price:
            worksheet = workbook.add_worksheet(str('Cập nhật giá sp'))
            worksheet.write(0, 0, str("Mã nội bộ"))
            worksheet.write(0, 1, str("Giá"))
            worksheet.write(1, 0, "XXXXX")
            worksheet.write(1, 1, "00000")
        elif self.update_group_sale:
            worksheet = workbook.add_worksheet(str('Cập nhật Nhóm sp bán hàng'))
            worksheet.write(0, 0, str("Mã nội bộ"))
            worksheet.write(0, 1, str("Nhóm sp bán hàng"))
            worksheet.write(1, 0, "XXXXX")
            worksheet.write(1, 1, "LS")
        else:
            worksheet = workbook.add_worksheet(str('Nhập sp mới'))
            worksheet.set_column('A:J', 20)
            worksheet.set_column('K:K', 30)
            worksheet.write(0, 0, str("Mã hàng"))
            worksheet.write(0, 1, str("barcode"))
            worksheet.write(0, 2, str("Tên"))
            worksheet.write(0, 3, str("ĐVT"))
            worksheet.write(0, 4, str("Mã mua hàng"))
            worksheet.write(0, 5, str("Thương hiệu"))
            worksheet.write(0, 6, str("Xuất sứ"))
            worksheet.write(0, 7, str("Giá bán"))
            worksheet.write(0, 8, str("Chi Phí"))
            worksheet.write(0, 9, str("Nhóm SP"))
            worksheet.write(0, 10, str("Nhóm sp bán hàng"))
            worksheet.write(1, 0, "ABB-1SDA079803R1")
            worksheet.write(1, 1, "2365986")
            worksheet.write(1, 2, "Aptomat (MCCB Formula) 3P 80A 5KA")
            worksheet.write(1, 3, "Cái")
            worksheet.write(1, 4, "1SDA079803R1")
            worksheet.write(1, 5, "ABB")
            worksheet.write(1, 6, "Việt Nam")
            worksheet.write(1, 7, "1,751,000")
            worksheet.write(1, 8, "1,751,000")
            worksheet.write(1, 9, "Aptomat")
            worksheet.write(1, 10, "Aptomat")

        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create({
            'name': 'format_import.xlsx',
            'datas_fname': 'format_import.xlsx',
            'datas': result
        })
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return {
            'type': 'ir.actions.act_url',
            'url': str(base_url) + str(download_url),
        }

    def send_mail_when_done_import(self):
        company_email = self.env['res.users'].browse(1).company_id.email
        mail_values = {
            'email_from': company_email,
            'email_to': self.user_email or 'nganty@tuanhuyco.com',
            'subject': 'Hoàn thành nhập sản phẩm',
            'body_html': "Hoàn thành nhập sản phẩm",
        }
        mail = self.env['mail.mail'].create(mail_values)
        mail.send()

    @api.multi
    def import_xls(self):
        for record in self:
            if record.import_data:
                if record.update_sale_tax:
                    data = base64.b64decode(record.import_data)
                    wb = open_workbook(file_contents=data)
                    sheet = wb.sheet_by_index(0)

                    for row_no in range(sheet.nrows):
                        if row_no > 0:
                            line = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(
                                row.value), sheet.row(row_no)))
                            if line[0].strip():
                                product_id = self.env['product.template'].search(
                                    [('default_code', '=', line[0].strip())])
                                if product_id and line[1].strip():
                                    amount_tax = float(line[1].strip()) * 100
                                    account_tax = self.env['account.tax'].search(
                                        [('type_tax_use', '=', 'sale'), ('amount', '=', amount_tax)])
                                    product_id.taxes_id = [(6, 0, account_tax.ids)]
                    break
                if record.update_unit_price:
                    data = base64.b64decode(record.import_data)
                    wb = open_workbook(file_contents=data)
                    sheet = wb.sheet_by_index(0)

                    output = StringIO.StringIO()
                    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
                    worksheet = workbook.add_worksheet('San Pham Khong Tim Thay')
                    row_write = 0
                    worksheet.write(row_write, 0, "So line")
                    worksheet.write(row_write, 1, "Mã hàng")
                    row_write += 1

                    for row_no in range(sheet.nrows):
                        if row_no == 0:
                            continue
                        line = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(
                            row.value), sheet.row(row_no)))
                        product_id = self.env['product.template'].search([('default_code', '=', line[0].strip())])
                        if not product_id:
                            print
                            "product_not_found: %s - %s" % (row_no + 1, line[0])
                            worksheet.write(row_write, 0, row_no + 1)
                            worksheet.write(row_write, 1, line[0])
                            row_write += 1
                        else:
                            product_id.list_price = float(line[1])
                    if row_write > 1:
                        workbook.close()
                        output.seek(0)
                        result = base64.b64encode(output.read())
                        attachment_obj = self.env['ir.attachment']
                        attachment_id = attachment_obj.create({
                            'name': 'san_pham_khong_tim_thay.xlsx',
                            'datas_fname': 'san_pham_khong_tim_thay.xlsx',
                            'datas': result
                        })
                        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
                        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
                        return {
                            'type': 'ir.actions.act_url',
                            'url': str(base_url) + str(download_url),
                        }

                if record.update_brand_name:
                    data = base64.b64decode(record.import_data)
                    wb = open_workbook(file_contents=data)
                    sheet = wb.sheet_by_index(0)

                    for row_no in range(sheet.nrows):
                        if row_no > 0:
                            line = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(
                                row.value), sheet.row(row_no)))
                            if line[0].strip():
                                brand_name_id = self.env['brand.name'].search(
                                    [('name', '=', line[0].strip())])
                                if not brand_name_id:
                                    brand_name_id = self.env['brand.name'].create({
                                        'name': line[0].strip(),
                                        'tiep_dau_ngu': line[1].strip() if line[1] else False
                                    })
                                else:
                                    if line[1]:
                                        brand_name_id.tiep_dau_ngu = line[1].strip()
                elif record.update_partner:
                    data = base64.b64decode(record.import_data)
                    wb = open_workbook(file_contents=data)
                    sheet = wb.sheet_by_index(0)

                    for row_no in range(sheet.nrows):
                        if row_no == 0:
                            continue
                        row = (
                            map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(
                                row.value),
                                sheet.row(row_no)))
                        partner_id = self.env['res.partner'].search(
                            ['|', ('name', '=', row[1]), ('name', '=', row[1].strip())])
                        if partner_id:
                            group_partner_1 = False
                            group_partner_2 = False
                            if row[4]:
                                group_partner_1 = self.env['partner.group.hk1'].search([('name', '=', row[4].strip())])
                                if not group_partner_1:
                                    group_partner_1 = self.env['partner.group.hk1'].create({
                                        'name': row[4].strip()
                                    })
                            if row[5]:
                                group_partner_2 = self.env['partner.group.hk2'].search([('name', '=', row[5].strip())])
                                if not group_partner_2:
                                    group_partner_2 = self.env['partner.group.hk2'].create({
                                        'name': row[5].strip()
                                    })
                            for partner in partner_id:
                                if group_partner_1:
                                    partner.group_kh1_id = group_partner_1
                                if group_partner_2:
                                    partner.group_kh2_id = group_partner_2
                        else:
                            print
                            "Khach hang khong tim thay: %s" % (row[1])
                else:
                    if not record.update_group_sale:
                        data = base64.b64decode(record.import_data)
                        wb = open_workbook(file_contents=data)
                        sheet = wb.sheet_by_index(0)

                        for row_no in range(sheet.nrows):
                            if record.import_by_cron:
                                if row_no < record.row_next:
                                    continue
                                if row_no - record.row_next == 120:
                                    record.row_next = row_no
                                    break
                                if record.row_next >= len(range(sheet.nrows)) - 1:
                                    record.send_mail_when_done_import()
                                    record.import_by_cron = False
                                    break
                            else:
                                if row_no == 0:
                                    continue
                            row = (
                                map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(
                                    row.value),
                                    sheet.row(row_no)))

                            product_model = self.env['product.template']
                            uom_model = self.env['product.uom']

                            default_code = row[0].strip()
                            barcode = row[1].strip()
                            name = row[2].strip()
                            uom_name = row[3].strip()
                            uom_id = uom_model.search([('name', '=', uom_name)], limit=1).id
                            purchase_code = row[4].strip()
                            brand = row[5].strip()
                            if brand:
                                brand = self.env['brand.name'].search([('name', '=', brand)], limit=1).id
                                if not brand:
                                    brand = self.env['brand.name'].create({
                                        'name': brand,
                                    }).id
                            source = row[6].strip()
                            if source:
                                source = self.env['source.name'].search([('name', '=', source)], limit=1).id
                                if not source:
                                    source = self.env['source.name'].create({
                                        'name': source,
                                    }).id
                            made_in = ''
                            listed_price = row[7].strip() and float(row[7].strip()) or 0
                            standard_price = row[8].strip() and float(row[8].strip()) or 0
                            group_product = row[9].strip()
                            group_id = False
                            if group_product:
                                group_id = self.env['product.group'].search([('name', '=', group_product)], limit=1).id
                                if not group_id:
                                    group_id = self.env['product.group'].create({
                                        'name': group_product,
                                    }).id
                                    print
                                    "Create group: %s" % (group_product,)
                            group_sale = row[10].strip()
                            group_sale_id = False
                            if group_sale:
                                group_sale_id = self.env['product.group.sale'].search([('name', '=', group_sale)],
                                                                                      limit=1).id
                                if not group_sale_id:
                                    group_sale_id = self.env['product.group.sale'].create({
                                        'name': group_sale,
                                    }).id
                                    print
                                    "Create group sale: %s" % (group_sale_id,)
                            if default_code:
                                product_id = product_model.search([('default_code', '=', default_code)])
                                productinf = {
                                    'name': name,
                                    'default_code': default_code,
                                    'list_price': listed_price,
                                    'standard_price': standard_price,
                                    'purchase_code': purchase_code,
                                    'brand_name_select': brand if brand else False,
                                    'source_select': source if source else False,
                                    'group_id': group_id,
                                    'group_sale_id': group_sale_id,
                                    'invoice_policy': 'delivery',
                                }
                                if uom_id:
                                    productinf.update({
                                        'uom_id': uom_id,
                                        'uom_po_id': uom_id,
                                    })
                                if barcode:
                                    productinf.update({
                                        'barcode': barcode,
                                    })
                                if product_id:
                                    if not record.update_product:
                                        continue
                                    else:
                                        product_id.write(productinf)
                                        print
                                        "Update-----: %s" % (row_no + 1,)
                                        continue
                                product = product_model.create(productinf)
                                if not product.barcode:
                                    barcode = self.env['ir.sequence'].next_by_code('product.template.barcode') or '/'
                                    product.barcode = barcode
                                print
                                "Row---------------------------: %s" % (row_no + 1,)
                            else:
                                print
                                "Row+++++++++++++++++++++++++++: %s" % (row_no + 1,)
                    else:
                        data = base64.b64decode(record.import_data)
                        wb = open_workbook(file_contents=data)
                        sheet = wb.sheet_by_index(0)

                        for row_no in range(sheet.nrows):
                            if row_no == 0:
                                continue
                            line = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(
                                row.value), sheet.row(row_no)))
                            if line[1] and line[0]:
                                product_id = self.env['product.template'].search(
                                    [('default_code', '=', line[0].strip())])
                                product_group_sale_id = self.env['product.group.sale'].search(
                                    [('name', '=', line[1].strip())])
                                if not product_group_sale_id:
                                    product_group_sale_id = self.env['product.group.sale'].create({
                                        'name': line[1].strip()
                                    })
                                    print
                                    "-----Tao nhom sp sale: %s" % (line[1])
                                if product_id and product_group_sale_id:
                                    product_id.group_sale_id = product_group_sale_id
                                if not product_id:
                                    print
                                    "Khong tim thay sp: %s - %s" % (line[0], row_no)

            else:
                product_template_ids = self.env['product.template'].search([]).filtered(
                    lambda pr: pr.barcode and '.0' in pr.barcode)
                for product_id in product_template_ids:
                    product_id.barcode = product_id.barcode.split('.0')[0]
