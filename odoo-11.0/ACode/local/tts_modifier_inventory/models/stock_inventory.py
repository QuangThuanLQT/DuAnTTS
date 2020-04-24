# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
import base64
import StringIO
import xlsxwriter
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from xlrd import open_workbook
from odoo.exceptions import UserError

class stock_inventory(models.Model):
    _inherit = 'stock.inventory'

    category_ids = fields.Many2many(
        'product.category', string='Inventoried Category',
        readonly=True, states={'draft': [('readonly', False)]},
        help="Specify Product Category to focus your inventory on a particular Category.")
    progress_date = fields.Datetime('In Progress Date', readonly=True)
    validate_date = fields.Datetime('Validate Date', readonly=True)
    progress_user = fields.Many2one('res.users', 'In Progress Person', readonly=True)
    validate_user = fields.Many2one('res.users', 'Validate Person', readonly=True)
    total_product = fields.Float('Total Product', compute='_compute_total', store=True, digits=(16, 0))
    theoretical_total = fields.Float('Theoretical Total', compute='_compute_total', store=True, digits=(16, 0))
    real_total = fields.Float('Real Total', compute='_compute_total', store=True, digits=(16, 0))
    diff_total = fields.Float('Different Total', compute='_compute_total', store=True, digits=(16, 0))

    def _get_datetime_utc(self, datetime_val):
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        resuft = datetime.strptime(datetime_val, DEFAULT_SERVER_DATETIME_FORMAT)
        resuft = pytz.utc.localize(resuft).astimezone(user_tz).strftime(
            '%d/%m/%Y %H:%M')
        return resuft

    @api.multi
    def unlink(self):
        for rec in self:
            if(rec.env.user.has_group('tts_modifier_access_right.group_ketoan_tonghop') or rec.env.user.has_group('tts_modifier_access_right.group_ketoan_kho')):
                if rec.state == 'draft':
                    return super(stock_inventory, self).unlink()
                else:
                    raise UserError(_('Cannot delete Inventory(s) which are not draft.'))
            else:
                return super(stock_inventory, self).unlink()

    @api.depends('line_ids.product_qty', 'line_ids.theoretical_qty', 'line_ids.diff_qty',)
    def _compute_total(self):
        for record in self:
            theoretical_total = real_total = diff_total = 0.0
            for line in record.line_ids:
                theoretical_total += line.theoretical_qty
                real_total += line.product_qty
                diff_total += line.diff_qty
            record.update({
                'total_product': len(record.line_ids),
                'theoretical_total': theoretical_total,
                'real_total': real_total,
                'diff_total': diff_total

            })

    @api.multi
    def button_dummy(self):
        theoretical_total = real_total = diff_total = 0.0
        for line in self.line_ids:
            if not line.product_id:
                theoretical_qty = 0
            else:
                theoretical_qty = sum([x.qty for x in line._get_quants()])
                if theoretical_qty and line.product_uom_id and line.product_id.uom_id != line.product_uom_id:
                    theoretical_qty = line.product_id.uom_id._compute_quantity(theoretical_qty, line.product_uom_id)
            diff_qty = line.product_qty - theoretical_qty
            theoretical_total += theoretical_qty
            real_total += line.product_qty
            diff_total += diff_qty
            line.update({
                'theoretical_qty': theoretical_qty,
                'diff_qty': diff_qty
            })
        self.update({
            'total_product': len(self.line_ids),
            'theoretical_total': theoretical_total,
            'real_total': real_total,
            'diff_total': diff_total
        })

    # @api.multi
    # def write(self, vals):
    #     res = super(stock_inventory, self).write(vals)
    #     if not 'button_dummy_create' in self._context and not 'button_dummy_write' in self._context:
    #         self.with_context(button_dummy_write=True).button_dummy()
    #     return res

    @api.onchange('filter')
    def onchange_filter(self):
        res = super(stock_inventory, self).onchange_filter()
        if self.filter != 'multi_category':
            self.category_ids = False
        return res

    @api.model
    def _selection_filter(self):
        """ Get the list of filter allowed according to the options checked
        in 'Settings\Warehouse'. """
        res_filter = [
            ('none', _('All products')),
            ('category', _('One product category')),
            ('multi_category', _('Multi product category')),
            ('product', _('One product only')),
            ('partial', _('Select products manually'))]

        if self.user_has_groups('stock.group_tracking_owner'):
            res_filter += [('owner', _('One owner only')), ('product_owner', _('One product for a specific owner'))]
        if self.user_has_groups('stock.group_production_lot'):
            res_filter.append(('lot', _('One Lot/Serial Number')))
        if self.user_has_groups('stock.group_tracking_lot'):
            res_filter.append(('pack', _('A Pack')))
        return res_filter

    @api.multi
    def _get_inventory_lines_values(self):
        # TDE CLEANME: is sql really necessary ? I don't think so
        locations = self.env['stock.location'].search([('id', 'child_of', [self.location_id.id])])
        domain = ' location_id in %s'
        args = (tuple(locations.ids),)

        vals = []
        Product = self.env['product.product']
        # Empty recordset of products available in stock_quants
        quant_products = self.env['product.product']
        # Empty recordset of products to filter
        products_to_filter = self.env['product.product']

        # case 0: Filter on company
        if self.company_id:
            domain += ' AND company_id = %s'
            args += (self.company_id.id,)

        # case 1: Filter on One owner only or One product for a specific owner
        if self.partner_id:
            domain += ' AND owner_id = %s'
            args += (self.partner_id.id,)
        # case 2: Filter on One Lot/Serial Number
        if self.lot_id:
            domain += ' AND lot_id = %s'
            args += (self.lot_id.id,)
        # case 3: Filter on One product
        if self.product_id:
            domain += ' AND product_id = %s'
            args += (self.product_id.id,)
            products_to_filter |= self.product_id
        # case 4: Filter on A Pack
        if self.package_id:
            domain += ' AND package_id = %s'
            args += (self.package_id.id,)
        # case 5: Filter on One product category + Exahausted Products
        if self.category_id:
            categ_products = Product.search([('categ_id', '=', self.category_id.id)])
            domain += ' AND product_id = ANY (%s)'
            args += (categ_products.ids,)
            products_to_filter |= categ_products

        if self.category_ids:
            categ_products = Product.search([('categ_id', 'in', self.category_ids.ids)])
            domain += ' AND product_id = ANY (%s)'
            args += (categ_products.ids,)
            products_to_filter |= categ_products

        self.env.cr.execute("""SELECT product_id, sum(qty) as product_qty, location_id, lot_id as prod_lot_id, package_id, owner_id as partner_id
                FROM stock_quant
                WHERE %s
                GROUP BY product_id, location_id, lot_id, package_id, partner_id """ % domain, args)

        for product_data in self.env.cr.dictfetchall():
            # replace the None the dictionary by False, because falsy values are tested later on
            for void_field in [item[0] for item in product_data.items() if item[1] is None]:
                product_data[void_field] = False
            product_data['theoretical_qty'] = product_data['product_qty']
            if product_data['product_id']:
                product_data['product_uom_id'] = Product.browse(product_data['product_id']).uom_id.id
                quant_products |= Product.browse(product_data['product_id'])
            vals.append(product_data)
        if self.exhausted:
            exhausted_vals = self._get_exhausted_inventory_line(products_to_filter, quant_products)
            vals.extend(exhausted_vals)
        return vals

    @api.multi
    def prepare_inventory(self):
        res = super(stock_inventory, self).prepare_inventory()
        self.progress_date = datetime.now()
        self.progress_user = self.env.uid
        return res

    @api.multi
    def action_done(self):
        res = super(stock_inventory, self).action_done()
        self.validate_date = datetime.now()
        self.validate_user = self.env.uid
        return res

    @api.multi
    def import_data_excel(self):
        for record in self:
            if record.import_data:
                data = base64.b64decode(record.import_data)
                wb = open_workbook(file_contents=data)
                sheet = wb.sheet_by_index(0)

                line_ids = record.line_ids.browse([])

                for row_no in range(sheet.nrows):
                    if row_no < 1:
                        continue
                    row = (
                    map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value),
                        sheet.row(row_no)))
                    if len(row) >= 2:
                        data = {
                            'product_qty': int(float(row[1])) if row[1]!="" else 0,
                            'location_id': record.location_id and record.location_id.id or False,
                        }
                        product = self.env['product.product'].search([
                            '|', ('default_code', '=', row[0].strip()),
                            ('barcode', '=', row[0].strip())
                        ], limit=1)
                        if product and product.id:
                            data['product_id'] = product.id
                            line_ids += record.line_ids.new(data)
                record.line_ids = line_ids

    @api.model
    def export_overview(self, response):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        product_ids = self.env['stock.inventory'].search(domain)
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Inventory Overview')

        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')

        worksheet.set_column('A:O', 20)

        summary_header = ['Inventory Reference', 'Inventoried Location', 'Inventory Date', 'Created Person', 'In Progress Date',
                          'In Progress Person', 'Validated Date',
                          'Validated Person', 'Total Products', 'Theoretical Total', 'Real Tota', 'Different Total']
        row = 0
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for product_id in product_ids:
            row += 1

            date = ''
            if product_id.date:
                date = self._get_datetime_utc(product_id.date)

            validate_date = ''
            if product_id.validate_date:
                validate_date = self._get_datetime_utc(product_id.validate_date)

            progress_date = ''
            if product_id.progress_date:
                progress_date = self._get_datetime_utc(product_id.progress_date)

            worksheet.write(row, 0, product_id.name, text_style)
            worksheet.write(row, 1, product_id.location_id.display_name or '', text_style)
            worksheet.write(row, 2, date, text_style)
            worksheet.write(row, 3, product_id.create_uid.name, text_style)
            worksheet.write(row, 4, progress_date or '', text_style)
            worksheet.write(row, 5, product_id.progress_user.name or '', text_style)
            worksheet.write(row, 6, validate_date or '', text_style)
            worksheet.write(row, 7, product_id.validate_user.name or '', text_style)
            worksheet.write(row, 8, product_id.total_product, body_bold_color_number)
            worksheet.write(row, 9, product_id.theoretical_total, body_bold_color_number)
            worksheet.write(row, 10, product_id.real_total, body_bold_color_number)
            worksheet.write(row, 11, product_id.diff_total, body_bold_color_number)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()


    api.model
    def export_detail(self, response):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        inventory_ids = self.env['stock.inventory'].search(domain)
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Inventory Detail')

        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')

        worksheet.set_column('A:O', 20)

        summary_header = ['Inventory Reference', 'Inventoried Location', 'Inventory Date', 'Default Code',
                          'Product Name', 'Theoretical Quantity', 'Real Quantity', 'Different Quantity']
        row = 0
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for inventory_id in inventory_ids:
            for product_id in inventory_id.line_ids:
                row += 1
                date = ''
                if inventory_id.date:
                    date = self._get_datetime_utc(inventory_id.date)

                worksheet.write(row, 0, inventory_id.name, text_style)
                worksheet.write(row, 1, inventory_id.location_id.display_name or '', text_style)
                worksheet.write(row, 2, date, text_style)
                worksheet.write(row, 3, product_id.product_id.default_code or '', text_style)
                worksheet.write(row, 4, product_id.product_id.display_name or '', text_style)
                worksheet.write(row, 5, product_id.theoretical_qty, body_bold_color_number)
                worksheet.write(row, 6, product_id.product_qty, body_bold_color_number)
                worksheet.write(row, 7, product_id.diff_qty, body_bold_color_number)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def export_excel(self):
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('%s' % (self.name))


        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 40)
        worksheet.set_column('C:C', 25)
        worksheet.set_column('D:D', 10)
        worksheet.set_column('E:E', 10)
        worksheet.set_column('F:F', 15)

        header_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'center', 'valign': 'vcenter'})
        header_bold_color.set_text_wrap(1)
        body_bold_color = workbook.add_format({'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        # body_bold_color_number = workbook.add_format({'bold': False, 'font_size': '14', 'align': 'right', 'valign': 'vcenter'})
        # body_bold_color_number.set_num_format('#,##0')
        row = 0
        summary_header = ['Mã nội bộ', 'Sản phẩm', 'Số lượng lý thuyết', 'Số lượng thực tế']

        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for line in self.line_ids:
            variants = [line.product_id.name]
            for attr in line.product_id.attribute_value_ids:
                if attr.attribute_id.name in ('Size', 'size'):
                    variants.append(('Size ' + attr.name))
                else:
                    variants.append((attr.name))
            product_name = ' - '.join(variants)
            row += 1
            worksheet.write(row, 0, line.product_id.default_code or '')
            worksheet.write(row, 1, product_name)
            worksheet.write(row, 2, line.product_qty)
            worksheet.write(row, 3, '')

        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create({
            'name': '%s.xlsx' % (self.name),
            'datas_fname': '%s.xlsx' % (self.name),
            'datas': result
        })
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        return {
            'type': 'ir.actions.act_url',
            'url': str(download_url),
        }


class stock_inventory_line(models.Model):
    _inherit = 'stock.inventory.line'
    _order = "product_id"

    diff_qty = fields.Float('Different Total', compute='_compute_diff_qty', store=True)

    @api.depends('product_qty', 'theoretical_qty')
    def _compute_diff_qty(self):
        for record in self:
            diff_qty = record.product_qty - record.theoretical_qty
            record.diff_qty = diff_qty
