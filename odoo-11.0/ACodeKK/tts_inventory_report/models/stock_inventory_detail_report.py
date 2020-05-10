# -*- coding: utf-8 -*-
from odoo import models, fields, api
import pytz
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo import tools
import base64
import StringIO
import xlsxwriter
from xlrd import open_workbook


class stock_check_report(models.Model):
    _name = 'stock.inventory.detail.report'
    _auto = False
    _order = 'default_code'

    product_id = fields.Many2one('product.product', string='Sản phẩm')
    name = fields.Char(string='Sản phẩm')
    display_name = fields.Char(string='Sản phẩm', compute='get_product_inventory_data')
    default_code = fields.Char(string='Mã nội bộ')
    uom_id = fields.Many2one('product.uom', string='Đơn vị tính')
    categ_id = fields.Many2one('product.category', string='Nhóm nội bộ')
    archived_date = fields.Datetime('Archived Time')
    unarchived_date = fields.Datetime('UnArchived Time')
    before_qty = fields.Float('Tồn đầu kì', compute='get_product_inventory_data')
    before_value = fields.Float('Giá trị đầu kì', compute='get_product_inventory_data')
    income_qty = fields.Float('Nhập NCC', compute='get_product_inventory_data')
    income_value = fields.Float('Giá trị nhập NCC', compute='get_product_inventory_data')
    outgoing_qty = fields.Float('Xuất bán', compute='get_product_inventory_data')
    outgoing_value = fields.Float('Giá trị xuất bán', compute='get_product_inventory_data')
    scrap_qty = fields.Float('Xuất hủy', compute='get_product_inventory_data')
    scrap_value = fields.Float('Giá trị xuất hủy', compute='get_product_inventory_data')
    add_inventory_qty = fields.Float('Nhập kiểm tăng', compute='get_product_inventory_data')
    add_inventory_value = fields.Float('Giá trị nhập kiểm tăng', compute='get_product_inventory_data')
    income_return_qty = fields.Float('Nhập trả', compute='get_product_inventory_data')
    income_return_value = fields.Float('Giá trị nhập trả', compute='get_product_inventory_data')
    sub_inventory_qty = fields.Float('Xuất kiểm', compute='get_product_inventory_data')
    sub_inventory_value = fields.Float('Giá trị xuất kiểm', compute='get_product_inventory_data')
    outgoing_return_qty = fields.Float('Xuất trả', compute='get_product_inventory_data')
    outgoing_return_value = fields.Float('Giá trị xuất trả', compute='get_product_inventory_data')
    after_qty = fields.Float('Tồn cuối kì', compute='get_product_inventory_data')
    after_value = fields.Float('Giá trị cuối kì', compute='get_product_inventory_data')

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'stock_inventory_detail_report')
        self.env.cr.execute(
            """CREATE or REPLACE VIEW stock_inventory_detail_report as (
            SELECT 
            min(pp.id) as id,
            min(pp.id) as product_id,
            pt.uom_id as uom_id,
            pt.name as name,
            pt.categ_id as categ_id,
            pp.default_code as default_code,
            pp.archived_date as archived_date,
            pp.unarchived_date as unarchived_date
            FROM product_product as pp
            INNER JOIN product_template pt ON pt.id = pp.product_tmpl_id
            GROUP BY pp.id, pt.uom_id, pt.name, pp.default_code, pt.categ_id
            ORDER BY pp.default_code
            )""")

    def get_cost_product(self, product_id, datetime):
        cost = 0
        price_history_ids = self.env['product.price.history'].search(
            [('product_id', '=', product_id.id), ('datetime', '=', datetime)], order='datetime asc')
        if price_history_ids:
            cost = price_history_ids[0].cost
        if not cost:
            price_history_ids = self.env['product.price.history'].search(
                [('product_id', '=', product_id.id), ('datetime', '<', datetime)], order='datetime desc')
            if price_history_ids:
                cost = price_history_ids[0].cost
        return cost

    ## Todo get before value

    def get_income_before_product(self, product_id, end_date, start_date=None):
        state = 'done'
        location_procurement = self.env.ref('stock.location_procurement')
        stock_location_stock = self.env.ref('stock.stock_location_stock')
        end_date = end_date + ' 23:59:59'

        query = """select sm.product_uom_qty, sm.price_unit from stock_move as sm \
                  JOIN stock_picking_type as spt ON spt.id = sm.picking_type_id \
                  JOIN product_product as pp ON pp.id = sm.product_id \
                  JOIN stock_picking as sp ON sp.id = sm.picking_id \
                  where sm.date <= %s and sm.product_id = %s \
                  and sm.location_id = %s and sm.location_dest_id = %s \
                  and sm.state = %s and sp.check_return_picking = FALSE
                  """

        params = (end_date, product_id.id, location_procurement.id, stock_location_stock.id, state)

        if start_date:
            query += " and sm.date >= %s"
            start_date = start_date + ' 00:00:00'
            params = (end_date, product_id.id, location_procurement.id, stock_location_stock.id, state, start_date)

        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        income_qty = income_value = 0
        for line in result:
            if line.get('product_uom_qty', False):
                income_qty += line.get('product_uom_qty')
            if line.get('price_unit', False):
                income_value += line.get('price_unit', 0) * line.get('product_uom_qty', 0)
        return income_qty, income_value

    def get_outgoing_before_product(self, product_id, end_date, start_date=None):
        state = 'done'
        move_type = 'outgoing'
        end_date = end_date + ' 23:59:59'

        query = """select sm.product_uom_qty, sm.date from stock_move as sm \
                  JOIN stock_picking_type as spt ON spt.id = sm.picking_type_id \
                  JOIN product_product as pp ON pp.id = sm.product_id \
                  JOIN stock_picking as sp ON sp.id = sm.picking_id \
                  where sm.date <= %s \
                  and spt.code = %s and sm.product_id = %s \
                  and sm.state = %s and sp.check_return_picking = FALSE \
                  """

        params = (end_date, move_type, product_id.id, state)

        if start_date:
            query += " and sm.date >= %s"
            start_date = start_date + ' 00:00:00'
            params = (end_date, move_type, product_id.id, state, start_date)

        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        outgoing_qty = outgoing_value = 0
        for line in result:
            if line.get('product_uom_qty', False):
                outgoing_qty += line.get('product_uom_qty')
                price = product_id.get_history_price(product_id.company_id.id, line.get('date', False))
                outgoing_value += line.get('product_uom_qty') * price

        return outgoing_qty, outgoing_value

    def get_income_return_before_product(self, product_id, end_date, start_date=None):
        state = 'done'
        move_type = 'outgoing'
        end_date = end_date + ' 23:59:59'

        query = """select sm.product_uom_qty, sm.date, pl.price_unit from stock_move as sm \
                              JOIN stock_picking_type as spt ON spt.id = sm.picking_type_id \
                              JOIN product_product as pp ON pp.id = sm.product_id \
                              JOIN stock_picking as sp ON sp.id = sm.picking_id \
                              JOIN purchase_order_line as pl on pl.id = sm.purchase_line_id \
                              where sm.date <= %s \
                              and spt.code = %s and sm.product_id = %s \
                              and sm.state = %s and sp.check_return_picking = TRUE \
                              """

        params = (end_date, move_type, product_id.id, state)

        if start_date:
            query += " and sm.date >= %s"
            start_date = start_date + ' 00:00:00'
            params = (end_date, move_type, product_id.id, state, start_date)

        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        income_qty = income_value = 0
        for line in result:
            if line.get('product_uom_qty', False):
                income_qty += line.get('product_uom_qty')
                price = product_id.get_history_price(product_id.company_id.id, line.get('date'))
                income_value += price * line.get('product_uom_qty', 0)
            # if line.get('price_unit', False):
            #     income_value += line.get('price_unit', 0) * line.get('product_uom_qty', 0)

        return income_qty, income_value

    def get_outgoing_return_before_product(self, product_id, end_date, start_date=None):
        state = 'done'
        move_type = 'incoming'
        end_date = end_date + ' 23:59:59'

        location_procurement = self.env.ref('stock.location_procurement')
        stock_location_stock = self.env.ref('stock.stock_location_stock')
        not_sellable = self.env['stock.location'].search([('not_sellable', '=', True)])
        location_dest_list = [location.id for location in not_sellable]
        location_dest_list.append(stock_location_stock.id)
        location_dest = ', '.join(str(id) for id in location_dest_list)

        query = """select sm.product_uom_qty, sm.price_unit, sm.date, sm.amount_cost_sale from stock_move as sm \
                  JOIN stock_picking_type as spt ON spt.id = sm.picking_type_id \
                  JOIN product_product as pp ON pp.id = sm.product_id \
                  JOIN stock_picking as sp ON sp.id = sm.picking_id \
                  where sm.date <= %s and sm.product_id = %s \
                  and sm.location_id = %s and sm.location_dest_id in %s \
                  and sm.state = %s and sp.check_return_picking = TRUE \
                  """

        params = (end_date, product_id.id, location_procurement.id, tuple(location_dest_list), state)

        if start_date:
            query += " and sm.date >= %s"
            start_date = start_date + ' 00:00:00'
            params = (end_date, product_id.id, location_procurement.id, tuple(location_dest_list), state, start_date)

        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        outgoing_qty = outgoing_value = 0
        for line in result:
            if line.get('product_uom_qty', False):
                outgoing_qty += line.get('product_uom_qty')
                # price = product_id.get_history_price(product_id.company_id.id, line.get('date'))
                outgoing_value += line.get('amount_cost_sale', 0) * line.get('product_uom_qty', 0)
        return outgoing_qty, outgoing_value

    def get_scrap_before_product(self, product_id, end_date, start_date=None):
        state = 'done'
        end_date = end_date + ' 23:59:59'

        query = """
            select sm.product_uom_qty, sm.date from stock_move as sm
            where sm.date <= %s and sm.product_id = %s \
            and sm.scrapped = TRUE and sm.state = %s
        """
        params = (end_date, product_id.id, state)

        if start_date:
            query += " and sm.date >= %s"
            start_date = start_date + ' 00:00:00'
            params = (end_date, product_id.id, state, start_date)

        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        scrap_qty = scrap_value = 0
        for line in result:
            if line.get('product_uom_qty', False):
                scrap_qty += line.get('product_uom_qty')
                price = product_id.get_history_price(product_id.company_id.id, line.get('date'))
                scrap_value += line.get('product_uom_qty') * price

        return scrap_qty, scrap_value

    def get_inventory_before_product(self, product_id, end_date, start_date=None):
        stock_location_stock = self.env.ref('stock.stock_location_stock')
        location_inventory = self.env.ref('stock.location_inventory')
        state = 'done'
        end_date = end_date + ' 23:59:59'

        add_inventory_qty = add_inventory_value = sub_inventory_qty = sub_inventory_value = 0

        sql_add = """SELECT sm.product_uom_qty, sm.date from stock_move as sm \
                    where sm.date <= %s and sm.product_id = %s and sm.state = %s \
                    and sm.location_id = %s and sm.location_dest_id = %s \
                    and sm.inventory_id is not null"""
        add_params = (end_date, product_id.id, state, location_inventory.id, stock_location_stock.id)

        if start_date:
            sql_add += " and sm.date >= %s"
            start_date = start_date + ' 00:00:00'
            add_params = (end_date, product_id.id, state, location_inventory.id, stock_location_stock.id, start_date)

        self.env.cr.execute(sql_add, add_params)
        result = self.env.cr.dictfetchall()
        for line in result:
            if line.get('product_uom_qty', False):
                add_inventory_qty += line.get('product_uom_qty')
                price = product_id.get_history_price(product_id.company_id.id, line.get('date', False))
                add_inventory_value += line.get('product_uom_qty') * price

        sql_sub = """SELECT sm.product_uom_qty, sm.date from stock_move as sm \
                    where sm.date <= %s and sm.product_id = %s and sm.state = %s \
                    and sm.location_id = %s and sm.location_dest_id = %s \
                    and sm.inventory_id is not null"""
        sub_params = (end_date, product_id.id, state, stock_location_stock.id, location_inventory.id)

        if start_date:
            sql_sub += " and sm.date >= %s"
            sub_params = (end_date, product_id.id, state, stock_location_stock.id, location_inventory.id, start_date)

        self.env.cr.execute(sql_sub, sub_params)
        result = self.env.cr.dictfetchall()
        for line in result:
            if line.get('product_uom_qty', False):
                sub_inventory_qty += line.get('product_uom_qty')
                price = product_id.get_history_price(product_id.company_id.id, line.get('date', False))
                sub_inventory_value += line.get('product_uom_qty') * price

        return add_inventory_qty, add_inventory_value, sub_inventory_qty, sub_inventory_value

    # TODO get data for product

    def get_end_value_july(self, product_id, end_date, cost):

        income_qty, income_value = self.get_income_before_product(product_id, end_date)
        outgoing_qty, outgoing_value = self.get_outgoing_before_product(product_id, end_date)
        scrap_qty, scrap_value = self.get_scrap_before_product(product_id, end_date)
        add_inventory_qty, add_inventory_value, sub_inventory_qty, sub_inventory_value = self.get_inventory_before_product(
            product_id, end_date)
        income_return_qty, income_return_value = self.get_outgoing_return_before_product(product_id, end_date)
        outgoing_return_qty, outgoing_return_value = self.get_income_return_before_product(product_id, end_date)

        before_qty = income_qty + add_inventory_qty + income_return_qty - outgoing_qty - sub_inventory_qty - outgoing_return_qty - scrap_qty
        before_value = before_qty * cost
        return before_qty, before_value

    def get_before_product(self, product_id, end_date):
        cost = self.get_cost_product(product_id, '2019-08-01 00:00:00')
        date_t7 = datetime.strptime('2019-07-31', DEFAULT_SERVER_DATE_FORMAT)
        if date_t7 < datetime.strptime(end_date, DEFAULT_SERVER_DATE_FORMAT):
            start_date = '2019-08-01'

            end_qty_july, end_value_july = self.get_end_value_july(product_id, '2019-07-31', cost)
            income_qty, income_value = self.get_income_before_product(product_id, end_date, start_date)
            outgoing_qty, outgoing_value = self.get_outgoing_before_product(product_id, end_date, start_date)
            scrap_qty, scrap_value = self.get_scrap_before_product(product_id, end_date, start_date)
            add_inventory_qty, add_inventory_value, sub_inventory_qty, sub_inventory_value = self.get_inventory_before_product(
                product_id, end_date, start_date)
            income_return_qty, income_return_value = self.get_outgoing_return_before_product(product_id, end_date,
                                                                                             start_date)
            outgoing_return_qty, outgoing_return_value = self.get_income_return_before_product(product_id, end_date,
                                                                                               start_date)

            before_qty = end_qty_july + income_qty + add_inventory_qty + income_return_qty - outgoing_qty - sub_inventory_qty - outgoing_return_qty - scrap_qty
            before_value = end_value_july + income_value + add_inventory_value + income_return_value - outgoing_value - sub_inventory_value - outgoing_return_value - scrap_value
        elif date_t7 == datetime.strptime(end_date, DEFAULT_SERVER_DATE_FORMAT):
            income_qty, income_value = self.get_income_before_product(product_id, end_date)
            outgoing_qty, outgoing_value = self.get_outgoing_before_product(product_id, end_date)
            scrap_qty, scrap_value = self.get_scrap_before_product(product_id, end_date)
            add_inventory_qty, add_inventory_value, sub_inventory_qty, sub_inventory_value = self.get_inventory_before_product(
                product_id, end_date)
            income_return_qty, income_return_value = self.get_outgoing_return_before_product(product_id, end_date)
            outgoing_return_qty, outgoing_return_value = self.get_income_return_before_product(product_id, end_date)
            before_qty = income_qty + add_inventory_qty + income_return_qty - outgoing_qty - sub_inventory_qty - outgoing_return_qty - scrap_qty
            before_value = before_qty * cost
        else:
            before_qty = before_value = 0
        return before_qty, before_value

    def get_income_product(self, product_id, start_date, end_date, picking_purchase_ids=None):
        state = 'done'
        location_procurement = self.env.ref('stock.location_procurement')
        stock_location_stock = self.env.ref('stock.stock_location_stock')
        query = """select sm.product_uom_qty, sm.price_unit from stock_move as sm \
                              JOIN stock_picking_type as spt ON spt.id = sm.picking_type_id \
                              JOIN product_product as pp ON pp.id = sm.product_id \
                              JOIN stock_picking as sp ON sp.id = sm.picking_id \
                              where sm.date >= %s and sm.date <= %s and sm.product_id = %s \
                              and sm.location_id = %s and sm.location_dest_id = %s \
                              and sm.state = %s and sp.check_return_picking = FALSE;
                              """
        # if picking_purchase_ids:
        #     picking_ids = "and sm.picking_id in (%s)" % (', '.join(str(id) for id in picking_purchase_ids))
        #     query += picking_ids
        date_start = start_date + ' 00:00:00'
        date_end = end_date + ' 23:59:59'

        params = (date_start, date_end, product_id.id, location_procurement.id, stock_location_stock.id, state)

        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        income_qty = income_value = 0
        for line in result:
            if line.get('product_uom_qty', False):
                income_qty += line.get('product_uom_qty')
            if line.get('price_unit', False):
                income_value += line.get('price_unit', 0) * line.get('product_uom_qty', 0)
        return income_qty, income_value

    def get_outgoing_product(self, product_id, start_date, end_date, picking_sale_ids=None):
        state = 'done'
        move_type = 'outgoing'

        query = """select sm.product_uom_qty, sm.date, sm.price_unit  from stock_move as sm \
                                  JOIN stock_picking_type as spt ON spt.id = sm.picking_type_id \
                                  JOIN product_product as pp ON pp.id = sm.product_id \
                                  JOIN stock_picking as sp ON sp.id = sm.picking_id \
                                  where sm.date >= %s and sm.date <= %s \
                                  and spt.code = %s and sm.product_id = %s \
                                  and sm.state = %s and sp.check_return_picking = FALSE \
                                  """
        # if picking_sale_ids:
        #     picking_ids = "and sm.picking_id in (%s)" % (', '.join(str(id) for id in picking_sale_ids))
        #     query += picking_ids
        start_date = start_date + ' 00:00:00'
        end_date = end_date + ' 23:59:59'

        params = (start_date, end_date, move_type, product_id.id, state)

        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        outgoing_qty = outgoing_value = 0
        for line in result:
            if line.get('product_uom_qty', False):
                outgoing_qty += line.get('product_uom_qty')
                price = product_id.get_history_price(product_id.company_id.id, line.get('date', False))
                outgoing_value += line.get('product_uom_qty') * price
        return outgoing_qty, outgoing_value

    def get_income_return_product(self, product_id, start_date, end_date, picking_purchase_ids=None):
        state = 'done'
        move_type = 'outgoing'
        query = """select sm.product_uom_qty, sm.date, pl.price_unit from stock_move as sm \
                              JOIN stock_picking_type as spt ON spt.id = sm.picking_type_id \
                              JOIN product_product as pp ON pp.id = sm.product_id \
                              JOIN stock_picking as sp ON sp.id = sm.picking_id \
                              JOIN purchase_order_line as pl on pl.id = sm.purchase_line_id \
                              where sm.date >= %s and sm.date <= %s \
                              and spt.code = %s and sm.product_id = %s \
                              and sm.state = %s and sp.check_return_picking = TRUE \
                              """
        # if picking_purchase_ids:
        #     picking_ids = "and sm.picking_id not in (%s)" % (', '.join(str(id) for id in picking_purchase_ids))
        #     query += picking_ids
        start_date = start_date + ' 00:00:00'
        end_date = end_date + ' 23:59:59'

        params = (start_date, end_date, move_type, product_id.id, state)

        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        income_qty = income_value = 0
        for line in result:
            if line.get('product_uom_qty', False):
                income_qty += line.get('product_uom_qty')
                price = product_id.get_history_price(product_id.company_id.id, line.get('date', False))
                income_value += price * line.get('product_uom_qty', 0)
            # if line.get('price_unit', False):
            #     income_value += line.get('price_unit', 0) * line.get('product_uom_qty', 0)
        return income_qty, income_value

    def get_outgoing_return_product(self, product_id, start_date, end_date, picking_sale_ids=None):
        state = 'done'
        move_type = 'incoming'
        location_procurement = self.env.ref('stock.location_procurement')
        stock_location_stock = self.env.ref('stock.stock_location_stock')
        not_sellable = self.env['stock.location'].search([('not_sellable', '=', True)])
        location_dest_list = [location.id for location in not_sellable]
        location_dest_list.append(stock_location_stock.id)
        location_dest = ', '.join(str(id) for id in location_dest_list)

        query = """select sm.product_uom_qty, sm.price_unit, sm.date, sm.amount_cost_sale from stock_move as sm \
                  JOIN stock_picking_type as spt ON spt.id = sm.picking_type_id \
                  JOIN product_product as pp ON pp.id = sm.product_id \
                  JOIN stock_picking as sp ON sp.id = sm.picking_id \
                  where sm.date >= %s and sm.date <= %s and sm.product_id = %s \
                  and sm.location_id = %s and sm.location_dest_id in %s \
                  and sm.state = %s and sp.check_return_picking = TRUE \
                  """
        # if picking_sale_ids:
        #     picking_ids = "and sm.picking_id not in (%s)" % (', '.join(str(id) for id in picking_sale_ids))
        #     query += picking_ids
        date_start = start_date + ' 00:00:00'
        date_end = end_date + ' 23:59:59'

        params = (date_start, date_end, product_id.id, location_procurement.id, tuple(location_dest_list), state)

        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        outgoing_qty = outgoing_value = 0
        for line in result:
            if line.get('product_uom_qty', False):
                outgoing_qty += line.get('product_uom_qty')
                # price = product_id.get_history_price(product_id.company_id.id, line.get('date', False))
                outgoing_value += line.get('amount_cost_sale', 0) * line.get('product_uom_qty', 0)
        return outgoing_qty, outgoing_value

    def get_scrap_product(self, product_id, start_date, end_date):
        state = 'done'
        query = """
            select sm.product_uom_qty, sm.date from stock_move as sm
            where sm.date >= %s and sm.date <= %s and sm.product_id = %s \
            and sm.scrapped = TRUE and sm.state = %s
        """
        date_start = start_date + ' 00:00:00'
        date_end = end_date + ' 23:59:59'
        params = (date_start, date_end, product_id.id, state)
        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        scrap_qty = scrap_value = 0
        for line in result:
            if line.get('product_uom_qty', False):
                scrap_qty += line.get('product_uom_qty')
                price = product_id.get_history_price(product_id.company_id.id, line.get('date'))
                scrap_value += line.get('product_uom_qty') * price
        return scrap_qty, scrap_value
        True

    def get_inventory_product(self, product_id, start_date, end_date):
        stock_location_stock = self.env.ref('stock.stock_location_stock')
        location_inventory = self.env.ref('stock.location_inventory')
        state = 'done'
        start_date = start_date + ' 00:00:00'
        end_date = end_date + ' 23:59:59'

        add_inventory_qty = add_inventory_value = sub_inventory_qty = sub_inventory_value = 0

        sql_add = """SELECT sm.product_uom_qty, sm.date from stock_move as sm \
                            where sm.date >= %s and sm.date <= %s and sm.product_id = %s and sm.state = %s \
                            and sm.location_id = %s and sm.location_dest_id = %s \
                            and sm.inventory_id is not null;"""
        add_params = (start_date, end_date, product_id.id, state, location_inventory.id, stock_location_stock.id)
        self.env.cr.execute(sql_add, add_params)
        result = self.env.cr.dictfetchall()
        for line in result:
            if line.get('product_uom_qty', False):
                add_inventory_qty += line.get('product_uom_qty')
                price = product_id.get_history_price(product_id.company_id.id, line.get('date', False))
                add_inventory_value += line.get('product_uom_qty') * price

        sql_sub = """SELECT sm.product_uom_qty, sm.date from stock_move as sm \
                            where sm.date >= %s and sm.date <= %s and sm.product_id = %s and sm.state = %s \
                            and sm.location_id = %s and sm.location_dest_id = %s \
                            and sm.inventory_id is not null;"""
        sub_params = (start_date, end_date, product_id.id, state, stock_location_stock.id, location_inventory.id)

        self.env.cr.execute(sql_sub, sub_params)
        result = self.env.cr.dictfetchall()
        for line in result:
            if line.get('product_uom_qty', False):
                sub_inventory_qty += line.get('product_uom_qty')
                price = product_id.get_history_price(product_id.company_id.id, line.get('date', False))
                sub_inventory_value += line.get('product_uom_qty') * price

        # add_inventory_qty = add_inventory_value = sub_inventory_qty = sub_inventory_value = 0
        # inventory_line = self.env['stock.inventory.line'].search(
        #     [('product_id', '=', product_id.id), ('inventory_id.date', '>=', start_date),
        #      ('inventory_id.date', '<=', end_date), ('inventory_id.state', '=', 'done')])
        # for line in inventory_line:
        #     inventory_date = line.inventory_id.date
        #     price = product_id.get_history_price(product_id.company_id.id, inventory_date)
        #     if line.theoretical_qty - line.product_qty > 0:
        #         sub_inventory_qty += line.theoretical_qty - line.product_qty
        #         sub_inventory_value += (line.theoretical_qty - line.product_qty) * price
        #     if line.theoretical_qty - line.product_qty < 0:
        #         add_inventory_qty += line.product_qty - line.theoretical_qty
        #         add_inventory_value += (line.product_qty - line.theoretical_qty) * price

        return add_inventory_qty, add_inventory_value, sub_inventory_qty, sub_inventory_value

    def get_product_inventory_data(self):
        start_date = self._context.get('date_start', False)
        if start_date:
            self.env['ir.config_parameter'].sudo().set_param('inventory.start_date', start_date)
        end_date = self._context.get('date_end', False)
        if end_date:
            self.env['ir.config_parameter'].sudo().set_param('inventory.end_date', end_date)

        for record in self:
            if not start_date and not end_date:
                start_date = self.env['ir.config_parameter'].sudo().get_param('inventory.start_date')
                end_date = self.env['ir.config_parameter'].sudo().get_param('inventory.end_date')
            end_date_before = (
                datetime.strptime(start_date, DEFAULT_SERVER_DATE_FORMAT) - timedelta(days=1)).strftime(
                DEFAULT_SERVER_DATE_FORMAT)
            variable_attributes = record.product_id.attribute_line_ids.filtered(lambda l: len(l.value_ids) >= 1).mapped(
                'attribute_id')
            variant = record.product_id.attribute_value_ids._variant_name(variable_attributes)
            display_name = variant and "%s (%s)" % (record.name, variant) or record.name

            before_qty, before_value = self.get_before_product(record.product_id, end_date_before)
            income_qty, income_value = self.get_income_product(record.product_id, start_date, end_date)
            outgoing_qty, outgoing_value = self.get_outgoing_product(record.product_id, start_date, end_date)
            scrap_qty, scrap_value = self.get_scrap_product(record.product_id, start_date, end_date)
            add_inventory_qty, add_inventory_value, sub_inventory_qty, sub_inventory_value = self.get_inventory_product(
                record.product_id, start_date, end_date)
            income_return_qty, income_return_value = self.get_outgoing_return_product(record.product_id, start_date,
                                                                                      end_date)
            outgoing_return_qty, outgoing_return_value = self.get_income_return_product(record.product_id, start_date,
                                                                                        end_date)

            after_qty = before_qty + income_qty + add_inventory_qty + income_return_qty - outgoing_qty - sub_inventory_qty - outgoing_return_qty - scrap_qty
            after_value = before_value + income_value + add_inventory_value + income_return_value - outgoing_value - sub_inventory_value - outgoing_return_value - scrap_value
            record.update({
                'display_name': display_name,
                'before_qty': before_qty,
                'before_value': before_value,
                'income_qty': income_qty,
                'income_value': income_value,
                'outgoing_qty': outgoing_qty,
                'outgoing_value': outgoing_value,
                'scrap_qty': scrap_qty,
                'scrap_value': scrap_value,
                'add_inventory_qty': add_inventory_qty,
                'add_inventory_value': add_inventory_value,
                'income_return_qty': income_return_qty,
                'income_return_value': income_return_value,
                'sub_inventory_qty': sub_inventory_qty,
                'sub_inventory_value': sub_inventory_value,
                'outgoing_return_qty': outgoing_return_qty,
                'outgoing_return_value': outgoing_return_value,
                'after_qty': after_qty,
                'after_value': after_value,
            })