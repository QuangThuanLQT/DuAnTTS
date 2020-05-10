# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons import decimal_precision as dp


class product_product_inherit(models.Model):
    _inherit = 'product.product'

    @api.multi
    def name_get(self):
        if 'product_show_onhand' in self._context:
            return [(record.id, "[%s] - [%s] -%s" % (record.default_code, record.qty_available, record.name)) for record
                    in self]
        else:
            return super(product_product_inherit, self).name_get()

    @api.model
    def _convert_prepared_anglosaxon_line(self, line, partner):
        return {
            'date_maturity': line.get('date_maturity', False),
            'partner_id': partner,
            'name': line['name'],
            'debit': round(line['price'], 2) > 0 and round(line['price'], 2),
            'credit': round(line['price'], 2) < 0 and -round(line['price'], 2),
            'account_id': line['account_id'],
            'analytic_line_ids': line.get('analytic_line_ids', []),
            'amount_currency': round(line['price'], 2) > 0 and abs(line.get('amount_currency', False)) or -abs(
                line.get('amount_currency', False)),
            'currency_id': line.get('currency_id', False),
            'quantity': line.get('quantity', 1.00),
            'product_id': line.get('product_id', False),
            'product_uom_id': line.get('uom_id', False),
            'analytic_account_id': line.get('account_analytic_id', False),
            'invoice_id': line.get('invoice_id', False),
            'tax_ids': line.get('tax_ids', False),
            'tax_line_id': line.get('tax_line_id', False),
            'analytic_tag_ids': line.get('analytic_tag_ids', False),
        }


class product_template_inherit(models.Model):
    _inherit = 'product.template'

    cost_root = fields.Float(compute='_get_cost_root', string="Cost Medium")
    group_id = fields.Many2one('product.group', string="Group Product")
    group_sale_id = fields.Many2one('product.group.sale', string="Group Product Sale")
    qty_available_sub = fields.Float('Số Lượng Thực Tế', digits=dp.get_precision('Product Unit of Measure'))
    product_stock_move_open = fields.One2many('stock.move', 'product_tmpl_id', compute='get_product_stock_move_open')

    @api.multi
    def unlink(self):
        for record in self:
            record.barcode_ids.unlink()
            product_barcode_ids = self.env['product.barcode.generator.line'].search([('product_id', '=', record.id)])
            if product_barcode_ids:
                product_barcode_ids.unlink()
        return super(product_template_inherit, self).unlink()

    @api.multi
    def get_product_stock_move_open(self):
        for record in self:
            moves = self.env['stock.move'].search([('product_id', 'in', record.product_variant_ids.ids)])
            record.product_stock_move_open = moves

    def _compute_quantities(self):
        res = self._compute_quantities_dict()
        for template in self:
            template.qty_available = res[template.id]['qty_available']
            template.virtual_available = res[template.id]['virtual_available']
            template.incoming_qty = res[template.id]['incoming_qty']
            template.outgoing_qty = res[template.id]['outgoing_qty']
            if template.qty_available_sub != res[template.id]['qty_available']:
                template.write({'qty_available_sub': res[template.id]['qty_available']})

    @api.constrains('default_code')
    def _check_public_holiday(self):
        for rec in self:
            if rec.default_code:
                pub_holiday_ids = rec.search([('default_code', '=', rec.default_code)])
                if pub_holiday_ids and len(pub_holiday_ids) > 1:
                    raise ValidationError(_('The Internal Reference must be unique!'))

    @api.model
    def get_onhand_show(self, active_id):
        product_id = self.env['product.template'].browse(active_id)
        onhand = 0
        if product_id:
            onhand = product_id.qty_available
        return str(onhand)

    def _get_cost_root(self):
        for record in self:
            purchase_line_ids = record.env['purchase.order.line'].search(
                [('product_id.product_tmpl_id', '=', record.id), ('order_id.state', '=', 'purchase')])
            amount = 0
            qty = 0
            for line in purchase_line_ids:
                if line.order_id.picking_ids and 'done' in line.order_id.picking_ids.mapped('state'):
                    amount += line.price_discount or line.price_unit
                    qty += 1
            if amount and qty:
                record.cost_root = float(amount / qty)
            else:
                amount = record.standard_price
                qty = 1
                record.cost_root = float(amount / qty)

    @api.model
    def default_get(self, fields):
        res = super(product_template_inherit, self).default_get(fields)
        res['type'] = 'product'
        res['pack_stock_management'] = 'decrmnt_both'
        categ_id = self.env['product.category'].search([
            ('name', '=', 'Vật tư hàng hóa'),
            ('parent_id.name', '=', 'Có thể bán'),
            ('parent_id.parent_id.name', '=', 'Tất cả')
        ], limit=1).id
        if categ_id:
            res['categ_id'] = categ_id
        product_uom = self.env['product.uom'].search([
            ('name', '=', 'Cái'),
            ('category_id', '=', self.env.ref('product.product_uom_categ_unit').id),
            ('active', '=', True)
        ], limit=1)
        if product_uom:
            res['uom_id'] = product_uom.id
            res['uom_po_id'] = product_uom.id
            res['purchase_method'] = 'purchase'
        return res

    @api.model
    def create(self, values):
        result = super(product_template_inherit, self).create(values)
        product = self.env['product.template'].search([('default_code', '=', result.default_code)])
        # if product:
        #     raise UserError(_("The Internal Reference must be unique!"))
        return result

    @api.multi
    def write(self, values):
        result = super(product_template_inherit, self).write(values)
        if values.get('price_unit', False) and values.get('price_unit') > 1:
            for record in self:
                if record.product_id and record.product_id.id:
                    product = record.product_id
                    if product.lst_price <= 1:
                        product.write({
                            'lst_price': values.get('price_unit'),
                        })
        for record in self:
            ir_translation = self.env['ir.translation'].search(
                [('res_id', '=', record.id), ('name', '=', 'product.template,name')], limit=1)
            if ir_translation and ir_translation.source != record.name:
                ir_translation.source = record.name
        return result

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        for i in range(0, len(domain)):
            if 'barcode' in domain[i] and 'ilike' in domain[i]:
                barcode = domain[i][2]
                product_ids = self.search([('barcode', '=', barcode)]).ids or [] + self.env['product.barcode'].search(
                    [('name', '=', barcode)]).product_id.ids or []
                domain[i] = ['id', 'in', product_ids]

        res = super(product_template_inherit, self).search_read(domain=domain, fields=fields, offset=offset,
                                                                limit=limit, order=order)
        return res

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        product_code_multi = False
        count = False
        index = False
        for do in domain:
            if 'default_code' in do and 'ilike' in do:
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
            if index:
                domain_or = []
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
        for i in range(0, len(domain)):
            if 'barcode' in domain[i] and 'ilike' in domain[i]:
                barcode = domain[i][2]
                product_ids = self.search([('barcode', '=', barcode)]).id or [] + self.env['product.barcode'].search(
                    [('name', '=', barcode)]).product_id.ids or []
                domain[i] = ['id', 'in', product_ids]
        res = super(product_template_inherit, self).read_group(domain, fields, groupby, offset=offset, limit=limit,
                                                               orderby=orderby, lazy=lazy)
        return res

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        product_code_multi = False
        count = False
        index = False
        for do in args:
            if 'default_code' in do and 'ilike' in do:
                product_code_multi = do[2]
        if product_code_multi and len(product_code_multi.split()) > 1 and all(
                len(default_code) > 6 for default_code in product_code_multi.split()):
            count_condition = 0
            list_condition = []
            list = []
            check = False
            for domain in args:
                if product_code_multi in domain:
                    if not index:
                        index = args.index(domain)
                    domain[2] = product_code_multi.split()[0]
                    count_condition += 1
                    list_condition.append([domain[0], domain[1]])
            for domain in reversed(args):
                if not product_code_multi.split()[0] in domain:
                    if not check:
                        list.append(domain)
                        args.remove(domain)
                else:
                    check = True
            if index:
                domain_or = []
                for i in range(1, len(product_code_multi.split())):
                    args.insert(index, unicode('|'))
                # args += domain_or
                for i in range(1, len(product_code_multi.split())):
                    domain_add = []
                    for k in range(1, count_condition):
                        domain_add.append(unicode('|'))
                    for condition in list_condition:
                        cont = condition + [product_code_multi.split()[i]]
                        domain_add.append(cont)
                    args += domain_add
                args += list
                True
        res = super(product_template_inherit, self).search(args, offset=offset, limit=limit, order=order, count=count)
        return res


