# -*- coding: utf-8 -*-

from odoo import models, fields, api
from lxml import etree
from odoo import SUPERUSER_ID
import types


class IrUiMenu_inventory_ihr(models.Model):
    _inherit = 'ir.ui.menu'

    def check_action(self, rec, action_list):
        action_ids = []
        for action in action_list:
            action_id = self.env.ref(action)
            if action_id:
                action_ids.append(action_id.id)
        if rec._context and rec._context.get('params') and rec._context.get('params').get(
                'action') in action_ids:
            return True
        else:
            return False

    def get_list_menu_hide(self, menu_parent, not_include_menu):
        menu_parent_id = self.env.ref(menu_parent)
        list_menu_not_inc = []
        for menu in not_include_menu:
            menu_id = self.env.ref(menu)
            if menu_id:
                list_menu_not_inc.append(menu_id.id)
        list_menu_hide = self.with_context(search_menu=True).env['ir.ui.menu'].search(
            [('parent_id', '=', menu_parent_id.id), ('id', 'not in', list_menu_not_inc)]).ids
        return list_menu_hide

    def search(self, args, offset=0, limit=None, order=None, count=False):
        res = super(IrUiMenu_inventory_ihr, self).search(args, offset, limit, order, count=count)
        if 'search_menu' not in self._context:
            if type(res) != int:
                pass
                # TODO INVENTORY MENU

                # TODO group_nv_kho
                if self.env.user.has_group('prinizi_modifier_accessright.group_nv_kho'):
                    menu_list = [
                        'stock.menu_product_category_config_stock',
                        'stock.menu_routes_config',
                        'stock.menu_product_in_config_stock',
                        'tts_api.ems_api_menu_root',
                        'delivery.menu_delivery',
                        'stock.menu_stock_uom_form_action',
                        'account.menu_finance',
                    ]
                    id_list = []
                    for menu in menu_list:
                        menu_id = self.env.ref(menu)
                        if menu_id and menu_id.id in res.ids:
                            id_list.append(menu_id.id)
                    id_list += self.env['ir.ui.menu'].get_list_menu_hide('stock.menu_warehouse_config', [
                        'stock.menu_action_location_form', 'tts_modifier_inventory.package_size_menu',
                    ])

                    filter_id = [par.id for par in res if par.id not in id_list]
                    res = self.browse(filter_id)

        return res

class stock_picking_type_ivenihr(models.Model):
    _inherit = 'stock.picking.type'

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if self.env.user.has_group('prinizi_modifier_accessright.group_nv_kho'):
            domain.append(('picking_type', 'in', ['pick', 'pack', 'delivery', 'reciept', 'internal',
                            'produce_name', 'produce_image', 'print', 'kcs1', 'kcs2']))

        res = super(stock_picking_type_ivenihr, self).search_read(domain=domain, fields=fields, offset=offset,
                                                             limit=limit, order=order)
        return res