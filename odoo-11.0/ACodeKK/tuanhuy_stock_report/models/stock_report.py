# -*- coding: utf-8 -*-
from odoo import models, fields, api
import pytz
import datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT,DEFAULT_SERVER_DATE_FORMAT
from odoo import tools
class stock_inventory_report(models.TransientModel):
    _name = 'stock.check.report.popup'

    date_start      = fields.Date(string='Từ ngày')
    date_to        = fields.Date(string='Đến Ngày')
    type            = fields.Selection([('done','Trạng thái hoàn thành'),('all','Tất cả trạng thái')],string='Loại',required=True,default='done')
    show_all       = fields.Boolean(string='Hiển thị tất cả')

    @api.multi
    def open_stock_report(self):
        move_obj = self.env['stock.move'].sudo()
        result_context = {}
        result_domain = []
        action = self.env.ref('tuanhuy_stock_report.action_stock_check_report').read()[0]

        if self.date_start:
            date_start = self.convert_to_utc(self.env.user, self.date_start)
            result_context.update({'inventory_date_from': date_start})

        if self.date_to:

            date_to = self.convert_to_utc(self.env.user, self.date_to)
            result_context.update({'inventory_date_to': date_to })

        if not self.date_start and not self.date_to:
            result_context.update({'inventory_report': True })
        if self.type == 'done':
            result_domain.append(('state', '=', 'done'))
        else:
            result_domain.append(('state', '!=', 'cancel'))
        result_context.update({'inventory_type': self.type})

        if not self.show_all:
            query = "SELECT DISTINCT product_id from stock_move WHERE "
            if self.type == 'done':
                query += " state = 'done'"
            else:
                query += " state != 'cancel'"
            if self.date_start or self.date_to:
                if self.date_start:
                    query += " AND date >= '%s'" %(self.date_start)
                if self.date_to:
                    query += " AND date <= '%s'" %(self.date_to)

            self.env.cr.execute(query)
            product_ids = [product[0] for product in self.env.cr.fetchall()]
            action['domain'] = [('id','in',product_ids)]
        action['context'] = str(result_context)
        # action['domain'] = str(result_domain)

        return action

    def convert_to_utc(self,user_id, date):
        timezone_tz = 'utc'
        if user_id and user_id.tz:
            timezone_tz = user_id.tz
        else:
            timezone_tz = 'Asia/Ho_Chi_Minh'
        date_start = datetime.datetime.strptime(date, DEFAULT_SERVER_DATE_FORMAT).replace(tzinfo=pytz.timezone(timezone_tz)).astimezone(pytz.utc)
        return date_start.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

