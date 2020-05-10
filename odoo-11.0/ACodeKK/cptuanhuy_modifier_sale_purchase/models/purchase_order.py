# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
from dateutil.relativedelta import relativedelta
import base64
from xlrd import open_workbook
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import StringIO
import xlsxwriter

class product_product_inherit(models.Model):
    _inherit = 'product.product'

    @api.multi
    def name_get(self):
        if 'product_show_onhand' in self._context:
            return [(record.id, "[%s] - [%s] -%s" % (record.default_code,record.qty_available,record.name)) for record in self]
        else:
            if  'only_show_default_code' in self._context:
                return [(record.id, "%s" % (record.default_code)) if record.default_code else (record.id, "%s" % (record.name)) for record in self]
            else:
                return super(product_product_inherit, self).name_get()



class purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'

    sale_id = fields.Many2one('sale.order',string='Đơn hàng')

    date_order = fields.Datetime(related='order_id.date_order', string='Order Date', readonly=True, store=True)
    name_id = fields.Char(related='order_id.name', string='Order Reference', readonly=True, store=True)

    @api.depends('product_qty', 'price_unit', 'taxes_id')
    def _compute_amount(self):
        # return True

        for line in self:
            if line.price_discount:
                price = line.price_discount
                taxes_id = line.taxes_id
            else:
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                taxes_id = line.taxes_id

            taxes = taxes_id.compute_all(price, line.order_id.currency_id, line.product_qty,
                                              product=line.product_id, partner=line.order_id.partner_id)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.onchange('product_id')
    @api.depends('product_id')
    def depends_product_to_name(self):
        for rec in self:
            if rec.product_id:
                rec.name = rec.product_id.name

    @api.onchange('product_id')
    def onchange_product_id(self):
        res = super(purchase_order_line, self).onchange_product_id()
        self.name = self.product_id.name
        return res



    @api.onchange('product_id')
    def onchange_product_id(self):
        result = super(purchase_order_line, self).onchange_product_id()
        self.date_planned = self.order_id.date_planned or datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        return result


class purchase_order(models.Model):
    _inherit = 'purchase.order'

    stock_out_name    = fields.Text(string='Đơn xuất',compute='get_stock_out_name')
    date_planned = fields.Datetime(string='Scheduled Date', compute=False, store=True, index=True, default=fields.Datetime.now)
    sale_ids        = fields.Many2many('sale.order',string='Đơn hàng',compute='get_sale_ids_line')

    @api.multi
    def get_sale_ids_line(self):
        for record in self:
            record.sale_ids = record.order_line.mapped('sale_id')

    @api.multi
    def get_stock_out_name(self):
        for record in self:
            stock_out_name = ''
            if len(record.picking_ids) > 1:
                True
            if record.picking_ids:
                for picking in record.picking_ids:
                    stock_out_name += '\n'.join( stock.name + ' - ' +dict(stock._fields['state'].selection).get(stock.state) for stock in picking.stock_out_ids)
            record.stock_out_name = stock_out_name

    @api.constrains('name')
    def _check_name(self):
        for record in self:
            order = self.search([('name', '=', record.name), ('id', '!=', record.id)])
            if order:
                raise ValidationError(_("Tên của đơn hàng phải là duy nhất!"))

    @api.depends('order_line.price_total')
    def _amount_all(self):
        # return True
        for order in self:
            amount_untaxed = amount_tax = amount_discount = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                # FORWARDPORT UP TO 10.0
                if order.company_id.tax_calculation_rounding_method == 'round_globally':
                    taxes = line.taxes_id.compute_all(line.price_unit, line.order_id.currency_id, line.product_qty,
                                                      product=line.product_id, partner=line.order_id.partner_id)
                    amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                else:
                    amount_tax += line.price_tax
                if line.price_discount:
                    amount_discount += (line.product_qty * (line.price_unit - line.price_discount))
                else:
                    amount_discount += (line.product_qty * line.price_unit * line.discount) / 100
            order.update({
                'amount_untaxed': order.currency_id.round(amount_untaxed),
                'amount_tax': order.currency_id.round(amount_tax),
                'amount_discount': order.currency_id.round(amount_discount),
                'amount_total': amount_untaxed + amount_tax,
            })

    @api.multi
    def import_data_excel(self):
        for record in self:
            if record.import_data:
                data = base64.b64decode(record.import_data)
                wb = open_workbook(file_contents=data)
                sheet = wb.sheet_by_index(0)

                order_line = record.order_line.browse([])

                row_error = []
                for row_no in range(sheet.nrows):
                    if row_no > 0:
                        row = (
                        map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value),
                            sheet.row(row_no)))
                        if len(row) >= 6:
                            product = self.env['product.product'].search([
                                '|', ('default_code', '=', row[0].strip()),
                                ('barcode', '=', row[0].strip())
                            ], limit=1)
                            if not product or float(row[5]) < 0 or int(float(row[4])) < 0:
                                row_error.append({
                                    'default_code': row[0],
                                    'price': row[5],
                                    'qty': row[4],
                                })
                if row_error:
                    return {
                        'name': 'Import Warning',
                        'type': 'ir.actions.act_window',
                        'res_model': 'import.warning',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'target': 'new',
                        'context': {
                            'data': row_error,
                        }
                    }

                else:
                    for row_no in range(sheet.nrows):
                        row = (
                            map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(
                                row.value), sheet.row(row_no)))
                        if len(row) >= 6:
                            product = self.env['product.product'].search([
                                '|', ('default_code', '=', row[0].strip()),
                                ('barcode', '=', row[0].strip())
                            ], limit=1)
                            sale_id = self.env['sale.order'].sudo().search([('name', '=', row[2].strip() or '')],
                                                                           limit=1)
                            if product and product.id:
                                line_data = {
                                    'product_id': product.id,
                                    'product_uom': product.uom_id.id,
                                    'name': row[1].strip() or product.name,
                                    'price_discount': float(row[5]),
                                    'product_uom_qty': int(float(row[4])),
                                    'product_qty': int(float(row[4])),
                                    'sale_id': sale_id or False
                                }
                                line = record.order_line.new(line_data)
                                line.onchange_product_id()
                                line.product_qty = int(float(row[4]))
                                line.price_unit = float(row[5]) or product.lst_price
                                order_line += line
                    record.order_line = order_line

    def export_po_data_excel(self):
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
        summary_header = ['Mã nội bộ', 'Miêu tả', 'Đơn hàng', 'Đơn vị', 'SL đặt', 'Giá đã CK']

        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for line in self.order_line:
            row += 1
            worksheet.write(row, 0, line.product_id.default_code or '')
            worksheet.write(row, 1, line.name)
            worksheet.write(row, 2, line.sale_id and line.sale_id.name or '')
            worksheet.write(row, 3, line.product_uom.name or '')
            worksheet.write(row, 4, line.product_qty)
            worksheet.write(row, 5, line.price_discount)

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
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return {
            'type': 'ir.actions.act_url',
            'url': str(base_url) + str(download_url),
        }


