# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp

class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    final_price = fields.Float(string="Price Unit", compute='_compute_price')
    cost_root = fields.Float(compute='_get_cost_root', string="Cost Medium")
    tax_sub = fields.Integer(string="Tax")
    sequence = fields.Integer(string='Sequence', default=False, readonly=True)
    date_order = fields.Datetime(string='Ngày Đặt Hàng')
    product_uom_qty = fields.Float(digits=(16,2))
    qty_to_invoice = fields.Float(digits=(16,2))
    qty_invoiced = fields.Float(digits=(16,2))
    qty_delivered = fields.Float(digits=(16,2))
    product_qty = fields.Float(digits=(16,2))
    discount = fields.Float(digits=(16,2))
    price_unit = fields.Float(digits=(16,2))
    price_subtotal = fields.Monetary(digits=(16,2))
    price_discount = fields.Monetary(digits=(16,2))
    brand_name = fields.Char('Trademark')
    group_sale_id = fields.Many2one('product.group.sale', string="Group Product Sale")
    product_default_code = fields.Char(string="Product Default Code",related="product_id.default_code")
    price_unit = fields.Float('Unit Price', required=True, digits=dp.get_precision('Product Price'), default=1.0)
    price_unit_sub = fields.Float('Unit Price', readonly=True, digits=dp.get_precision('Product Price'), related="price_unit")
    delivery_count = fields.Integer(compute="_get_delivery_count")

    last_price_unit = fields.Float('Giá in ra phiếu', compute='_get_last_price_unit', digits=dp.get_precision('Product Price'))

    @api.depends('invoice_lines.invoice_id.state', 'invoice_lines.quantity')
    def _get_invoice_qty(self):
        if not self.env.context.get('no_qty_invoiced', False):
            super(sale_order_line, self)._get_invoice_qty()
        else:
            pass

    @api.multi
    def write(self, values):
        result = super(sale_order_line, self).write(values)
        return result

    @api.depends('product_uom_qty', 'price_subtotal')
    def _get_last_price_unit(self):
        for record in self:
            if record.price_subtotal and record.product_uom_qty:
                record.last_price_unit = record.price_subtotal / record.product_uom_qty



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
        res = super(sale_order_line, self).read_group(domain, fields, groupby, offset=offset, limit=limit,
                                                      orderby=orderby, lazy=lazy)
        if 'order_id' in groupby:
            for line in res:
                self.env.cr.execute("select so.date_order,rp.name from sale_order as so left join res_partner as rp ON so.partner_id = rp.id where so.id = %s" % (line.get('order_id',False)[0]))
                res_trans = self.env.cr.fetchall()
                line.update({
                    'date_order' : res_trans[0][0],
                    'order_partner_id': res_trans[0][1]
                })
        return res

    def _get_delivery_count(self):
        for record in self:
            if record.order_id.delivery_count:
                record.delivery_count = record.order_id.delivery_count

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if 'sale_order_return' not in fields:
            fields.append('sale_order_return')
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
        # for i in range(0, len(domain)):
        #     if 'barcode' in domain[i] and 'ilike' in domain[i]:
        #         barcode = domain[i][2]
        #         product_ids = self.search([('barcode', '=', barcode)]).id or [] + self.env['product.barcode'].search(
        #             [('name', '=', barcode)]).product_id.ids or []
        #         domain[i] = ['id', 'in', product_ids]
        res = super(sale_order_line, self).search_read(domain=domain, fields=fields, offset=offset,
                                                      limit=limit, order=order)
        def convertQty(x):
            if x.get('sale_order_return', False):
                x['product_uom_qty'] = -x['product_uom_qty']
                x['price_subtotal'] = -x['price_subtotal']
            return x
        if self.env.context.get('summaries', False):
            res = map(lambda x: convertQty(x), res)
        return res

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        if self.order_id.state != 'sale':
            if not self.product_id:
                return {'domain': {'product_uom': []}}

            vals = {}
            domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
            if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
                vals['product_uom'] = self.product_id.uom_id
                vals['product_uom_qty'] = 1.0

            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id.id,
                quantity=vals.get('product_uom_qty') or self.product_uom_qty,
                date=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id
            )

            result = {'domain': domain}

            title = False
            message = False
            warning = {}
            if product.sale_line_warn != 'no-message':
                title = _("Warning for %s") % product.name
                message = product.sale_line_warn_msg
                warning['title'] = title
                warning['message'] = message
                result = {'warning': warning}
                if product.sale_line_warn == 'block':
                    self.product_id = False
                    return result

            name = product.name
            if product.description_sale:
                name += '\n' + product.description_sale
            vals['name'] = name
            vals['brand_name'] = product.brand_name
            vals['group_sale_id'] = product.group_sale_id and product.group_sale_id.id

            for record in self:
                if record.order_id.tax_id and record.order_id.tax_id.id:
                    record.tax_id = record.order_id.tax_id
                    record.tax_sub = int(record.order_id.tax_id.amount)

            self._compute_tax_id()

            if self.order_id.pricelist_id and self.order_id.partner_id and not self.sale_order_return:
                price_unit = self.env['account.tax']._fix_tax_included_price_company(
                    self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
                if price_unit == 0:
                    vals['price_unit'] = 1
                else:
                    vals['price_unit'] = price_unit
            self.update(vals)

            self.onchange_product_for_ck()
            return result
        else:
            self.name = self.product_id.name
            if self.product_id.description_sale:
                self.name += '\n' + self.product_id.description_sale

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        if not self.product_uom or not self.product_id:
            self.price_unit = 0.0
            return
        if self.order_id.pricelist_id and self.order_id.partner_id:
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id.id,
                quantity=self.product_uom_qty,
                date=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position')
            )
            price_unit = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product),
                                                                                      product.taxes_id, self.tax_id,
                                                                                      self.company_id)
            if not self.sale_order_return:
                self.price_unit = price_unit or 1
                if self.order_partner_id:
                    self.onchange_product_for_ck(self.order_partner_id.id)

    @api.onchange('tax_sub')
    def onchange_tax_sub(self):
        for record in self:
            tax_id = self.env['account.tax'].search([('type_tax_use','=','sale'),('amount','=',float(record.tax_sub))],limit=1)
            if tax_id:
                record.tax_id = [(6,0,tax_id.ids)]
            else:
                tax_id = self.env['account.tax'].search(
                    [('type_tax_use', '=', 'sale'), ('amount', '=', 0)],limit=1)
                record.tax_id = [(6,0,tax_id.ids)]
                record.tax_sub = 0


    # @api.onchange('price_unit')
    # def _onchange_price_unit(self):
    #     for record in self:
    #         if record.product_id and record.product_id.list_price:
    #             record.price_unit = record.product_id.list_price
    #             record.onchange_product_for_ck()

    @api.onchange('product_id', 'product_uom_qty')
    def onchange_product_uom_qty(self):
        if self.sale_order_return == True and 'sale_order_ctx' in self._context and self._context.get('sale_order_ctx'):
            sale_id = self.env['sale.order'].browse(self._context.get('sale_order_ctx')[0][2])
            if self.product_id:
                order_line = sale_id.mapped('order_line').filtered(lambda l: l.product_id.id == self.product_id.id)
                product_uom_qty = sum(order_line.mapped('product_uom_qty'))
                if self.product_uom_qty > product_uom_qty:
                    self.product_uom_qty = product_uom_qty
                    warning = {
                        'title': 'Dữ liệu không hợp lệ',
                        'message': "Số lượng không không thể lớn hơn %s." % (product_uom_qty)
                    }
                    return {'warning': warning}
                    #raise UserError(_("Số lượng không không thể lớn hơn %s." % (product_uom_qty)))


    @api.onchange('price_discount')
    def line_onchange_price_discount(self):
        if self.price_unit and self.price_discount:
            self.discount = (self.price_unit - self.price_discount) / self.price_unit * 100

    @api.onchange('product_id')
    def _get_cost_root(self):
        for record in self:
            if record.product_id:
                record.cost_root = record.product_id.cost_root

    @api.onchange('product_id', 'price_unit', 'product_uom', 'product_uom_qty', 'tax_id')
    def _onchange_discount(self):
        # self.discount = 0.0
        if not (self.product_id and self.product_uom and
                self.order_id.partner_id and self.order_id.pricelist_id and
                self.order_id.pricelist_id.discount_policy == 'without_discount' and
                self.env.user.has_group('sale.group_discount_per_so_line')):
            return


    @api.multi
    def _compute_price(self):
        for record in self:
            final_price = record.price_unit
            if record.price_discount:
                final_price = record.price_discount
            elif record.discount:
                final_price = (1 - record.discount / 100) * final_price
            record.final_price = final_price


    # @api.onchange('price_unit', 'discount')
    # def onchange_price_discount(self):
    #     for record in self:
    #         discount = (record.price_unit * record.discount) / 100
    #         record.price_discount = record.price_unit - discount

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id', 'price_discount')
    @api.onchange('product_uom_qty', 'discount', 'price_unit', 'tax_id', 'price_discount')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        # for line in self:
        #     if line.price_discount:
        #         price = line.price_discount
        #     else:
        #         price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
        #     taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
        #                                     product=line.product_id, partner=line.order_id.partner_shipping_id)
        #     line.update({
        #         'price_tax': taxes['total_included'] - taxes['total_excluded'],
        #         'price_total': taxes['total_included'],
        #         'price_subtotal': taxes['total_excluded'],
        #     })

    @api.multi
    def _prepare_invoice_line(self, qty):
        self.ensure_one()

        res = super(sale_order_line, self)._prepare_invoice_line(qty)
        if self.price_discount:
            res.update({
                'price_unit': self.price_unit,
                'price_discount' : self.price_discount,
            })
        return res

    @api.onchange('product_uom_qty', 'product_uom', 'route_id')
    def _onchange_product_id_check_availability(self):
        res = super(sale_order_line, self)._onchange_product_id_check_availability()
        if res != None and 'warning' in res:
            res = {}
        return res

    # @api.model
    # def create(self, values):
    #     result = super(sale_order_line, self).create(values)
    #     if values.get('price_unit', False) and values.get('price_unit') > 1:
    #         if values.get('product_id', False):
    #             product = self.env['product.product'].browse(values.get('product_id'))
    #             if product.lst_price <= 1:
    #                 product.write({
    #                     'lst_price': values.get('price_unit'),
    #                 })
    #     return result
    #
    # @api.multi
    # def write(self, values):
    #     result = super(sale_order_line, self).write(values)
    #     if values.get('price_unit', False) and values.get('price_unit') > 1:
    #         for record in self:
    #             if record.product_id and record.product_id.id:
    #                 product = record.product_id
    #                 if product.lst_price <= 1:
    #                     product.write({
    #                         'lst_price': values.get('price_unit'),
    #                     })
    #     return result
    # @api.model
    # def create_order_line_report(self):
    #     data = {}
    #     ids = self.env.context.get('active_ids', [])
    #     orderlines = self.browse(ids)
    #     list = []
    #     for line in orderlines:
    #         dict = {
    #             'date_order': line.date_order,
    #             'order_id': line.order_id.name,
    #             'product_id': line.product_id.default_code,
    #             'product_name': line.product_id.name,
    #             'product_uom': line.product_uom.name,
    #             'product_uom_qty': line.product_uom_qty,
    #             'price_unit': line.price_unit,
    #             'price_subtotal': line.price_subtotal,
    #         }
    #         list.append(dict)
    #
    #     datas = {
    #         'ids': self.env.context.get('active_ids', []),
    #         'doc_model': self.env.context.get('active_model'),
    #         'orderlines': list,
    #         'model': self._name,
    #         'form': list,
    #         # 'date_to': end_date
    #     }
    #     return self.env['report'].get_action(self, 'tuanhuy_sale.report_saleorder_line',data=datas)

class ReportFeeOutstanding(models.AbstractModel):
    _name = 'report.tuanhuy_sale.report_saleorder_line'


    @api.multi
    def render_html(self,docids, data=None):
        self.model=self.env.context.get('active_model')
        docs = self.env['sale.order.line'].browse(docids).sorted(key=lambda r: r.date_order, reverse=True)
        list = []
        partner_name = docs[0].order_partner_id.name
        total_amount = 0
        for line in docs:
            total_amount += line.price_subtotal
            date_order = datetime.strptime(line.date_order, DEFAULT_SERVER_DATETIME_FORMAT)
            list.append(date_order)
        date_from = min(list).strftime('%d/%m/%Y')
        date_to = max(list).strftime('%d/%m/%Y')
        docargs = {'doc_ids': self.ids,
                   'doc_model': self.model,
                   'docs': docs,
                   'date_from': date_from,
                   'date_to': date_to,
                   'partner_name': partner_name,
                   'total_amount': total_amount
                   }
        return self.env['report'].render('tuanhuy_sale.report_saleorder_line', docargs)