class product_group(models.Model):
    _name = 'product.group'

    name = fields.Char(string="Group Name")


class product_group_sale(models.Model):
    _name = 'product.group.sale'

    name = fields.Char(string="Group Name")
    group_line_ids = fields.One2many('product.group.sale.line', 'product_group_sale_id', string="Group Line")
    price_type = fields.Selection(
        [('list_price', 'Giá bán'), ('standard_price', 'Chi phí'), ('cost_root', 'Giá Trung Bình')],
        'Loại giá sử dụng', default="list_price")

    def _check_duplicate_name(self):
        res = True
        if self.env['product.group.sale'].search([('id', '!=', self.id), ('name', '=', self.name)]):
            res = False
        return res

    _constraints = [(_check_duplicate_name, 'Tên nhóm sản phẩm bán hàng đã tồn tại.', ['name'])]

    def merge_sale_group(self, sale_group_ids):
        for sale_group_id in sale_group_ids:
            product_ids = self.env['product.template'].search([('group_sale_id', '=', sale_group_id.id)])
            for product_id in product_ids:
                product_id.group_sale_id = self
        sale_group_ids.unlink()

    def export_product_group_sale(self):
        ids = self.env.context.get('active_ids', [])
        group_sale_ids = self.browse(ids)

        list_cus = ['Loại sản phẩm', 'Loại giá sử dụng']
        for group_sale_id in group_sale_ids:
            for line in group_sale_id.group_line_ids:
                if line.partner_name not in list_cus:
                    list_cus.append(str(line.partner_name))


class product_group_sale_line(models.Model):
    _name = 'product.group.sale.line'

    partner_id = fields.Many2one('res.partner', string="Customer", domain=[('customer', '=', True)])
    partner_name = fields.Char(string="Relative Customer Name")
    discount = fields.Float(string="Discount")
    product_group_sale_id = fields.Many2one('product.group.sale')
    price_type = fields.Selection(
        [('list_price', 'Giá bán'), ('standard_price', 'Chi phí'), ('cost_root', 'Giá Trung Bình')],
        'Loại giá sử dụng', related="product_group_sale_id.price_type")
