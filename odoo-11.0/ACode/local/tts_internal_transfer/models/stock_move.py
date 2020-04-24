# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import StringIO
import xlsxwriter
from lxml import etree
import pytz


class stock_move(models.Model):
    _inherit = 'stock.move'

    @api.multi
    @api.constrains('location_id', 'product_id')
    def _check_currency_and_amount(self):
        for line in self:
            if line.location_id and line.picking_type_id.warehouse_id and line.location_id == line.picking_type_id.warehouse_id.lot_stock_id:
                if line.picking_id.is_orther_picking == True:
                    if line.product_uom_qty > line.product_id.sp_co_the_ban:
                        raise ValidationError(_(
                            "Bạn định dịch chuyển %s sản phẩm %s nhưng chỉ có %s sản phẩm có thể đặt hàng!." % (
                            line.product_uom_qty, line.product_id.display_name, line.product_id.sp_co_the_ban)))