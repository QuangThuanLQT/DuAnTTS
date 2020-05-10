# -*- coding: utf-8 -*-
import logging
import random

from odoo import api, models, fields, tools, _
from odoo.http import request
from odoo.exceptions import UserError, ValidationError
from odoo.addons import decimal_precision as dp

_logger = logging.getLogger(__name__)


class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    line_child_user = fields.Many2one('res.users', string='Child User Line')

    # @api.model
    # def search(self, args, offset=0, limit=None, order=None, count=False):
    #     if request.env.user.is_children == True:
    #         args.append(('line_child_user', '=', request.env.user.id))
    #     res = super(sale_order_line, self).search(args, offset=offset, limit=limit, order=order, count=count)
    #
    #     return res


class sale_order(models.Model):
    _inherit = 'sale.order'

    # @api.multi
    # def _cart_find_product_line(self, product_id=None, line_id=None, **kwargs):
    #     self.ensure_one()
    #     lines = super(sale_order, self)._cart_find_product_line(product_id, line_id)
    #     if line_id:
    #         return lines
    #     domain = [('id', 'in', lines.ids)]
    #     if request.env.user.is_children == True:
    #         domain.append(('line_child_user', '=', request.env.user.id))
    #     return self.env['sale.order.line'].sudo().search(domain)
    #
    # @api.multi
    # def _website_product_id_change(self, order_id, product_id, qty=0):
    #     values = super(sale_order, self)._website_product_id_change(order_id, product_id, qty=qty)
    #     if request.env.user.is_children == True:
    #         values['line_child_user'] = request.env.user.id
    #     return values