class stock_check_report(models.Model):
    _name = 'stock.check.report'
    _auto = False


    product_id      = fields.Many2one('product.product',string='Sản phẩm')
    name            = fields.Char(string='Sản phẩm')
    default_code    = fields.Char(string='Mã nội bộ')
    uom_id     = fields.Many2one('product.uom',string='Đơn vị tính')
    categ_id     = fields.Many2one('product.category',string='Nhóm nội bộ')
    incoming_before_date = fields.Float(string='Nhập đầu kì', compute='compute_inventory_report')
    incoming_after_date = fields.Float(string='Nhập cuối kì', compute='compute_inventory_report')
    incoming_current = fields.Float(string='Nhập', compute='compute_inventory_report')

    outgoing_before_date = fields.Float(string='Xuất đầu kì', compute='compute_inventory_report')
    outgoing_after_date = fields.Float(string='Xuất cuối kì', compute='compute_inventory_report')
    outgoing_current = fields.Float(string='Xuất', compute='compute_inventory_report')

    inventory_before = fields.Float(string='Tồn đầu kì', compute='compute_inventory_report')
    inventory_after = fields.Float(string='Tồn cuối kì', compute='compute_inventory_report')
    inventory_current = fields.Float(string='Tồn kho', compute='compute_inventory_report')

    inventory_forecast = fields.Float(string='Tồn dự báo', compute='compute_inventory_report')
    inventory_value     = fields.Float(string='Giá trị tồn kho', compute='compute_inventory_report')
    before_value     = fields.Float(string='Giá trị đầu kì', compute='compute_inventory_report')
    incoming_current_value     = fields.Float(string='Giá trị nhập', compute='compute_inventory_report')
    outgoing_current_value     = fields.Float(string='Giá trị xuất', compute='compute_inventory_report')

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'stock_check_report')
        self.env.cr.execute(
            """CREATE or REPLACE VIEW stock_check_report as (
            SELECT 
            min(pp.id) as id,
            min(pp.id) as product_id,
            pt.uom_id as uom_id,
            pt.name as name,
            pt.categ_id as categ_id,
            pt.default_code as default_code
            FROM product_product as pp
            INNER JOIN product_template pt ON pt.id = pp.product_tmpl_id
            GROUP BY pp.id,pt.uom_id,pt.name,pt.default_code,pt.categ_id)
            """)

    @api.multi
    def open_stock_move(self):
        for record in self:
            domain = []
            context = self.env.context.copy() or {}
            action = self.env.ref('tuanhuy_stock.stock_picking_line_action').read()[0]
            if context.get('inventory_type', False):
                if context.get('inventory_type', False) == 'done':
                    domain.append(('state', '=', 'done'))
                else:
                    domain.append(('state', '!=', 'cancel'))
            # domain.append(('product_id','in',record.product_id.ids))
            action['domain'] = domain
            action['context'] = {'search_default_product_id': record.product_id.ids, 'search_default_wh_stock': True}
            return action

    @api.multi
    def compute_inventory_report(self):
        context     = self.env.context.copy()
        current_domain      = []
        type_domain      = []
        move_obj    = self.env['stock.move'].sudo()
        wh_stock    = self.env.ref('stock.stock_location_stock')
        date_start  = context.get('inventory_date_from',False)
        date_to     = context.get('inventory_date_to',False)
        before_domain   = []
        after_domain    = []

        if date_start:
            current_domain.append(('date','>=',date_start))
            before_domain = [('date', '<=', date_start)]
        if date_to:
            current_domain.append(('date','<=',date_to))
            after_domain = [('date', '>=', date_to)]
        if context.get('inventory_type', False):
            if context.get('inventory_type', False) == 'done':
                type_domain.append(('state','=','done'))
            else:
                type_domain.append(('state', '!=', 'cancel'))

        incoming_domain = [('location_dest_id','=',wh_stock.id or False)]
        outgoing_domain = [('location_id','=',wh_stock.id or False)]

        for record in self:
            product_domain              = [('product_id','=',record.product_id.id)]
            if date_start:
                record.incoming_before_date = sum(move_obj.search(before_domain + incoming_domain + product_domain  + type_domain).mapped('product_uom_qty'))
                incoming_before_date_val = sum(move_obj.search(before_domain + incoming_domain + product_domain  + type_domain).mapped('quant_ids.inventory_value'))

                record.outgoing_before_date = sum(move_obj.search(before_domain + outgoing_domain + product_domain + type_domain).mapped('product_uom_qty'))
                outgoing_before_date_val = sum(move_obj.search(before_domain + outgoing_domain + product_domain + type_domain).mapped('quant_ids.inventory_value'))
            else:
                record.incoming_before_date = incoming_before_date_val = record.outgoing_before_date = outgoing_before_date_val = 0

            if date_to:
                record.incoming_after_date = sum(move_obj.search(after_domain + incoming_domain + product_domain + type_domain).mapped('product_uom_qty'))
                incoming_after_date_val = sum(move_obj.search(after_domain + incoming_domain + product_domain + type_domain).mapped('quant_ids.inventory_value'))
                record.outgoing_after_date = sum(move_obj.search(after_domain + outgoing_domain + product_domain + type_domain).mapped('product_uom_qty'))
                outgoing_after_date_val = sum(move_obj.search(after_domain + outgoing_domain + product_domain + type_domain).mapped('quant_ids.inventory_value'))
            else:
                record.incoming_after_date = incoming_after_date_val = record.outgoing_after_date = outgoing_after_date_val = 0

            record.incoming_current     = sum(move_obj.search(current_domain+ incoming_domain + product_domain  + type_domain).mapped('product_uom_qty'))
            incoming_current_val     = sum(move_obj.search(current_domain+ incoming_domain + product_domain  + type_domain).mapped('quant_ids.inventory_value'))

            record.outgoing_current     = sum(move_obj.search(current_domain+ outgoing_domain + product_domain  + type_domain).mapped('product_uom_qty'))
            outgoing_current_val     = sum(move_obj.search(current_domain+ outgoing_domain + product_domain  + type_domain).mapped('quant_ids.inventory_value'))

            record.inventory_before     = record.incoming_before_date - record.outgoing_before_date
            record.inventory_current    = record.incoming_current - record.outgoing_current
            record.inventory_after      = record.inventory_before + record.inventory_current + record.incoming_after_date - record.outgoing_after_date

            record.inventory_forecast   = sum(move_obj.search([('state','not in',['draft','cancel'])] + product_domain + incoming_domain).mapped('product_uom_qty')) - sum(move_obj.search([('state','not in',['draft','cancel'])] + product_domain + outgoing_domain).mapped('product_uom_qty'))

            record.before_value      = incoming_before_date_val - outgoing_before_date_val
            record.incoming_current_value      = incoming_current_val
            record.outgoing_current_value      = outgoing_current_val
            record.inventory_value      = record.before_value + incoming_current_val - outgoing_current_val + incoming_after_date_val - outgoing_after_date_val