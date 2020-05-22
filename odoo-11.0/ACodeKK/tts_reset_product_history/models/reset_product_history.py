# -*- coding: utf-8 -*-

from odoo import models, fields, api
import base64
from xlrd import open_workbook


class reset_product_history(models.TransientModel):
    _name = 'reset.product.history'

    start_date = fields.Datetime('Ngày bắt đầu', required=1, default='2019-08-01 00:00:00')
    product_ids = fields.Many2many('product.product', string='Danh sách sản phẩm')
    check_all = fields.Boolean(default=False, string='Tất cả sản phẩm')
    import_data = fields.Binary(string="Tập tin")

    def import_data_get_product(self):
        if self.import_data:
            data = base64.b64decode(self.import_data)
            wb = open_workbook(file_contents=data)
            sheet = wb.sheet_by_index(0)
            product_ids = self.env['product.product']
            for row_no in range(sheet.nrows):
                if row_no > 0:
                    row = (
                        map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(
                            row.value),
                            sheet.row(row_no)))
                    if row[0]:
                        product_id = self.env['product.product'].search([
                            '|', ('active', '=', True),
                            ('active', '=', False),
                            ('default_code', '=', row[0].strip())
                        ])
                        if product_id:
                            product_ids += product_id
            return product_ids

    @api.multi
    def reset_product_history(self):
        for rec in self:
            PriceHistory = self.env['product.price.history']
            if rec.check_all:
                product_ids = self.env['product.product'].search(['|', ('active', '=', True), ('active', '=', False)])
            elif rec.import_data:
                product_ids = self.import_data_get_product()
            else:
                product_ids = rec.product_ids
            count = 0
            for product_id in product_ids:
                count += 1
                price_history_ids = PriceHistory.search(
                    [('datetime', '>', rec.start_date), ('product_id', '=', product_id.id)])
                price_history_ids.unlink()
                if product_id.cost_method != 'average':
                    continue
                domain = [
                    ('location_id.usage', '=', 'procurement'),
                    ('location_dest_id.not_sellable', '=', False),
                    ('location_dest_id.usage', '=', 'internal'),
                    ('state', '=', 'done'),
                    ('date', '>', rec.start_date),
                    ('product_id', '=', product_id.id)
                ]

                move_ids = self.env['stock.move'].search(domain, order='date DESC')
                new_std_price = 0
                for move in move_ids:
                    product_tot_qty_available = move.remain_qty_dk
                    if move.picking_id.picking_from_sale_return:
                        if move.picking_id.sale_id.sale_order_return_ids:
                            order_return = move.picking_id.sale_id.sale_order_return_ids[0]
                            if order_return.invoice_ids:
                                invoice_id = order_return.invoice_ids[0]
                                date_order = invoice_id.create_date
                            else:
                                date_order = order_return.confirmation_date
                        else:
                            date_order = move.picking_id.sale_id.confirmation_date
                        amount_unit = move.product_id.get_history_price(move.company_id.id, move.date)
                        amount_cost_sale = move.product_id.get_history_price(move.company_id.id, date_order)
                        new_std_price = ((amount_unit * product_tot_qty_available) + (
                                amount_cost_sale * move.product_qty)) / (product_tot_qty_available + move.product_qty)
                    else:
                        # if the incoming move is for a purchase order with foreign currency, need to call this to get the same value that the quant will use.
                        amount_unit = move.product_id.get_history_price(move.company_id.id, move.date)
                        new_std_price = ((amount_unit * product_tot_qty_available) + (
                                move.price_unit * move.product_qty)) / (product_tot_qty_available + move.product_qty)
                    PriceHistory.create({
                        'product_id': move.product_id.id,
                        'cost': new_std_price,
                        'company_id': self._context.get('force_company', self.env.user.company_id.id),
                        'datetime': move.date,
                    })
                if new_std_price != 0:
                    product_id.with_context(not_update_price_history=True).write({
                        'standard_price': new_std_price,
                    })
                print
                count


class product_product_ihr(models.Model):
    _inherit = 'product.product'

    @api.multi
    def _set_standard_price(self, value):
        ''' Store the standard price change in order to be able to retrieve the cost of a product for a given date'''
        if not self._context.get('not_update_price_history', False):
            PriceHistory = self.env['product.price.history']
            for product in self:
                PriceHistory.create({
                    'product_id': product.id,
                    'cost': value,
                    'company_id': self._context.get('force_company', self.env.user.company_id.id),
                })
