# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_round, float_is_zero


class stock_move(models.Model):
    _inherit = 'stock.move'

    purchase_order_id        = fields.Many2one('purchase.order', 'Tham Chiếu', related='picking_id.purchase_id')
    sale_order_id            = fields.Many2one('sale.order', 'Tham Chiếu', related='picking_id.sale_id')
    brand_name               = fields.Char('Thương Hiệu', related='product_id.brand_name', store=True)
    product_group_id         = fields.Many2one('product.group', 'Nhóm', related='product_id.group_id', store=True)
    product_qty_reserve      = fields.Float(string='SL giữ chỗ', compute='_get_product_qty_reserve')
    product_qty_missing      = fields.Float(string='SL còn thiếu', compute='_get_product_qty_missing', store=True)
    record_checked           = fields.Boolean('Checked')
    product_default_code_sub = fields.Char(string='Mã nội bộ', compute='_get_product_sub')
    product_name_sub         = fields.Char(string='Sản phẩm', compute='_get_product_sub')
    remain_qty               = fields.Float(string='Tồn',compute='_get_remain_qty',store=False)
    remain_qty_dk            = fields.Float(string="Tồn ĐK",compute='_get_remain_qty_dk')
    quantity_in              = fields.Float(string="Nhập",compute='_get_quantity',store=True)
    quantity_out             = fields.Float(string="Xuất", compute='_get_quantity',store=True)
    quantity_du_bao          = fields.Float(string="Tồn dự báo",compute='_get_quantity_du_bao',store=False)
    first_line               = fields.Boolean()
    partner_sub_id           = fields.Many2one('res.partner',string="Đối tác",compute="_get_res_partner",store=True)

    def cron_price_unit_stock_move(self):
        stock_move_ids = self.env['stock.move'].search([('price_unit','=',False)])
        for stock_move_id in stock_move_ids:
            stock_move_id.price_unit = sum(stock_move_id.mapped('quant_ids').mapped('inventory_value'))

    @api.multi
    def action_confirm(self):
        res = super(stock_move, self).action_confirm()
        for record in self:
            record.update_account_move_after()
        return res

    @api.depends('partner_id','picking_partner_id')
    def _get_res_partner(self):
        for record in self:
            if record.partner_id:
                record.partner_sub_id = record.partner_id
            if record.picking_partner_id:
                record.partner_sub_id = record.picking_partner_id

    @api.multi
    def update_stock_move_quantity(self):
        self._get_quantity()
        return True

    @api.depends('product_uom_qty', 'location_id', 'location_dest_id')
    def _get_quantity(self):
        for record in self:
            if record.location_dest_id.name == 'Stock' and record.location_id.name == 'Stock':
                record.quantity_in  = record.product_uom_qty
                record.quantity_out = record.product_uom_qty
            elif record.location_dest_id.name == 'Stock':
                record.quantity_in  = record.product_uom_qty
                record.quantity_out = 0
            else:
                record.quantity_in  = 0
                record.quantity_out = record.product_uom_qty

    def _get_remain_qty_dk(self):
        for record in self:
            query_in_1 = """SELECT SUM(m.product_uom_qty) AS total_qty FROM stock_move m 
            INNER JOIN stock_location l
            ON l.id = m.location_dest_id WHERE m.product_id = '%s' AND l.name = 'Stock' AND m.date < '%s' AND m.state = 'done'"""% (record.product_id.id, record.date)
            self.env.cr.execute(query_in_1)
            sum_in_1 = self.env.cr.fetchall()
            if sum_in_1 and len(sum_in_1) > 0:
                sum_in_1 = sum_in_1[0][0] or 0
            else:
                sum_in_1 = 0

            query_in_2 = """SELECT SUM(m.product_uom_qty) AS total_qty FROM stock_move m 
                        INNER JOIN stock_location l
                        ON l.id = m.location_dest_id WHERE m.product_id = '%s' AND l.name = 'Stock' AND m.date = '%s' AND m.id < '%s' AND m.state = 'done'""" % \
                         (record.product_id.id, record.date,record.id)
            self.env.cr.execute(query_in_2)
            sum_in_2 = self.env.cr.fetchall()
            if sum_in_2 and len(sum_in_2) > 0:
                sum_in_2 = sum_in_2[0][0] or 0
            else:
                sum_in_2 = 0

            query_out_1 = """SELECT SUM(m.product_uom_qty) AS total_qty FROM stock_move m 
            INNER JOIN stock_location l
            ON l.id = m.location_id WHERE m.product_id = '%s' AND l.name = 'Stock' AND m.date < '%s' AND m.state = 'done'"""% (record.product_id.id, record.date)
            self.env.cr.execute(query_out_1)
            sum_out_1 = self.env.cr.fetchall()
            if sum_out_1 and len(sum_out_1) > 0:
                sum_out_1 = sum_out_1[0][0] or 0
            else:
                sum_out_1 = 0

            query_out_2 = """SELECT SUM(m.product_uom_qty) AS total_qty FROM stock_move m 
                                    INNER JOIN stock_location l
                                    ON l.id = m.location_id WHERE m.product_id = '%s' AND l.name = 'Stock' AND m.date = '%s' AND m.id < '%s' AND m.state = 'done'""" % \
                         (record.product_id.id, record.date, record.id)
            self.env.cr.execute(query_out_2)
            sum_out_2 = self.env.cr.fetchall()
            if sum_out_2 and len(sum_out_2) > 0:
                sum_out_2 = sum_out_2[0][0] or 0
            else:
                sum_out_2 = 0

            remain_qty_dk = sum_in_1 + sum_in_2 - sum_out_1 - sum_out_2
            record.remain_qty_dk = remain_qty_dk

    def update_account_move_after(self):
        for record in self:
            query_1 = """SELECT id FROM stock_move m 
                        WHERE m.product_id = '%s' AND m.date > '%s' AND m.state not in ('draft','cancel')""" % (
            record.product_id.id, record.date)
            self.env.cr.execute(query_1)
            account_move_ids = self.env.cr.fetchall()
            for account_move_id in account_move_ids:
                if account_move_id[0]:
                    account_move_id = self.env['stock.move'].browse(account_move_id[0])
                    account_move_id._get_quantity_du_bao()
                    account_move_id._get_remain_qty()

    def _get_remain_qty_dk_not_cancel(self):
        for record in self:
            query_in_1 = """SELECT SUM(m.product_uom_qty) AS total_qty FROM stock_move m 
            INNER JOIN stock_location l
            ON l.id = m.location_dest_id WHERE m.product_id = '%s' AND l.name = 'Stock' AND m.date < '%s' AND m.state not in ('draft','cancel')"""% (record.product_id.id, record.date)
            self.env.cr.execute(query_in_1)
            sum_in_1 = self.env.cr.fetchall()
            if sum_in_1 and len(sum_in_1) > 0:
                sum_in_1 = sum_in_1[0][0] or 0
            else:
                sum_in_1 = 0

            query_in_2 = """SELECT SUM(m.product_uom_qty) AS total_qty FROM stock_move m 
                        INNER JOIN stock_location l
                        ON l.id = m.location_dest_id WHERE m.product_id = '%s' AND l.name = 'Stock' AND m.date = '%s' AND m.id < '%s' AND m.state not in ('draft','cancel')""" % \
                         (record.product_id.id, record.date,record.id)
            self.env.cr.execute(query_in_2)
            sum_in_2 = self.env.cr.fetchall()
            if sum_in_2 and len(sum_in_2) > 0:
                sum_in_2 = sum_in_2[0][0] or 0
            else:
                sum_in_2 = 0

            query_out_1 = """SELECT SUM(m.product_uom_qty) AS total_qty FROM stock_move m 
            INNER JOIN stock_location l
            ON l.id = m.location_id WHERE m.product_id = '%s' AND l.name = 'Stock' AND m.date < '%s' AND m.state not in ('draft','cancel')"""% (record.product_id.id, record.date)
            self.env.cr.execute(query_out_1)
            sum_out_1 = self.env.cr.fetchall()
            if sum_out_1 and len(sum_out_1) > 0:
                sum_out_1 = sum_out_1[0][0] or 0
            else:
                sum_out_1 = 0

            query_out_2 = """SELECT SUM(m.product_uom_qty) AS total_qty FROM stock_move m 
                                    INNER JOIN stock_location l
                                    ON l.id = m.location_id WHERE m.product_id = '%s' AND l.name = 'Stock' AND m.date = '%s' AND m.id < '%s' AND m.state not in ('draft','cancel')""" % \
                         (record.product_id.id, record.date, record.id)
            self.env.cr.execute(query_out_2)
            sum_out_2 = self.env.cr.fetchall()
            if sum_out_2 and len(sum_out_2) > 0:
                sum_out_2 = sum_out_2[0][0] or 0
            else:
                sum_out_2 = 0

            remain_qty_dk = sum_in_1 + sum_in_2 - sum_out_1 - sum_out_2
            return remain_qty_dk

    @api.depends('quantity_in', 'quantity_out')
    def _get_quantity_du_bao(self):
        for record in self:
            record.quantity_du_bao = record._get_remain_qty_dk_not_cancel() + record.quantity_in - record.quantity_out

    @api.depends('quantity_in','quantity_out','state')
    def _get_remain_qty(self):
        for record in self:
            if record.state == 'done':
                record.remain_qty = record.remain_qty_dk + record.quantity_in - record.quantity_out
            else:
                record.remain_qty = record.remain_qty_dk
            # if remain_qty != record.remain_qty:
            #     self._cr.execute("""UPDATE stock_move SET remain_qty=%s WHERE id=%s""" % (remain_qty,record.id))

    @api.depends('product_qty_reserve', 'product_uom_qty')
    def _get_product_qty_missing(self):
        for record in self:
            if record.filtered(lambda move: move.state in ('draft', 'done', 'cancel') or move.location_id.usage != 'internal'):
                record.product_qty_missing == 0.0
            else:
                record.product_qty_missing = record.product_uom_qty - record.product_qty_reserve

    def _get_product_sub(self):
        for record in self:
            record.product_default_code_sub = record.product_id.default_code
            record.product_name_sub = record.product_id.name

    def cron_run_action_assign(self):
        pickings = self.env['stock.picking'].search([
            ('state', '=', 'assigned')
        ])
        if pickings and len(pickings) > 0:
            for picking in pickings:
                picking.do_new_transfer()

        pickings = self.env['stock.picking'].search([
            ('state', 'in', ('confirmed', 'partially_available'))
        ])
        if pickings and len(pickings) > 0:
            # Step1: Reset all stock picking
            pickings.do_unreserve()

            for picking in pickings:
                # Step 2: Assign picking one by one
                picking.action_assign()

                # Step3: If picking dont have enough good we assign to other first
                if picking.state == 'partially_available':
                    picking.do_unreserve()
                elif picking.state == 'assigned':
                    picking.do_new_transfer()
                else:
                    pass

            # Step4: After all assign current confirmed picking
            confirmed_pickings = pickings.filtered(lambda r: r.state in ('confirmed'))
            confirmed_pickings.action_assign()

        return True

    def action_all_stock_move(self):
        ids = self.env.context.get('active_ids', [])
        orderlines = self.browse(ids)
        product_list = []
        for order in orderlines:
            product_list.append(order.product_id.id)
        action = self.env.ref('tuanhuy_stock.stock_picking_line_action').read()[0]
        action['domain'] = [('product_id', 'in', product_list)]
        return action

    def action_update_check_record(self):
        ids = self.env.context.get('active_ids', [])
        orderlines = self.browse(ids)
        for order in orderlines:
            order.record_checked = False

    @api.multi
    def change_record_checked(self):
        for record in self:
            if not record.record_checked:
                record.record_checked = True
            else:
                record.record_checked = False

    @api.multi
    def _get_product_qty_reserve(self):
        for record in self:
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            void_moves = record.filtered(
                lambda move: move.state in ('draft', 'done', 'cancel') or move.location_id.usage != 'internal')
            other_moves = record - void_moves
            total_available = 0.0
            for move in other_moves:
                total_available = min(move.product_qty, move.reserved_availability + move.availability)
                total_available = move.product_id.uom_id._compute_quantity(total_available, move.product_uom,
                                                                           round=False)
                total_available = float_round(total_available, precision_digits=precision)
            record.product_qty_reserve = total_available

    @api.multi
    def action_done(self):
        res = super(stock_move, self).action_done()
        for stock in self:
            if stock.inventory_id and stock.inventory_id.accounting_date:
                stock.write({'date': stock.inventory_id.accounting_date})
                for quant in stock.quant_ids:
                    quant.in_date = stock.inventory_id.accounting_date
            if 'purchase_order_return' in self._context and self._context['purchase_order_return'] == True:
                stock.write({'date': stock.purchase_order_id.date_order})
                for quant in stock.quant_ids:
                    quant.in_date = stock.purchase_order_id.date_order
            elif 'sale_order_return' in self._context and self._context['sale_order_return'] == True:
                stock.write({'date': stock.sale_order_id.date_order})
                for quant in stock.quant_ids:
                    quant.in_date = stock.sale_order_id.date_order
            elif not stock.inventory_id and 'sale_order_return' not in self._context and 'purchase_order_return' not in self._context:
                order = stock.purchase_order_id or stock.sale_order_id
                if order:
                    stock.write({'date': order.date_order})
                    for quant in stock.quant_ids:
                        quant.in_date = order.date_order
        return res

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):

        if self.env.context.get('summaries', False):
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
                list_domain = []
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
                            list_domain.append(do)
                            domain.remove(do)
                    else:
                        check = True
                # if index:
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
                domain += list_domain
            res = super(stock_move, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)

            def convertVals(x):
                if x.get('origin', False) and ('SO' in x.get('origin') or 'RTP' in x.get('origin')):
                    if 'product_uom_qty' in x:
                        x['product_uom_qty'] = -x['product_uom_qty']
                    if 'product_qty_reserve' in x:
                        x['product_qty_reserve'] = -x['product_qty_reserve']

                return x

            res = map(lambda x: convertVals(x), res)
            list_first_line = []
            product_ids = list(set([x['product_id'][0] for x in res]))
            for product in product_ids:
                dict_list = []
                for record in res:
                    if record['product_id'][0] == product:
                        dict_list.append(record)
                min_date = dict_list[0]['date']
                min_id = dict_list[0]['id']
                if len(dict_list) > 1:
                    for line in range(1, len(dict_list)):
                        if dict_list[line]['date'] < min_date:
                            min_date = dict_list[line]['date']
                            min_id = dict_list[line]['id']
                list_first_line.append(min_id)
            for record in res:
                if record['id'] in list_first_line:
                    record['first_line'] = True
            return res
        if self.env.context.get('stock_summaries', False):
            res = super(stock_move, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit,
                                                      order=order)

            def convertVals(x):
                if x.get('location_dest_id', False) and x.get('location_dest_id', False)[1] != 'WH/Stock':
                    x['product_uom_qty'] = -x['product_uom_qty']
                return x

            res = map(lambda x: convertVals(x), res)
            return res
        return super(stock_move, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)

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
        res = super(stock_move, self.with_context(virtual_id=False)).read_group(domain, fields, groupby, offset=offset,
                                                                              limit=limit, orderby=orderby, lazy=lazy)
        for result in res:
            if 'product_id' in result:
                picking_type_id = self.env['stock.picking.type'].search([('code', '=', 'outgoing')], limit=1)
                moves = self.env['stock.move'].search([
                    ('picking_type_id', '=', picking_type_id and picking_type_id.id),
                    ('product_id', '=', result['product_id'][0])
                ])
                if 'product_uom_qty' in result:
                    for move in moves:
                        result['product_uom_qty'] -= 2 * move.product_uom_qty

        if 'origin' in groupby:
            for line in res:
                if 'PO' in line.get('origin',False) or 'RTP' in line.get('origin',False):
                    self.env.cr.execute("select po.date_order from purchase_order as po where po.name = '%s'" % (
                        line.get('origin', False)))
                res_trans = self.env.cr.fetchall()
                if res_trans:
                    line.update({
                        'date': res_trans[0][0],
                    })
        return res
