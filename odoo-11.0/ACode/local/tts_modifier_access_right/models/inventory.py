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

                # TODO group_nv_nganh_hang
                if self.env.user.has_group('tts_modifier_access_right.group_nv_nganh_hang'):
                    menu_list = [
                        'stock.stock_picking_type_menu',
                        'stock.menu_stock_warehouse_mgmt',
                        'stock.menu_routes_config',
                        'tts_api.ems_api_menu_root',
                        'stock.menu_stock_uom_form_action'
                    ]
                    id_list = []
                    for menu in menu_list:
                        menu_id = self.env.ref(menu)
                        if menu_id and menu_id.id in res.ids:
                            id_list.append(menu_id.id)

                    id_list += self.env['ir.ui.menu'].get_list_menu_hide('stock.menu_stock_inventory_control', [
                        'stock.menu_action_inventory_form', 'stock.menu_stock_scrap','tts_modifier_inventory.not_sellable_product_menu'
                    ])
                    id_list += self.env['ir.ui.menu'].get_list_menu_hide('stock.menu_product_in_config_stock', [
                        'stock.menu_product_category_config_stock'
                    ])
                    
                    filter_id = [par.id for par in res if par.id not in id_list]
                    res = self.browse(filter_id)

                # TODO group_ketoan_tonghop
                if self.env.user.has_group('tts_modifier_access_right.group_ketoan_tonghop'):
                    menu_list = [
                        # 'stock.stock_picking_type_menu',
                        'stock.menu_stock_warehouse_mgmt',
                        'stock.menu_stock_config_settings',
                    ]
                    id_list = []
                    for menu in menu_list:
                        menu_id = self.env.ref(menu)
                        if menu_id and menu_id.id in res.ids:
                            id_list.append(menu_id.id)

                    filter_id = [par.id for par in res if par.id not in id_list]
                    res = self.browse(filter_id)

                # TODO group_ketoan_kho
                if self.env.user.has_group('tts_modifier_access_right.group_ketoan_kho'):
                    menu_list = [
                        # 'stock.stock_picking_type_menu',
                        'stock.menu_stock_warehouse_mgmt',
                        'stock.menu_stock_config_settings',
                    ]
                    id_list = []
                    for menu in menu_list:
                        menu_id = self.env.ref(menu)
                        if menu_id and menu_id.id in res.ids:
                            id_list.append(menu_id.id)

                    filter_id = [par.id for par in res if par.id not in id_list]
                    res = self.browse(filter_id)

                # TODO group_ql_kho
                if self.env.user.has_group('tts_modifier_access_right.group_ql_kho'):
                    menu_list = [
                        'stock.menu_product_category_config_stock',
                        'stock.menu_routes_config',
                        'stock.menu_product_in_config_stock',
                        'tts_api.ems_api_menu_root',
                        'delivery.menu_delivery',
                        'stock.menu_stock_uom_form_action'
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

                # TODO group_nv_nhap_hang
                if self.env.user.has_group('tts_modifier_access_right.group_nv_nhap_hang'):
                    menu_list = [
                        'stock.menu_stock_scrap'
                    ]
                    id_list = []
                    for menu in menu_list:
                        menu_id = self.env.ref(menu)
                        if menu_id and menu_id.id in res.ids:
                            id_list.append(menu_id.id)

                    filter_id = [par.id for par in res if par.id not in id_list]
                    res = self.browse(filter_id)

                # TODO group_soan_donggoi
                if self.env.user.has_group('tts_modifier_access_right.group_soan_donggoi'):
                    menu_list = [
                        'stock.menu_stock_scrap'
                    ]
                    id_list = []
                    for menu in menu_list:
                        menu_id = self.env.ref(menu)
                        if menu_id and menu_id.id in res.ids:
                            id_list.append(menu_id.id)

                    filter_id = [par.id for par in res if par.id not in id_list]
                    res = self.browse(filter_id)

                # TODO group_nv_giao_hang
                if self.env.user.has_group('tts_modifier_access_right.group_nv_giao_hang'):
                    menu_list = [
                        'stock.menu_stock_inventory_control',
                        'tuanhuy_stock.stock_picking_line_menu',
                        'stock.menu_warehouse_report',
                        'stock.menu_stock_config_settings',
                    ]
                    id_list = []
                    for menu in menu_list:
                        menu_id = self.env.ref(menu)
                        if menu_id and menu_id.id in res.ids:
                            id_list.append(menu_id.id)

                    filter_id = [par.id for par in res if par.id not in id_list]
                    res = self.browse(filter_id)

                # TODO ACCOUNT MENU

                # TODO group_ketoan_kho
                if self.env.user.has_group('tts_modifier_access_right.group_ketoan_kho'):
                    menu_list = [
                        'account.menu_finance_bank',
                        'account.menu_finance_entries',
                        'account.menu_finance_reports',
                        'account.menu_finance_configuration'
                    ]
                    id_list = []
                    for menu in menu_list:
                        menu_id = self.env.ref(menu)
                        if menu_id and menu_id.id in res.ids:
                            id_list.append(menu_id.id)

                    filter_id = [par.id for par in res if par.id not in id_list]
                    res = self.browse(filter_id)

                # TODO group_ketoan_tonghop
                if self.env.user.has_group('tts_modifier_access_right.group_ketoan_tonghop'):
                    menu_list = [
                        'account.menu_finance_bank',
                        'account.menu_finance_entries',
                        'account.menu_finance_reports',
                        'account.menu_finance_configuration'
                    ]
                    id_list = []
                    for menu in menu_list:
                        menu_id = self.env.ref(menu)
                        if menu_id and menu_id.id in res.ids:
                            id_list.append(menu_id.id)

                    filter_id = [par.id for par in res if par.id not in id_list]
                    res = self.browse(filter_id)

        return res

class product_template_ivenihr(models.Model):
    _inherit = 'product.template'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(product_template_ivenihr, self).fields_view_get(view_id, view_type, toolbar=toolbar,
                                                                 submenu=False)
        doc = etree.XML(res['arch'])

        # TODO group_giam_doc_kd
        #
        # if self.env.user.has_group('tts_modifier_access_right.group_giam_doc_kd'):
        #     if view_type == 'form':
        #         for node in doc.xpath("//form"):
        #             node.set('create', "false")
        #             node.set('modifiers', """{"create": "false"}""")
        #             node.set('delete', "false")
        #             node.set('modifiers', """{"delete": "false"}""")
        #             node.set('edit', "false")
        #             node.set('modifiers', """{"edit": "false"}""")
        #         res['arch'] = etree.tostring(doc)
        #     if view_type == 'tree':
        #         for node in doc.xpath("//tree"):
        #             node.set('create', "false")
        #             node.set('modifiers', """{"create": "false"}""")
        #             node.set('delete', "false")
        #             node.set('modifiers', """{"delete": "false"}""")
        #         res['arch'] = etree.tostring(doc)
        #     if view_type == 'kanban':
        #         for node in doc.xpath("//kanban"):
        #             node.set('create', "false")
        #             node.set('modifiers', """{"create": "false"}""")
        #         res['arch'] = etree.tostring(doc)

        # TODO group_ql_kho

        if self.env.user.has_group('tts_modifier_access_right.group_ql_kho'):
            if view_type == 'form':
                for node in doc.xpath("//form"):
                    node.set('create', "false")
                    node.set('modifiers', """{"create": "false"}""")
                    node.set('delete', "false")
                    node.set('modifiers', """{"delete": "false"}""")
                    node.set('edit', "false")
                    node.set('modifiers', """{"edit": "false"}""")
                for node in doc.xpath("//field[@name='list_price']"):
                    node.set('invisible', "false")
                    node.set('modifiers', """{"invisible": "false"}""")
                for node in doc.xpath("//label[@for='standard_price']"):
                    node.set('invisible', "false")
                    node.set('modifiers', """{"invisible": "false"}""")
                for node in doc.xpath("//field[@name='standard_price']"):
                    node.set('invisible', "false")
                    node.set('modifiers', """{"invisible": "false"}""")
                for node in doc.xpath("//field[@name='cost_root']"):
                    node.set('invisible', "false")
                    node.set('modifiers', """{"invisible": "false"}""")
                res['arch'] = etree.tostring(doc)
            if view_type == 'tree':
                for node in doc.xpath("//tree"):
                    node.set('create', "false")
                    node.set('modifiers', """{"create": "false"}""")
                    node.set('delete', "false")
                    node.set('modifiers', """{"delete": "false"}""")
                res['arch'] = etree.tostring(doc)
            if view_type == 'kanban':
                for node in doc.xpath("//kanban"):
                    node.set('create', "false")
                    node.set('modifiers', """{"create": "false"}""")
                res['arch'] = etree.tostring(doc)

        # TODO group_nv_nhap_hang

        if self.env.user.has_group('tts_modifier_access_right.group_nv_nhap_hang'):
            if view_type == 'form':
                for node in doc.xpath("//form"):
                    node.set('create', "false")
                    node.set('modifiers', """{"create": "false"}""")
                    node.set('delete', "false")
                    node.set('modifiers', """{"delete": "false"}""")
                    node.set('edit', "false")
                    node.set('modifiers', """{"edit": "false"}""")
                for node in doc.xpath("//field[@name='list_price']"):
                    node.set('invisible', "false")
                    node.set('modifiers', """{"invisible": "false"}""")
                for node in doc.xpath("//label[@for='standard_price']"):
                    node.set('invisible', "false")
                    node.set('modifiers', """{"invisible": "false"}""")
                for node in doc.xpath("//field[@name='standard_price']"):
                    node.set('invisible', "false")
                    node.set('modifiers', """{"invisible": "false"}""")
                for node in doc.xpath("//field[@name='cost_root']"):
                    node.set('invisible', "false")
                    node.set('modifiers', """{"invisible": "false"}""")
                res['arch'] = etree.tostring(doc)
            if view_type == 'tree':
                for node in doc.xpath("//tree"):
                    node.set('create', "false")
                    node.set('modifiers', """{"create": "false"}""")
                    node.set('delete', "false")
                    node.set('modifiers', """{"delete": "false"}""")
                res['arch'] = etree.tostring(doc)
            if view_type == 'kanban':
                for node in doc.xpath("//kanban"):
                    node.set('create', "false")
                    node.set('modifiers', """{"create": "false"}""")
                res['arch'] = etree.tostring(doc)

        # TODO group_soan_donggoi

        if self.env.user.has_group('tts_modifier_access_right.group_soan_donggoi'):
            if view_type == 'form':
                for node in doc.xpath("//form"):
                    node.set('create', "false")
                    node.set('modifiers', """{"create": "false"}""")
                    node.set('delete', "false")
                    node.set('modifiers', """{"delete": "false"}""")
                    node.set('edit', "false")
                    node.set('modifiers', """{"edit": "false"}""")
                for node in doc.xpath("//field[@name='list_price']"):
                    node.set('invisible', "false")
                    node.set('modifiers', """{"invisible": "false"}""")
                for node in doc.xpath("//label[@for='standard_price']"):
                    node.set('invisible', "false")
                    node.set('modifiers', """{"invisible": "false"}""")
                for node in doc.xpath("//field[@name='standard_price']"):
                    node.set('invisible', "false")
                    node.set('modifiers', """{"invisible": "false"}""")
                for node in doc.xpath("//field[@name='cost_root']"):
                    node.set('invisible', "false")
                    node.set('modifiers', """{"invisible": "false"}""")
                res['arch'] = etree.tostring(doc)
            if view_type == 'tree':
                for node in doc.xpath("//tree"):
                    node.set('create', "false")
                    node.set('modifiers', """{"create": "false"}""")
                    node.set('delete', "false")
                    node.set('modifiers', """{"delete": "false"}""")
                res['arch'] = etree.tostring(doc)
            if view_type == 'kanban':
                for node in doc.xpath("//kanban"):
                    node.set('create', "false")
                    node.set('modifiers', """{"create": "false"}""")
                res['arch'] = etree.tostring(doc)
        return res

class product_product_ivenihr(models.Model):
    _inherit = 'product.product'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(product_product_ivenihr, self).fields_view_get(view_id, view_type, toolbar=toolbar,
                                                                 submenu=False)
        doc = etree.XML(res['arch'])

        # TODO group_giam_doc_kd

        # if self.env.user.has_group('tts_modifier_access_right.group_giam_doc_kd'):
        #     if view_type == 'form':
        #         for node in doc.xpath("//form"):
        #             node.set('create', "false")
        #             node.set('modifiers', """{"create": "false"}""")
        #             node.set('delete', "false")
        #             node.set('modifiers', """{"delete": "false"}""")
        #             node.set('edit', "false")
        #             node.set('modifiers', """{"edit": "false"}""")
        #         res['arch'] = etree.tostring(doc)
        #     if view_type == 'tree':
        #         for node in doc.xpath("//tree"):
        #             node.set('create', "false")
        #             node.set('modifiers', """{"create": "false"}""")
        #             node.set('delete', "false")
        #             node.set('modifiers', """{"delete": "false"}""")
        #         res['arch'] = etree.tostring(doc)
        #     if view_type == 'kanban':
        #         for node in doc.xpath("//kanban"):
        #             node.set('create', "false")
        #             node.set('modifiers', """{"create": "false"}""")
        #         res['arch'] = etree.tostring(doc)

        # TODO group_ql_kho

        if self.env.user.has_group('tts_modifier_access_right.group_ql_kho'):
            if view_type == 'form':
                for node in doc.xpath("//form"):
                    node.set('create', "false")
                    node.set('modifiers', """{"create": "false"}""")
                    node.set('delete', "false")
                    node.set('modifiers', """{"delete": "false"}""")
                    node.set('edit', "false")
                    node.set('modifiers', """{"edit": "false"}""")
                for node in doc.xpath("//field[@name='lst_price']"):
                    node.set('invisible', "false")
                    node.set('modifiers', """{"invisible": "false"}""")
                for node in doc.xpath("//label[@for='standard_price']"):
                    node.set('invisible', "false")
                    node.set('modifiers', """{"invisible": "false"}""")
                for node in doc.xpath("//field[@name='standard_price']"):
                    node.set('invisible', "false")
                    node.set('modifiers', """{"invisible": "false"}""")
                for node in doc.xpath("//field[@name='cost_root']"):
                    node.set('invisible', "false")
                    node.set('modifiers', """{"invisible": "false"}""")
                res['arch'] = etree.tostring(doc)
            if view_type == 'tree':
                for node in doc.xpath("//tree"):
                    node.set('create', "false")
                    node.set('modifiers', """{"create": "false"}""")
                    node.set('delete', "false")
                    node.set('modifiers', """{"delete": "false"}""")
                res['arch'] = etree.tostring(doc)
            if view_type == 'kanban':
                for node in doc.xpath("//kanban"):
                    node.set('create', "false")
                    node.set('modifiers', """{"create": "false"}""")
                res['arch'] = etree.tostring(doc)

        # TODO group_nv_nhap_hang

        if self.env.user.has_group('tts_modifier_access_right.group_nv_nhap_hang'):
            if view_type == 'form':
                for node in doc.xpath("//form"):
                    node.set('create', "false")
                    node.set('modifiers', """{"create": "false"}""")
                    node.set('delete', "false")
                    node.set('modifiers', """{"delete": "false"}""")
                    node.set('edit', "false")
                    node.set('modifiers', """{"edit": "false"}""")
                for node in doc.xpath("//field[@name='lst_price']"):
                    node.set('invisible', "false")
                    node.set('modifiers', """{"invisible": "false"}""")
                for node in doc.xpath("//label[@for='standard_price']"):
                    node.set('invisible', "false")
                    node.set('modifiers', """{"invisible": "false"}""")
                for node in doc.xpath("//field[@name='standard_price']"):
                    node.set('invisible', "false")
                    node.set('modifiers', """{"invisible": "false"}""")
                for node in doc.xpath("//field[@name='cost_root']"):
                    node.set('invisible', "false")
                    node.set('modifiers', """{"invisible": "false"}""")
                res['arch'] = etree.tostring(doc)
            if view_type == 'tree':
                for node in doc.xpath("//tree"):
                    node.set('create', "false")
                    node.set('modifiers', """{"create": "false"}""")
                    node.set('delete', "false")
                    node.set('modifiers', """{"delete": "false"}""")
                res['arch'] = etree.tostring(doc)
            if view_type == 'kanban':
                for node in doc.xpath("//kanban"):
                    node.set('create', "false")
                    node.set('modifiers', """{"create": "false"}""")
                res['arch'] = etree.tostring(doc)

        # TODO group_soan_donggoi

        if self.env.user.has_group('tts_modifier_access_right.group_soan_donggoi'):
            if view_type == 'form':
                for node in doc.xpath("//form"):
                    node.set('create', "false")
                    node.set('modifiers', """{"create": "false"}""")
                    node.set('delete', "false")
                    node.set('modifiers', """{"delete": "false"}""")
                    node.set('edit', "false")
                    node.set('modifiers', """{"edit": "false"}""")
                for node in doc.xpath("//field[@name='lst_price']"):
                    node.set('invisible', "false")
                    node.set('modifiers', """{"invisible": "false"}""")
                for node in doc.xpath("//label[@for='standard_price']"):
                    node.set('invisible', "false")
                    node.set('modifiers', """{"invisible": "false"}""")
                for node in doc.xpath("//field[@name='standard_price']"):
                    node.set('invisible', "false")
                    node.set('modifiers', """{"invisible": "false"}""")
                for node in doc.xpath("//field[@name='cost_root']"):
                    node.set('invisible', "false")
                    node.set('modifiers', """{"invisible": "false"}""")
                res['arch'] = etree.tostring(doc)
            if view_type == 'tree':
                for node in doc.xpath("//tree"):
                    node.set('create', "false")
                    node.set('modifiers', """{"create": "false"}""")
                    node.set('delete', "false")
                    node.set('modifiers', """{"delete": "false"}""")
                res['arch'] = etree.tostring(doc)
            if view_type == 'kanban':
                for node in doc.xpath("//kanban"):
                    node.set('create', "false")
                    node.set('modifiers', """{"create": "false"}""")
                res['arch'] = etree.tostring(doc)

        return res

class stock_inventory_ivenihr(models.Model):
    _inherit = 'stock.inventory'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(stock_inventory_ivenihr, self).fields_view_get(view_id, view_type, toolbar=toolbar,
                                                                   submenu=False)
        doc = etree.XML(res['arch'])

        # TODO group_nv_nganh_hang

        if self.env.user.has_group('tts_modifier_access_right.group_nv_nganh_hang'):
            if view_type == 'form':
                for node in doc.xpath("//form"):
                    node.set('create', "false")
                    node.set('modifiers', """{"create": "false"}""")
                    node.set('delete', "false")
                    node.set('modifiers', """{"delete": "false"}""")
                    node.set('edit', "false")
                    node.set('modifiers', """{"edit": "false"}""")
                res['arch'] = etree.tostring(doc)
            if view_type == 'tree':
                for node in doc.xpath("//tree"):
                    node.set('create', "false")
                    node.set('modifiers', """{"create": "false"}""")
                    node.set('delete', "false")
                    node.set('modifiers', """{"delete": "false"}""")
                res['arch'] = etree.tostring(doc)

        # TODO group_ketoan_tonghop

        if self.env.user.has_group('tts_modifier_access_right.group_ketoan_tonghop'):
            if view_type == 'form':
                for node in doc.xpath("//form"):
                    node.set('delete', "true")
                    node.set('modifiers', """{"delete": "true"}""")
                res['arch'] = etree.tostring(doc)

        # TODO group_ketoan_kho

        if self.env.user.has_group('tts_modifier_access_right.group_ketoan_kho'):
            if view_type == 'form':
                for node in doc.xpath("//form"):
                    node.set('delete', "true")
                    node.set('modifiers', """{"delete": "true"}""")
                res['arch'] = etree.tostring(doc)
        return res


class stock_scrap_ivenihr(models.Model):
    _inherit = 'stock.scrap'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(stock_scrap_ivenihr, self).fields_view_get(view_id, view_type, toolbar=toolbar,
                                                                   submenu=False)
        doc = etree.XML(res['arch'])

        # TODO group_giam_doc_kd

        if self.env.user.has_group('tts_modifier_access_right.group_nv_nganh_hang'):
            if view_type == 'form':
                for node in doc.xpath("//form"):
                    node.set('create', "false")
                    node.set('modifiers', """{"create": "false"}""")
                    node.set('delete', "false")
                    node.set('modifiers', """{"delete": "false"}""")
                    node.set('edit', "false")
                    node.set('modifiers', """{"edit": "false"}""")
                res['arch'] = etree.tostring(doc)
            if view_type == 'tree':
                for node in doc.xpath("//tree"):
                    node.set('create', "false")
                    node.set('modifiers', """{"create": "false"}""")
                    node.set('delete', "false")
                    node.set('modifiers', """{"delete": "false"}""")
                res['arch'] = etree.tostring(doc)
        return res

class stock_picking_type_ivenihr(models.Model):
    _inherit = 'stock.picking.type'

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if self.env.user.has_group('tts_modifier_access_right.group_nv_giao_hang'):
            domain.append(('code', '=', 'outgoing'))
        elif self.env.user.has_group('tts_modifier_access_right.group_soan_donggoi'):
            location_pack_zone = self.env.ref('stock.location_pack_zone')
            domain += ['|', ('default_location_dest_id', '=', location_pack_zone.id),
                        ('default_location_src_id', '=', location_pack_zone.id)]
        elif self.env.user.has_group('tts_modifier_access_right.group_nv_nhap_hang'):
            location_pack_zone = self.env.ref('stock.location_pack_zone')
            stock_location_stock = self.env.ref('stock.stock_location_stock')
            picking_type_ids = self.search([('code', 'in', ['internal','incoming'])])
            picking_type_ids = picking_type_ids.filtered(lambda l: l.default_location_dest_id != location_pack_zone and l.default_location_src_id != location_pack_zone)
            picking_type_ids = picking_type_ids.filtered(lambda l: l.code == 'incoming' or l.default_location_src_id == stock_location_stock and l.default_location_dest_id == stock_location_stock)
            domain.append(('id', 'in', picking_type_ids.ids))
        elif self.env.user.has_group('tts_modifier_access_right.group_ketoan_kho') or self.env.user.has_group('tts_modifier_access_right.group_ketoan_tonghop'):
            stock_location_stock = self.env.ref('stock.stock_location_stock')
            location_pack_zone = self.env.ref('stock.location_pack_zone')
            picking_type_ids = self.search([('code', 'in', ['internal'])])
            picking_type_ids = picking_type_ids.filtered(lambda l:l.default_location_src_id == stock_location_stock and l.default_location_dest_id not in (stock_location_stock,location_pack_zone))
            domain.append(('id', 'in', picking_type_ids.ids))
        res = super(stock_picking_type_ivenihr, self).search_read(domain=domain, fields=fields, offset=offset,
                                                            limit=limit, order=order)
        return res

class stock_picking_ivenihr(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if self.env.user.has_group('tts_modifier_access_right.group_nv_giao_hang'):
            domain.append(('picking_type_id.code', '=', 'outgoing'))
        elif self.env.user.has_group('tts_modifier_access_right.group_soan_donggoi'):
            location_pack_zone = self.env.ref('stock.location_pack_zone')
            domain += ['|', ('picking_type_id.default_location_dest_id', '=', location_pack_zone.id),
                          ('picking_type_id.default_location_src_id', '=', location_pack_zone.id)]
        elif self.env.user.has_group('tts_modifier_access_right.group_nv_nhap_hang'):
            location_pack_zone = self.env.ref('stock.location_pack_zone')
            stock_location_stock = self.env.ref('stock.stock_location_stock')
            picking_type_ids = self.env['stock.picking.type'].search([('code', 'in', ['internal', 'incoming'])])
            picking_type_ids = picking_type_ids.filtered(lambda
                                                             l: l.default_location_dest_id != location_pack_zone and l.default_location_src_id != location_pack_zone)
            picking_type_ids = picking_type_ids.filtered(lambda l: l.code == 'incoming' or l.default_location_src_id == stock_location_stock and l.default_location_dest_id == stock_location_stock)

            domain.append(('picking_type_id', 'in', picking_type_ids.ids))
        elif self.env.user.has_group('tts_modifier_access_right.group_ketoan_kho') or self.env.user.has_group('tts_modifier_access_right.group_ketoan_tonghop'):
            stock_location_stock = self.env.ref('stock.stock_location_stock')
            location_pack_zone = self.env.ref('stock.location_pack_zone')
            picking_type_ids = self.env['stock.picking.type'].search([('code', 'in', ['internal'])])
            picking_type_ids = picking_type_ids.filtered(lambda l:l.default_location_src_id == stock_location_stock and l.default_location_dest_id not in (location_pack_zone))
            domain.append(('picking_type_id', 'in', picking_type_ids.ids))

        res = super(stock_picking_ivenihr, self).search_read(domain=domain, fields=fields, offset=offset,
                                                            limit=limit, order=order)
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(stock_picking_ivenihr, self).fields_view_get(view_id, view_type, toolbar=toolbar,
                                                                   submenu=False)
        doc = etree.XML(res['arch'])

        # TODO group_soan_donggoi
        if not self.env.user.has_group('tts_modifier_access_right.group_ql_kho') and \
            not self.env.user.has_group('tts_modifier_access_right.group_ketoan_kho') and \
            not self.env.user.has_group('tts_modifier_access_right.group_ketoan_tonghop') and self._uid != 1:
            if view_type == 'form':
                for node in doc.xpath("//form"):
                    node.set('create', "false")
                    node.set('modifiers', """{"create": "false"}""")
                res['arch'] = etree.tostring(doc)
            if view_type == 'tree':
                for node in doc.xpath("//tree"):
                    node.set('create', "false")
                    node.set('modifiers', """{"create": "false"}""")
                res['arch'] = etree.tostring(doc)

        # TODO group_soan_donggoi
        if self.env.user.has_group('tts_modifier_access_right.group_soan_donggoi'):
            if view_type == 'form':
                for node in doc.xpath("//button[@name='action_cancel']"):
                    node.set('attrs', "{'invisible':[(True,'=',True)]}")
                    node.set('invisible', "true")
                    node.set('modifiers', """{"invisible": "true"}""")
                res['arch'] = etree.tostring(doc)

        # TODO group_truong_kd
        if self.env.user.has_group('tts_modifier_access_right.group_truong_kd'):
            if view_type == 'form':
                for node in doc.xpath("//form"):
                    node.set('edit', "false")
                    node.set('modifiers', """{"edit": "false"}""")
                res['arch'] = etree.tostring(doc)
        # TODO group_nv_nhap_hang
        if self.env.user.has_group('tts_modifier_access_right.group_nv_nhap_hang'):
            if view_type == 'form':
                for node in doc.xpath("//button[@name='action_cancel']"):
                    node.set('attrs', "{'invisible':[(True,'=',True)]}")
                    node.set('invisible', "true")
                    node.set('modifiers', """{"invisible": "true"}""")
                res['arch'] = etree.tostring(doc)
        # TODO group_nv_giao_hang
        if self.env.user.has_group('tts_modifier_access_right.group_nv_giao_hang'):
            if view_type == 'form':
                for node in doc.xpath("//button[@name='action_cancel']"):
                    node.set('attrs', "{'invisible':[(True,'=',True)]}")
                    node.set('invisible', "true")
                    node.set('modifiers', """{"invisible": "true"}""")
                res['arch'] = etree.tostring(doc)
        # TODO group_ql_kho
        if self.env.user.has_group('tts_modifier_access_right.group_ql_kho'):
            if view_type == 'form':
                for node in doc.xpath("//button[@name='action_cancel']"):
                    node.set('attrs', "{'invisible':[(True,'=',True)]}")
                    node.set('invisible', "true")
                    node.set('modifiers', """{"invisible": "true"}""")
                res['arch'] = etree.tostring(doc)
        return res