# -*- coding: utf-8 -*-
from odoo import models, fields, api
import pytz
from datetime import datetime, timedelta


# from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
# from odoo import tools
# import base64
# import StringIO
# import xlsxwriter
# from xlrd import open_workbook


class stock_inventory_report(models.TransientModel):
    _name = 'stock.inventory.report.popup'

    date_start = fields.Date(string='Từ ngày', required=True)
    date_end = fields.Date(string='Đến Ngày', required=True)
    type = fields.Selection(
        [('all', 'Tất cả'), ('active', 'Hàng đang kinh doanh'), ('unactive', 'Hàng ngừng kinh doanh')],
        string='Lựa chọn hiển thị', default='all', required=True)

    @api.multi
    def open_stock_report(self):
        move_obj = self.env['stock.move'].sudo()
        result_context = {}
        action = self.env.ref('tts_inventory_report.action_stock_inventory_report').read()[0]

        if self.date_start:
            result_context.update({'date_start': self.date_start})

        if self.date_end:
            result_context.update({'date_end': self.date_end})
        where_str = ''
        if self.type == 'all':
            where_str = "WHERE (active = True and archived_date is null and unarchived_date is null and create_date <= '%s') " \
                        "OR (active = False and archived_date > '%s')" \
                        "OR (active = True and unarchived_date <= '%s')" \
                        "OR (active = True AND unarchived_date >= '%s' and unarchived_date <= '%s') " \
                        "OR (active = False AND archived_date >= '%s' and archived_date <= '%s')" \
                        "OR (id in (select product_id from stock_move where date >= '%s' and date <= '%s'))" \
                        % (self.date_end, self.date_end, self.date_end, self.date_start, self.date_end, self.date_start,
                           self.date_end, (self.date_start + ' 00:00:00'), (self.date_end + ' 23:59:59'))
        elif self.type == 'active':
            where_str = "WHERE active = True AND unarchived_date <= '%s'" % (self.date_end)
        elif self.type == 'unactive':
            where_str = "WHERE (active = False AND archived_date >= '%s' and archived_date <= '%s')" % (
                self.date_start, self.date_end)

        query = """SELECT id FROM product_product %s order by default_code;""" % (where_str)
        self.env.cr.execute(query)
        product_ids = self.env.cr.fetchall()
        ids = []
        for product in product_ids:
            if len(product) > 0:
                ids.append(product[0])
        action['domain'] = [('id', 'in', ids)]
        action['context'] = (result_context)

        return action

    def convert_to_utc(self, user_id, date):
        timezone_tz = 'utc'
        if user_id and user_id.tz:
            timezone_tz = user_id.tz
        else:
            timezone_tz = 'Asia/Ho_Chi_Minh'
        date_start = datetime.datetime.strptime(date, DEFAULT_SERVER_DATE_FORMAT).replace(
            tzinfo=pytz.timezone(timezone_tz)).astimezone(pytz.utc)
        return date_start.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

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

    def get_before_incoming_qty(self, product_id):
        state = 'done'
        move_type = 'incoming'
        query = """select sum(sm.product_uom_qty) as product_uom_qty from stock_move as sm \
                  JOIN stock_picking_type as spt ON spt.id = sm.picking_type_id \
                  where sm.date < %s and spt.code = %s \
                  and sm.product_id = %s and sm.state = %s
                  """
        date_start = str(self.date_start) + ' 00:00:00'
        params = (date_start, move_type, product_id.id, state)

        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        value = 0
        for line in result:
            if line.get('product_uom_qty', False):
                value = line.get('product_uom_qty')
        return value

    def get_before_outgoing_qty(self, product_id):
        state = 'done'
        move_type = 'outgoing'
        query = """select sum(sm.product_uom_qty) as product_uom_qty from stock_move as sm \
                  JOIN stock_picking_type as spt ON spt.id = sm.picking_type_id \
                  where sm.date < %s and spt.code = %s \
                  and sm.product_id = %s and sm.state = %s
                  """
        date_start = str(self.date_start) + ' 00:00:00'
        params = (date_start, move_type, product_id.id, state)

        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        value = 0
        for line in result:
            if line.get('product_uom_qty', False):
                value = line.get('product_uom_qty')
        return value

    ## Todo get before value

    def get_income_before_product(self, product_id, end_date, start_date=None):
        state = 'done'
        location_procurement = self.env.ref('stock.location_procurement')
        stock_location_stock = self.env.ref('stock.stock_location_stock')
        end_date = end_date + ' 23:59:59'

        query = """select sum(sm.product_uom_qty) as product_uom_qty, sum(sm.product_uom_qty * sm.price_unit) as total from stock_move as sm \
                  JOIN stock_picking_type as spt ON spt.id = sm.picking_type_id \
                  JOIN product_product as pp ON pp.id = sm.product_id \
                  JOIN stock_picking as sp ON sp.id = sm.picking_id \
                  where sm.date <= %s and sm.product_id = %s \
                  and sm.location_id = %s and sm.location_dest_id = %s \
                  and sm.state = %s and sp.check_return_picking = FALSE \
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
            if line.get('total', False):
                income_value += line.get('total', 0)
        return income_qty, income_value

    def get_outgoing_before_product(self, product_id, end_date, start_date=None):
        state = 'done'
        move_type = 'outgoing'
        end_date = end_date + ' 23:59:59'
        condition = ''
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
        condition = ''
        query = """select sm.product_uom_qty, pl.price_unit, sm.date from stock_move as sm \
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

        return income_qty, income_value

    def get_outgoing_return_before_product(self, product_id, end_date, start_date=None):
        state = 'done'
        move_type = 'incoming'
        end_date = end_date + ' 23:59:59'
        condition = ''

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
                  and sm.state = %s and sp.check_return_picking = TRUE
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
        condition = ''
        query = """
            select sm.product_uom_qty, sm.date from stock_move as sm
            where sm.date <= %s and sm.product_id = %s \
            and sm.scrapped = TRUE and sm.state = %s \
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
        condition = ''

        add_inventory_qty = add_inventory_value = sub_inventory_qty = sub_inventory_value = 0

        sql_add = """SELECT sm.product_uom_qty, sm.date from stock_move as sm \
                    where sm.date <= %s and sm.product_id = %s and sm.state = %s \
                    and sm.location_id = %s and sm.location_dest_id = %s \
                    and sm.inventory_id is not null \
                  """

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
                    and sm.inventory_id is not null \
                  """
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

    ## Todo get report vale

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

    def get_income_product(self, product_id, picking_purchase_ids=None):
        state = 'done'
        location_procurement = self.env.ref('stock.location_procurement')
        stock_location_stock = self.env.ref('stock.stock_location_stock')
        move_type = 'incoming'
        query = """select sum(sm.product_uom_qty) as product_uom_qty, sum(sm.product_uom_qty * sm.price_unit) as total from stock_move as sm \
                  JOIN stock_picking_type as spt ON spt.id = sm.picking_type_id \
                  JOIN product_product as pp ON pp.id = sm.product_id \
                  JOIN stock_picking as sp ON sp.id = sm.picking_id \
                  where sm.date >= %s and sm.date <= %s and sm.product_id = %s \
                  and sm.location_id = %s and sm.location_dest_id = %s \
                  and sm.state = %s and sp.check_return_picking = FALSE;
                  """

        start_date = str(self.date_start) + ' 00:00:00'
        end_date = str(self.date_end) + ' 23:59:59'

        params = (start_date, end_date, product_id.id, location_procurement.id, stock_location_stock.id, state)

        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        income_qty = income_value = 0
        for line in result:
            if line.get('product_uom_qty', False):
                income_qty += line.get('product_uom_qty')
            if line.get('total', False):
                income_value += line.get('total', 0)
        return income_qty, income_value

    def get_outgoing_product(self, product_id, picking_sale_ids=None):
        state = 'done'
        move_type = 'outgoing'

        query = """select sm.product_uom_qty, sm.date from stock_move as sm \
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
        start_date = str(self.date_start) + ' 00:00:00'
        end_date = str(self.date_end) + ' 23:59:59'

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

    def get_income_return_product(self, product_id, picking_purchase_ids=None):
        state = 'done'
        move_type = 'outgoing'
        query = """select sm.product_uom_qty, pl.price_unit, sm.date from stock_move as sm \
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
        start_date = str(self.date_start) + ' 00:00:00'
        end_date = str(self.date_end) + ' 23:59:59'

        params = (start_date, end_date, move_type, product_id.id, state)

        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        income_qty = income_value = 0
        for line in result:
            if line.get('product_uom_qty', False):
                income_qty += line.get('product_uom_qty')
                price = product_id.get_history_price(product_id.company_id.id, line.get('date', False))
                income_value += price * line.get('product_uom_qty', 0)

        return income_qty, income_value

    def get_outgoing_return_product(self, product_id, picking_sale_ids=None):
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

        start_date = str(self.date_start) + ' 00:00:00'
        end_date = str(self.date_end) + ' 23:59:59'

        params = (start_date, end_date, product_id.id, location_procurement.id, tuple(location_dest_list), state)

        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        outgoing_qty = outgoing_value = 0
        for line in result:
            if line.get('product_uom_qty', False):
                outgoing_qty += line.get('product_uom_qty')
                # price = product_id.get_history_price(product_id.company_id.id, line.get('date', False))
                outgoing_value += line.get('product_uom_qty', 0) * line.get('amount_cost_sale', 0)
        return outgoing_qty, outgoing_value

    def get_scrap_product(self, product_id):
        state = 'done'
        query = """
            select sm.product_uom_qty, sm.date from stock_move as sm
            where sm.date >= %s and sm.date <= %s and sm.product_id = %s \
            and sm.scrapped = TRUE and sm.state = %s
        """
        start_date = str(self.date_start) + ' 00:00:00'
        end_date = str(self.date_end) + ' 23:59:59'
        params = (start_date, end_date, product_id.id, state)
        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        scrap_qty = scrap_value = 0
        for line in result:
            if line.get('product_uom_qty', False):
                scrap_qty += line.get('product_uom_qty')
                price = product_id.get_history_price(product_id.company_id.id, line.get('date'))
                scrap_value += line.get('product_uom_qty') * price

        return scrap_qty, scrap_value

    def get_inventory_product(self, product_id):
        stock_location_stock = self.env.ref('stock.stock_location_stock')
        location_inventory = self.env.ref('stock.location_inventory')
        state = 'done'
        start_date = str(self.date_start) + ' 00:00:00'
        end_date = str(self.date_end) + ' 23:59:59'

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

        return add_inventory_qty, add_inventory_value, sub_inventory_qty, sub_inventory_value

    def get_data(self):

        end_date_before = (
                datetime.strptime(self.date_start, DEFAULT_SERVER_DATE_FORMAT) - timedelta(days=1)).strftime(
            DEFAULT_SERVER_DATE_FORMAT)

        data = []
        where_str = ''
        if self.type == 'all':
            where_str = "WHERE (active = True and archived_date is null and unarchived_date is null and create_date <= '%s') " \
                        "OR (active = False and archived_date > '%s')" \
                        "OR (active = True and unarchived_date <= '%s')" \
                        "OR (active = True AND unarchived_date >= '%s' and unarchived_date <= '%s') " \
                        "OR (active = False AND archived_date >= '%s' and archived_date <= '%s')" \
                        "OR (id in (select product_id from stock_move where date >= '%s' and date <= '%s'))" \
                        % (self.date_end, self.date_end, self.date_end, self.date_start, self.date_end, self.date_start,
                           self.date_end, (self.date_start + ' 00:00:00'), (self.date_end + ' 23:59:59'))
            # where_str = "Where id = 58926"
        elif self.type == 'active':
            where_str = "WHERE active = True AND unarchived_date <= '%s'" % (self.date_end)
        elif self.type == 'unactive':
            where_str = "WHERE (active = False AND archived_date >= '%s' and archived_date <= '%s')" % (
                self.date_start, self.date_end)
        query = """SELECT id FROM product_product %s order by default_code;""" % (where_str)
        self.env.cr.execute(query)
        product_ids = self.env.cr.fetchall()
        for product in product_ids:
            product_data = {}
            if product[0]:
                product_id = self.env['product.product'].browse(product[0])
                variable_attributes = product_id.attribute_line_ids.filtered(
                    lambda l: len(l.value_ids) >= 1).mapped(
                    'attribute_id')
                variant = product_id.attribute_value_ids._variant_name(variable_attributes)
                product_name = variant and "%s (%s)" % (product_id.name, variant) or product_id.name

                before_qty, before_value = self.get_before_product(product_id, end_date_before)
                income_qty, income_value = self.get_income_product(product_id)
                outgoing_qty, outgoing_value = self.get_outgoing_product(product_id)
                scrap_qty, scrap_value = self.get_scrap_product(product_id)
                add_inventory_qty, add_inventory_value, sub_inventory_qty, sub_inventory_value = self.get_inventory_product(
                    product_id)
                income_return_qty, income_return_value = self.get_outgoing_return_product(product_id)
                outgoing_return_qty, outgoing_return_value = self.get_income_return_product(product_id)

                after_qty = before_qty + income_qty + add_inventory_qty + income_return_qty - outgoing_qty - sub_inventory_qty - outgoing_return_qty - scrap_qty
                after_value = before_value + income_value + add_inventory_value + income_return_value - outgoing_value - sub_inventory_value - outgoing_return_value - scrap_value

                product_data.update({
                    'product_name': product_name,
                    'default_code': product_id.default_code,
                    'categ_id': product_id.categ_id.display_name,
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
                    'after_value': after_value
                })
            if product_data:
                data.append(product_data)
        return data

    @api.multi
    def export_data(self):
        data = self.get_data()
        len_data = len(data)
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Bao Cao Ton Kho')
        bold = workbook.add_format({'bold': True})
        merge_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': '16'})
        header_title = workbook.add_format({'bold': False, 'align': 'center', 'valign': 'vcenter', 'font_size': '11'})
        header_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        header_bold_number = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'right', 'valign': 'vcenter'})
        header_bold_number.set_num_format('#,##0')
        body_bold = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'right', 'valign': 'vcenter'})
        body_bold_number.set_num_format('#,##0')
        back_color = 'A2:U2'
        date_start = datetime.strptime(self.date_start, DEFAULT_SERVER_DATE_FORMAT).strftime('%d-%m-%Y')
        date_end = datetime.strptime(self.date_end, DEFAULT_SERVER_DATE_FORMAT).strftime('%d-%m-%Y')
        worksheet.merge_range(back_color, "BÁO CÁO NHẬP XUẤT TỒN CHI TIẾT", merge_format)
        worksheet.merge_range(2, 0, 2, 20, "Từ ngày: %s Đến ngày : %s" % (date_start, date_end), header_title)
        worksheet.merge_range(3, 0, 3, 20, "Ngày tạo báo cáo: %s" % datetime.now().date().strftime('%d-%m-%Y'),
                              header_title)

        worksheet.set_column('A:A', 30)
        worksheet.set_column('B:B', 12)
        worksheet.set_column('C:C', 40)
        worksheet.set_column('D:D', 12)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 12)
        worksheet.set_column('G:G', 20)
        worksheet.set_column('H:H', 12)
        worksheet.set_column('I:I', 20)
        worksheet.set_column('J:J', 12)
        worksheet.set_column('K:K', 20)
        worksheet.set_column('L:L', 12)
        worksheet.set_column('M:M', 20)
        worksheet.set_column('N:N', 12)
        worksheet.set_column('O:O', 20)
        worksheet.set_column('P:P', 12)
        worksheet.set_column('Q:Q', 20)
        worksheet.set_column('R:R', 12)
        worksheet.set_column('S:S', 20)
        worksheet.set_column('T:T', 12)
        worksheet.set_column('U:U', 20)
        worksheet.set_column('V:V', 12)

        row = 5
        summary_header = ['Nhóm hàng', 'Mã hàng', 'Tên hàng', 'Tồn đầu kì', 'Giá trị đầu kì', 'Nhập NCC',
                          'Giá trị nhập NCC', 'Nhập kiểm tăng', 'Giá trị nhập kiểm tăng', 'Nhập trả',
                          'Giá trị nhập trả', 'Xuất bán', 'Giá trị xuất bán', 'Xuất hủy', 'Giá trị xuất hủy',
                          'Xuất trả', 'Giá trị xuất trả', 'Xuất kiểm', 'Giá trị xuất kiểm', 'Tồn cuối kì',
                          'Giá trị cuối kì']

        [worksheet.write(row, header_cell, summary_header[header_cell], header_bold_color) for header_cell in
         range(0, len(summary_header)) if summary_header[header_cell]]

        row += 1
        summary_header_2 = ['D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L',
                            'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U']
        [worksheet.write(row, header_cell + 3, "=SUM(%s%s:%s%s)" % (
            summary_header_2[header_cell], row + 2, summary_header_2[header_cell], row + 1 + len_data),
                         header_bold_number) for
         header_cell in range(0, len(summary_header_2)) if summary_header_2[header_cell]]

        row += 1

        for line in data:
            worksheet.write(row, 0, line.get('categ_id'), body_bold)
            worksheet.write(row, 1, line.get('default_code'), body_bold)
            worksheet.write(row, 2, line.get('product_name'), body_bold)
            worksheet.write(row, 3, line.get('before_qty'), body_bold_number)
            worksheet.write(row, 4, line.get('before_value'), body_bold_number)
            worksheet.write(row, 5, line.get('income_qty'), body_bold_number)
            worksheet.write(row, 6, line.get('income_value'), body_bold_number)
            worksheet.write(row, 7, line.get('add_inventory_qty'), body_bold_number)
            worksheet.write(row, 8, line.get('add_inventory_value'), body_bold_number)
            worksheet.write(row, 9, line.get('income_return_qty'), body_bold_number)
            worksheet.write(row, 10, line.get('income_return_value'), body_bold_number)
            worksheet.write(row, 11, line.get('outgoing_qty'), body_bold_number)
            worksheet.write(row, 12, line.get('outgoing_value'), body_bold_number)
            worksheet.write(row, 13, line.get('scrap_qty'), body_bold_number)
            worksheet.write(row, 14, line.get('scrap_value'), body_bold_number)
            worksheet.write(row, 15, line.get('outgoing_return_qty'), body_bold_number)
            worksheet.write(row, 16, line.get('outgoing_return_value'), body_bold_number)
            worksheet.write(row, 17, line.get('sub_inventory_qty'), body_bold_number)
            worksheet.write(row, 18, line.get('sub_inventory_value'), body_bold_number)
            worksheet.write(row, 19, line.get('after_qty'), body_bold_number)
            worksheet.write(row, 20, line.get('after_value'), body_bold_number)
            row += 1

        workbook.close()
        output.seek(0)
        name = 'Baocaotonkho_%s_%s.xlsx' % (self.date_start, self.date_end)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create(
            {'name': name, 'datas_fname': name, 'datas': result})
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        return {"type": "ir.actions.act_url",
                "url": str(download_url)}

    ## TODO update data

    def check_by_partner(self):
        for order in self.env['sale.order'].search([('sale_order_return', '=', True)]):
            for picking in order.picking_ids:
                picking.check_return_picking = True

    def check_by_partner_report(self):
        state = 'done'
        location_procurement = self.env.ref('stock.location_procurement')
        stock_location_stock = self.env.ref('stock.stock_location_stock')
        start_date = str(self.date_start) + ' 00:00:00'
        end_date = str(self.date_end) + ' 23:59:59'
        move_type = 'incoming'

        partner_sql = """select DISTINCT sm.partner_id from stock_move as sm \
                          JOIN stock_picking as sp ON sp.id = sm.picking_id \
                          where sm.date >= %s and sm.date <= %s \
                          and sm.location_id = %s and sm.location_dest_id = %s \
                          and sm.state = %s and sp.check_return_picking = FALSE;
                          """
        params_partner = (start_date, end_date, location_procurement.id, stock_location_stock.id, state)
        self.env.cr.execute(partner_sql, params_partner)
        result_partner = self.env.cr.dictfetchall()
        for partner in result_partner:
            partner_id = self.env['res.partner'].browse(partner.get('partner_id'))
            query = """select sm.origin, sm.product_uom_qty, sm.price_unit from stock_move as sm \
                              JOIN stock_picking_type as spt ON spt.id = sm.picking_type_id \
                              JOIN product_product as pp ON pp.id = sm.product_id \
                              JOIN stock_picking as sp ON sp.id = sm.picking_id \
                              where sm.date >= %s and sm.date <= %s and sm.partner_id = %s \
                              and sm.location_id = %s and sm.location_dest_id = %s \
                              and sm.state = %s and sp.check_return_picking = FALSE;
                              """

            params = (start_date, end_date, partner_id.id, location_procurement.id, stock_location_stock.id, state)

            self.env.cr.execute(query, params)
            result = self.env.cr.dictfetchall()
            income_qty = income_value = 0
            for line in result:
                print
                "%s" % line.get('origin')
                if line.get('product_uom_qty', False):
                    income_qty += line.get('product_uom_qty')
                if line.get('price_unit', False):
                    income_value += line.get('price_unit', 0) * line.get('product_uom_qty', 0)
            print
            "%s, %s, %s" % (partner_id.ref, income_qty, income_value)

    def update_amount_cost_sale(self):
        domain = [
            ('location_id.usage', '=', 'procurement'),
            ('location_dest_id.usage', '=', 'internal'),
            ('state', '=', 'done'),
        ]
        move_ids = self.env['stock.move'].search(domain, order='date DESC')
        for move in move_ids:
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
                amount_cost_sale = move.product_id.get_history_price(move.company_id.id, date_order)
                move.write({'amount_cost_sale': amount_cost_sale})
