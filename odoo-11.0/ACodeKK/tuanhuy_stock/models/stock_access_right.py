# -*- coding: utf-8 -*-

from openerp import api, models, fields
from lxml import etree


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    def search(self, args, offset=0, limit=None, order=None, count=False):
        res = super(IrUiMenu, self).search(args, offset, limit, order, count=count)
        if self.env.user.has_group('tuanhuy_stock.user_stock_only_read'):
            menu_hr_expense = self.env['ir.model.data'].get_object_reference('hr_expense', 'menu_hr_expense_root')
            employee_list_my = self.env['ir.model.data'].get_object_reference('hr', 'menu_open_view_employee_list_my')
            menu_stock_warehouse = self.env['ir.model.data'].get_object_reference('stock', 'menu_stock_warehouse_mgmt')
            product_product_menu = self.env['ir.model.data'].get_object_reference('stock', 'product_product_menu')
            menu_action_inventory = self.env['ir.model.data'].get_object_reference('stock',
                                                                                   'menu_action_inventory_form')
            stock_picking_type_menu = self.env['ir.model.data'].get_object_reference('stock', 'stock_picking_type_menu')
            menu_product_variant = self.env['ir.model.data'].get_object_reference('modifier_product', 'menu_product_variant_config_stock_barcode')
            filter = []
            filter.append(menu_hr_expense[1])
            filter.append(employee_list_my[1])
            filter.append(menu_stock_warehouse[1])
            filter.append(product_product_menu[1])
            filter.append(menu_action_inventory[1])
            filter.append(stock_picking_type_menu[1])
            filter.append(menu_product_variant[1])
            remove_partner = [par.id for par in res if par.id not in filter]
            res = self.browse(remove_partner)
        return res

class product_group(models.Model):
    _inherit = "product.group"

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(product_group, self).fields_view_get(view_id=view_id, view_type=view_type,
                                                       toolbar=toolbar, submenu=submenu)
        if self.env.user.has_group('tuanhuy_stock.user_stock_only_read'):
            if view_type in 'tree':
                doc = etree.XML(res['arch'], parser=None, base_url=None)
                first_node = doc.xpath("//tree")[0]
                first_node.set('create', 'false')
                first_node.set('delete', 'false')
                res['arch'] = etree.tostring(doc)
            if view_type in 'form':
                doc = etree.XML(res['arch'], parser=None, base_url=None)
                second_node = doc.xpath("//form")[0]
                second_node.set('create', 'false')
                second_node.set('edit', 'false')
                second_node.set('delete', 'false')
                res['arch'] = etree.tostring(doc)
        return res

class product_brand_name(models.Model):
    _inherit = "brand.name"

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(product_brand_name, self).fields_view_get(view_id=view_id, view_type=view_type,
                                                       toolbar=toolbar, submenu=submenu)
        if self.env.user.has_group('tuanhuy_stock.user_stock_only_read'):
            if view_type in 'tree':
                doc = etree.XML(res['arch'], parser=None, base_url=None)
                first_node = doc.xpath("//tree")[0]
                first_node.set('create', 'false')
                first_node.set('delete', 'false')
                res['arch'] = etree.tostring(doc)
            if view_type in 'form':
                doc = etree.XML(res['arch'], parser=None, base_url=None)
                second_node = doc.xpath("//form")[0]
                second_node.set('create', 'false')
                second_node.set('edit', 'false')
                second_node.set('delete', 'false')
                res['arch'] = etree.tostring(doc)
        return res

class product_group_sale(models.Model):
    _inherit = "product.group.sale"

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(product_group_sale, self).fields_view_get(view_id=view_id, view_type=view_type,
                                                       toolbar=toolbar, submenu=submenu)
        if self.env.user.has_group('tuanhuy_stock.user_stock_only_read'):
            if view_type in 'tree':
                doc = etree.XML(res['arch'], parser=None, base_url=None)
                first_node = doc.xpath("//tree")[0]
                first_node.set('create', 'false')
                first_node.set('delete', 'false')
                res['arch'] = etree.tostring(doc)
            if view_type in 'form':
                doc = etree.XML(res['arch'], parser=None, base_url=None)
                second_node = doc.xpath("//form")[0]
                second_node.set('create', 'false')
                second_node.set('edit', 'false')
                second_node.set('delete', 'false')
                res['arch'] = etree.tostring(doc)
        return res