# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class res_users(models.Model):
    _inherit = 'res.users'

    @api.model
    def search_user_order(self, name):
        user_ids = []
        users = self.search([('name', '=', name)])
        if users:
            user_ids = users.ids
        else:
            self.env.cr.execute("""SELECT users.id, partner.name 
                                    FROM res_users users 
                                    LEFT JOIN res_partner partner ON (users.partner_id = partner.id) 
                                    WHERE UPPER(name) LIKE '%s'""" % ("%" + name.upper() + "%"))
            customers = self.env.cr.fetchall()
            for customer in customers:
                user_ids.append(customer[0])
        return user_ids


class product_product(models.Model):
    _inherit = 'product.product'

    # @api.depends('qty_available', 'virtual_available')
    # def _compute_product(self):
    #     move_obj = self.env['stock.move'].sudo()
    #     dest_location = self.env.ref('stock.stock_location_customers')
    #     for rec in self:
    #         sp_ban_chua_giao = 0
    #         so_ids = self.env['sale.order'].search([('sale_order_return', '=', False), ('state', '=', 'sale')]).filtered(lambda s: s.trang_thai_dh not in ['done', 'cancel'])
    #         line_product = so_ids.mapped('order_line').filtered(lambda line: line.product_id == rec)
    #         for line in line_product:
    #             sp_ban_chua_giao += line.product_uom_qty
    #         rec.sp_ban_chua_giao = sp_ban_chua_giao
    #         line_ids = self.env['sale.order.line'].search(
    #             [('product_id', '=', rec.id), ('order_id.state', 'in', ('draft', 'sent'))])
    #         sp_da_bao_gia = sum(line_ids.mapped('product_uom_qty'))
    #         rec.sp_da_bao_gia = sp_da_bao_gia
    #         rec.sp_co_the_ban = rec.qty_available - rec.sp_ban_chua_giao - rec.sp_da_bao_gia


    @api.model
    def search_product_name(self, name):
        sale_order = []
        order_ids = self.search([('name', '=', name)])
        if order_ids:
            sale_order = order_ids.ids
        else:
            for record in self.search([]).name_get():
                if record[1] and name.lower() in record[1].lower():
                    sale_order.append(record[0])
            self.env.cr.execute("""SELECT pp.id 
                                    FROM product_product pp 
                                    LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
                                    WHERE LOWER(name) LIKE '%s' OR pp.default_code = '%s';""" % (("%" + name.lower() + "%"),name))
            customers = self.env.cr.fetchall()
            for customer in customers:
                sale_order.append(customer[0])
            for attrs in name.split():
                product_ids = self.search([('attribute_value_ids.name', 'like', attrs)])
                for product in product_ids:
                    if product.id not in sale_order:
                        sale_order.append(product.id)
        return sale_order