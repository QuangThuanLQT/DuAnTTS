# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.tools.float_utils import float_is_zero, float_compare
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import StringIO
import xlsxwriter
import base64
from odoo.exceptions import UserError

class purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'

    tax_sub = fields.Integer(string="Tax")
    sequence = fields.Integer(string='Sequence', default=False, readonly=True)
    price_unit = fields.Float(digits=(16, 2))
    product_qty = fields.Float(digits=(16, 2))
    qty_invoiced = fields.Float(digits=(16, 2))
    qty_received = fields.Float(digits=(16, 2))
    price_discount = fields.Monetary(digits=(16, 2))
    price_subtotal = fields.Monetary(digits=(16, 2))
    cost_root = fields.Float(digits=(16, 0))
    brand_name = fields.Char('Trademark')
    group_sale_id = fields.Many2one('product.group.sale', string="Group Product Sale")
    final_price = fields.Float(string="Price Unit", compute='_compute_price')
    product_default_code = fields.Char(string="Product Default Code", related="product_id.default_code")
    delivery_count = fields.Integer(compute="_get_delivery_count")
    order_partner_id = fields.Many2one(related='order_id.partner_id', store=True, string='Vendor')

    last_price_unit =  fields.Float(string='Giá in ra phiếu', digits=(16, 2), compute='_get_last_price_unit')

    @api.depends('product_qty', 'price_subtotal')
    def _get_last_price_unit(self):
        for record in self:
            if record.price_subtotal and record.product_qty:
                record.last_price_unit = record.price_subtotal / record.product_qty

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        product_code_multi = False
        count = False
        index = False
        for do in domain:
            if 'product_id' in do and 'ilike' in do:
                product_code_multi = do[2]
        if product_code_multi and len(product_code_multi.split()) > 1 and all(
                        len(default_code) > 6 for default_code in product_code_multi.split()):
            count_condition = 0
            list_condition = []
            list = []
            check = False
            for do in domain:
                if product_code_multi in do:
                    if not index:
                        index = domain.index(do)
                    do[2] = product_code_multi.split()[0]
                    count_condition += 1
                    list_condition.append([do[0], do[1]])
            for do in reversed(domain):
                if not product_code_multi.split()[0] in do:
                    if not check:
                        list.append(do)
                        domain.remove(do)
                else:
                    check = True
            # if index:
            #     domain_or = []
            for i in range(1, len(product_code_multi.split())):
                domain.insert(index, unicode('|'))
            # args += domain_or
            for i in range(1, len(product_code_multi.split())):
                domain_add = []
                for k in range(1, count_condition):
                    domain_add.append(unicode('|'))
                for condition in list_condition:
                    cont = condition + [product_code_multi.split()[i]]
                    domain_add.append(cont)
                domain += domain_add
            domain += list
        res = super(purchase_order_line, self).read_group(domain, fields, groupby, offset=offset, limit=limit,
                                                      orderby=orderby, lazy=lazy)
        if 'order_id' in groupby:
            for line in res:
                self.env.cr.execute(
                    "select po.date_order,rp.name from purchase_order as po left join res_partner as rp ON po.partner_id = rp.id where po.id = %s" % (
                    line.get('order_id', False)[0]))
                res_trans = self.env.cr.fetchall()
                line.update({
                    'date_order': res_trans[0][0],
                    'partner_id': res_trans[0][1]
                })
        return res

    def _get_delivery_count(self):
        for record in self:
            if record.order_id.picking_count:
                record.delivery_count = record.order_id.picking_count

    @api.depends('product_qty', 'price_unit', 'taxes_id')
    def _compute_amount(self):
        return True

        # for line in self:
        #     taxes = line.taxes_id.compute_all(line.price_unit, line.order_id.currency_id, line.product_qty,
        #                                       product=line.product_id, partner=line.order_id.partner_id)
        #     line.update({
        #         'price_tax': taxes['total_included'] - taxes['total_excluded'],
        #         'price_total': taxes['total_included'],
        #         'price_subtotal': taxes['total_excluded'],
        #     })


    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        product_code_multi = False
        count = False
        index = False
        for do in domain:
            if 'product_id' in do and 'ilike' in do:
                product_code_multi = do[2]
        if product_code_multi and len(product_code_multi.split()) > 1 and all(
                        len(default_code) > 6 for default_code in product_code_multi.split()):
            count_condition = 0
            list_condition = []
            list = []
            check = False
            for do in domain:
                if product_code_multi in do:
                    if not index:
                        index = domain.index(do)
                    do[2] = product_code_multi.split()[0]
                    count_condition += 1
                    list_condition.append([do[0], do[1]])
            for do in reversed(domain):
                if not product_code_multi.split()[0] in do:
                    if not check:
                        list.append(do)
                        domain.remove(do)
                else:
                    check = True
            # if index:
            #     domain_or = []
            for i in range(1, len(product_code_multi.split())):
                domain.insert(index, unicode('|'))
            # args += domain_or
            for i in range(1, len(product_code_multi.split())):
                domain_add = []
                for k in range(1, count_condition):
                    domain_add.append(unicode('|'))
                for condition in list_condition:
                    cont = condition + [product_code_multi.split()[i]]
                    domain_add.append(cont)
                domain += domain_add
            domain += list
        if self.env.context.get('summaries', False):
            if 'purchase_order_return' not in fields:
                fields.append('purchase_order_return')
            res = super(purchase_order_line, self).search_read(domain=domain, fields=fields, offset=offset,
                                                               limit=limit, order=order)

            def convertQty(x):
                if x.get('purchase_order_return', False):
                    x['product_qty'] = -x['product_qty']
                    x['price_subtotal'] = -x['price_subtotal']
                return x
            res = map(lambda x: convertQty(x), res)
            return res
        return super(purchase_order_line, self).search_read(domain=domain, fields=fields, offset=offset,
                                                               limit=limit, order=order)



    @api.multi
    def _get_stock_move_price_unit(self):
        self.ensure_one()
        line = self[0]
        order = line.order_id
        price_unit = line.price_discount or line.price_unit * (1 - (line.discount or 0.0) / 100.0)
        if line.taxes_id:
            price_unit = line.taxes_id.with_context(round=False).compute_all(
                price_unit, currency=line.order_id.currency_id, quantity=1.0, product=line.product_id,
                partner=line.order_id.partner_id
            )['total_excluded']
        if line.product_uom.id != line.product_id.uom_id.id:
            price_unit *= line.product_uom.factor / line.product_id.uom_id.factor
        if order.currency_id != order.company_id.currency_id:
            price_unit = order.currency_id.compute(price_unit, order.company_id.currency_id, round=False)
        return price_unit

    @api.multi
    def _compute_price(self):
        for record in self:
            final_price = record.price_unit
            if record.price_discount:
                final_price = record.price_discount
            elif record.discount:
                final_price = (1 - record.discount / 100) * final_price
            record.final_price = final_price

    @api.onchange('tax_sub')
    def onchange_tax_sub(self):
        for record in self:
            tax_id = self.env['account.tax'].search(
                [('type_tax_use', '=', 'purchase'), ('amount', '=', float(record.tax_sub))], limit=1)
            if tax_id:
                record.taxes_id = [(6, 0, tax_id.ids)]
            else:
                tax_id = self.env['account.tax'].search(
                    [('type_tax_use', '=', 'purchase'), ('amount', '=', 0)], limit=1)
                record.taxes_id = [(6, 0, tax_id.ids)]
                record.tax_sub = 0

    @api.multi
    def check_supplier_price(self, price):
        supplierinfo_model = self.env['product.supplierinfo']
        for record in self:
            order = record.order_id or False
            if order and order.id:
                if order.partner_id and order.partner_id.id:
                    seller_price = supplierinfo_model.search([
                        ('name', '=', order.partner_id.id),
                        ('product_id', '=', record.product_id.id),
                    ], limit=1)
                    if seller_price and seller_price.id:
                        seller_price.price = price
                    else:
                        sellerinfor = {
                            'name': order.partner_id.id,
                            'price': price,
                            'product_tmpl_id': record.product_id.product_tmpl_id.id,
                            'product_id': record.product_id.id
                        }
                        supplierinfo_model.create(sellerinfor)

    @api.onchange('product_id')
    def onchange_product_id(self):
        result = super(purchase_order_line, self).onchange_product_id()
        for record in self:
            if record.order_id.tax_id and record.order_id.tax_id.id:
                record.tax_sub  = int(record.order_id.tax_id.amount)
                record.taxes_id = record.order_id.tax_id
        self.brand_name = self.product_id.brand_name
        self.group_sale_id = self.product_id.group_sale_id

        return result

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.order_id.state != 'purchase':
            result = {}
            if not self.product_id:
                return result

            # Reset date, price and quantity since _onchange_quantity will provide default values
            self.date_planned = self.order_id.date_order or datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            self.price_unit = self.product_id.standard_price if self.product_id.standard_price else 1
            self.product_qty = 0.0
            self.product_uom = self.product_id.uom_po_id or self.product_id.uom_id
            result['domain'] = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}

            product_lang = self.product_id.with_context(
                lang=self.partner_id.lang,
                partner_id=self.partner_id.id,
            )
            self.name = product_lang.display_name
            if product_lang.description_purchase:
                self.name += '\n' + product_lang.description_purchase

            fpos = self.order_id.fiscal_position_id
            if self.env.uid == SUPERUSER_ID:
                company_id = self.env.user.company_id.id
                self.taxes_id = fpos.map_tax(
                    self.product_id.supplier_taxes_id.filtered(lambda r: r.company_id.id == company_id))
            else:
                self.taxes_id = fpos.map_tax(self.product_id.supplier_taxes_id)

            if self.order_id.tax_id and self.order_id.tax_id.id:
                self.tax_sub  = int(self.order_id.tax_id.amount)
                self.taxes_id = self.order_id.tax_id

            self._suggest_quantity()
            self._onchange_quantity()

            return result
        else:
            self.name = self.product_id.name
            if self.product_id.description_sale:
                self.name += '\n' + self.product_id.description_sale

    # @api.multi
    # def update_stock_move(self):
    #     for record in self:
    #         record.move_ids.update_stock_quant()

    @api.model
    def create(self, values):
        result = super(purchase_order_line, self).create(values)
        if values.get('price_unit', False) and values.get('price_unit') > 0:
            result.check_supplier_price(values.get('price_unit'))
        return result

    @api.multi
    def write(self, values):
        result = super(purchase_order_line, self).write(values)
        if values.get('price_unit', False) and values.get('price_unit') > 0:
            self.check_supplier_price(values.get('price_unit'))
        # self.update_stock_move()
        return result

    @api.multi
    def print_excel_report(self, data, response):
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Sheet 1')

        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 15)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 50)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 15)
        worksheet.set_column('G:G', 15)
        worksheet.set_column('H:H', 25)

        header_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter'})
        header_bold_color.set_text_wrap(1)
        body_bold_color = workbook.add_format(
            {'bold': False, 'font_size': '14', 'align': 'left', 'valign': 'vcenter'})
        # body_bold_color_number = workbook.add_format({'bold': False, 'font_size': '14', 'align': 'right', 'valign': 'vcenter'})
        # body_bold_color_number.set_num_format('#,##0')
        row = 0
        summary_header = ['STT','Tham chiếu đơn hàng', 'Ngày đặt hàng', 'Mã Nội Bộ', 'Miêu tả', 'Giá in ra phiếu', 'Số lượng', 'Đơn vị tính','Thành tiền']

        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]
        domain = [('state','not in',('draft','sent','cancel')),('purchase_order_return', '=', False)]
        for key,val in data.items():
            if val and key == 'partner_id':
                partner_domain = val.split(',')
                partner_domain[2] = [int(partner_domain[2])]
                domain.append(tuple(partner_domain))
            elif val and key in ('product_qty','price_unit','discount','price_discount','price_discount','tax_sub','qty_received','qty_invoiced','price_subtotal'):
                select_domain = val.split(',')
                select_domain[2] = int(select_domain[2])
                domain.append(tuple(select_domain))
            elif val and key == 'start_date':
                domain.append(('date_planned','>=',datetime.strptime(val,'%d/%m/%Y').strftime(DEFAULT_SERVER_DATETIME_FORMAT)))
            elif val and key == 'end_date':
                domain.append(('date_planned', '<=', datetime.strptime(val,'%d/%m/%Y').strftime(DEFAULT_SERVER_DATETIME_FORMAT)))

        po_lines = self.env['purchase.order.line'].search(domain)
        for line in po_lines:
            row += 1
            worksheet.write(row, 0, row or '')
            worksheet.write(row, 1, line.order_id.name or '')
            worksheet.write(row, 2,
                            line.date_order and datetime.strptime(line.date_order, DEFAULT_SERVER_DATETIME_FORMAT).strftime('%d/%m/%Y') or '')
            worksheet.write(row, 3, line.product_default_code or '')
            worksheet.write(row, 4, line.name or '')
            worksheet.write(row, 5, line.last_price_unit or '')
            worksheet.write(row, 6, line.product_qty)
            worksheet.write(row, 7, line.product_uom.name or '')
            worksheet.write(row, 8, line.price_subtotal)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
        # result = base64.b64encode(output.read())
        # attachment_obj = self.env['ir.attachment']
        # attachment_id = attachment_obj.create({
        #     'name': 'San Pham Da Mua.xls',
        #     'datas_fname': 'San Pham Da Mua.xlsx',
        #     'datas': result
        # })
        # download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        # base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        # return {
        #     'type': 'ir.actions.act_url',
        #     'url': str(base_url) + str(download_url),
        # }

# class stock_move(models.Model):
#     _inherit = 'stock.move'
#
#     @api.multi
#     def update_stock_quant(self):
#         for record in self:
#             record.quant_ids.write({
#                 'cost': record.purchase_line_id.price_unit,
#                 'qty': record.purchase_line_id.product_qty,
#                 'product_id': record.purchase_line_id.product_id.id,
#             })