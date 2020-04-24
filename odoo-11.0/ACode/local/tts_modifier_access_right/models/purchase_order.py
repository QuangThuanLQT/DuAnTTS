# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import SUPERUSER_ID
import types
from lxml import etree
from odoo.exceptions import UserError


class purchase_order(models.Model):
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
        res = super(purchase_order, self).search(args, offset, limit, order, count=count)
        if 'search_menu' not in self._context:
            if type(res) != int:

                # TODO PURCHASE MENU

                # # TODO group_giam_doc_kd
                if self.env.user.has_group('tts_modifier_access_right.group_giam_doc_kd'):
                    menu_list = [
                        'tuanhuy_purchase.purchase_order_line_menu',
                        'tuanhuy_purchase.purchase_order_summaries_menu_parent',
                        'tuanhuy_import_sale_purchase.import_purchase_order_menu_parent',
                        'tuanhuy_purchase.purchase_order_line_return_menu',
                        'purchase.menu_action_picking_tree_in_move',
                        'purchase.menu_purchase_general_settings',
                    ]
                    id_list = []
                    for menu in menu_list:
                        menu_id = self.env.ref(menu)
                        if menu_id and menu_id.id in res.ids:
                            id_list.append(menu_id.id)
                    filter_id = [par.id for par in res if par.id not in id_list]
                    res = self.browse(filter_id)

                # # TODO group_nv_nganh_hang
                # if self.env.user.has_group('tts_modifier_access_right.group_nv_nganh_hang'):
                #     menu_list = [
                #         'tuanhuy_purchase.purchase_order_line_menu',
                #         'tuanhuy_purchase.purchase_order_summaries_menu_parent',
                #         'tuanhuy_import_sale_purchase.import_purchase_order_menu_parent',
                #         'tuanhuy_purchase.purchase_order_line_return_menu',
                #         'purchase.menu_action_picking_tree_in_move',
                #         'purchase.menu_purchase_general_settings',
                #         'purchase.menu_procurement_management',
                #         'sale_purchase_returns.purchase_order_return_menu_parent',
                #         'purchase.menu_purchase_control',
                #         'purchase.menu_purchase_config',
                #     ]
                #     id_list = []
                #     for menu in menu_list:
                #         menu_id = self.env.ref(menu)
                #         if menu_id and menu_id.id in res.ids:
                #             id_list.append(menu_id.id)
                #     filter_id = [par.id for par in res if par.id not in id_list]
                #     res = self.browse(filter_id)

                # # TODO group_nv_mua_hang
                if self.env.user.has_group('tts_modifier_access_right.group_nv_mua_hang'):
                    menu_list = [
                        'tuanhuy_purchase.purchase_order_line_menu',
                        'tuanhuy_purchase.purchase_order_summaries_menu_parent',
                        'tuanhuy_import_sale_purchase.import_purchase_order_menu_parent',
                        'tuanhuy_purchase.purchase_order_line_return_menu',
                        'purchase.menu_action_picking_tree_in_move',
                        'purchase.menu_purchase_general_settings',
                    ]
                    id_list = []
                    for menu in menu_list:
                        menu_id = self.env.ref(menu)
                        if menu_id and menu_id.id in res.ids:
                            id_list.append(menu_id.id)
                    filter_id = [par.id for par in res if par.id not in id_list]
                    res = self.browse(filter_id)

                # TODO group_truong_kd
                if self.env.user.has_group('tts_modifier_access_right.group_truong_kd'):
                    menu_list = [
                        'purchase.menu_purchase_root',
                    ]
                    id_list = []
                    for menu in menu_list:
                        menu_id = self.env.ref(menu)
                        if menu_id and menu_id.id in res.ids:
                            id_list.append(menu_id.id)
                    filter_id = [par.id for par in res if par.id not in id_list]
                    res = self.browse(filter_id)

                # # TODO group_nvkd
                if self.env.user.has_group('tts_modifier_access_right.group_nvkd'):
                    menu_list = [
                        'purchase.menu_purchase_root',
                    ]
                    id_list = []
                    for menu in menu_list:
                        menu_id = self.env.ref(menu)
                        if menu_id and menu_id.id in res.ids:
                            id_list.append(menu_id.id)
                    filter_id = [par.id for par in res if par.id not in id_list]
                    res = self.browse(filter_id)

                # # TODO group_ketoan_tonghop
                if self.env.user.has_group('tts_modifier_access_right.group_ketoan_tonghop'):
                    menu_list = [
                    ]
                    id_list = []
                    for menu in menu_list:
                        menu_id = self.env.ref(menu)
                        if menu_id and menu_id.id in res.ids:
                            id_list.append(menu_id.id)
                    filter_id = [par.id for par in res if par.id not in id_list]
                    res = self.browse(filter_id)

                # # TODO group_ketoan_kho
                if self.env.user.has_group('tts_modifier_access_right.group_ketoan_kho'):
                    menu_list = [
                    ]
                    id_list = []
                    for menu in menu_list:
                        menu_id = self.env.ref(menu)
                        if menu_id and menu_id.id in res.ids:
                            id_list.append(menu_id.id)
                    filter_id = [par.id for par in res if par.id not in id_list]
                    res = self.browse(filter_id)

                # # TODO group_ql_kho
                if self.env.user.has_group('tts_modifier_access_right.group_ql_kho'):
                    menu_list = [
                        'purchase.menu_purchase_root',
                    ]
                    id_list = []
                    for menu in menu_list:
                        menu_id = self.env.ref(menu)
                        if menu_id and menu_id.id in res.ids:
                            id_list.append(menu_id.id)
                    filter_id = [par.id for par in res if par.id not in id_list]
                    res = self.browse(filter_id)

                # # TODO group_nv_nhap_hang
                if self.env.user.has_group('tts_modifier_access_right.group_nv_nhap_hang'):
                    menu_list = [
                        'purchase.menu_purchase_root',
                    ]
                    id_list = []
                    for menu in menu_list:
                        menu_id = self.env.ref(menu)
                        if menu_id and menu_id.id in res.ids:
                            id_list.append(menu_id.id)
                    filter_id = [par.id for par in res if par.id not in id_list]
                    res = self.browse(filter_id)

                # # TODO group_soan_donggoi
                if self.env.user.has_group('tts_modifier_access_right.group_soan_donggoi'):
                    menu_list = [
                        'purchase.menu_purchase_root',
                    ]
                    id_list = []
                    for menu in menu_list:
                        menu_id = self.env.ref(menu)
                        if menu_id and menu_id.id in res.ids:
                            id_list.append(menu_id.id)
                    filter_id = [par.id for par in res if par.id not in id_list]
                    res = self.browse(filter_id)

                # # TODO group_nv_giao_hang
                if self.env.user.has_group('tts_modifier_access_right.group_nv_giao_hang'):
                    menu_list = [
                        'purchase.menu_purchase_root',
                    ]
                    id_list = []
                    for menu in menu_list:
                        menu_id = self.env.ref(menu)
                        if menu_id and menu_id.id in res.ids:
                            id_list.append(menu_id.id)
                    filter_id = [par.id for par in res if par.id not in id_list]
                    res = self.browse(filter_id)

        return res


class purchase_order_inherit(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(purchase_order_inherit, self).fields_view_get(view_id, view_type, toolbar=toolbar,
                                                      submenu=False)
        doc = etree.XML(res['arch'])

        # TODO group_ketoan_kho

        if self.env.user.has_group('tts_modifier_access_right.group_ketoan_kho') and self._context.get('purchase_order_return', False):
            if view_type == 'form':
                for node in doc.xpath("//form"):
                    node.set('create', "true")
                    node.set('modifiers', """{"create": "true"}""")
                    node.set('edit', "true")
                    node.set('modifiers', """{"edit": "true"}""")
                    node.set('delete', "false")
                    node.set('modifiers', """{"delete": "false"}""")
                # for node in doc.xpath("//form/header/button"):
                #     node.set('invisible', "1")
                #     node.set('modifiers', """{"invisible": true}""")
                res['arch'] = etree.tostring(doc)
            if view_type == 'tree':
                for node in doc.xpath("//tree"):
                    node.set('create', "true")
                    node.set('modifiers', """{"create": "true"}""")
                    node.set('delete', "false")
                    node.set('modifiers', """{"delete": "false"}""")
                res['arch'] = etree.tostring(doc)

        # TODO group_ketoan_tonghop

        if self.env.user.has_group('tts_modifier_access_right.group_ketoan_tonghop') and self._context.get(
                'purchase_order_return', False):
            if view_type == 'form':
                for node in doc.xpath("//form"):
                    node.set('create', "true")
                    node.set('modifiers', """{"create": "true"}""")
                    node.set('edit', "true")
                    node.set('modifiers', """{"edit": "true"}""")
                    node.set('delete', "false")
                    node.set('modifiers', """{"delete": "false"}""")
                # for node in doc.xpath("//form/header/button"):
                #     node.set('invisible', "1")
                #     node.set('modifiers', """{"invisible": true}""")
                res['arch'] = etree.tostring(doc)
            if view_type == 'tree':
                for node in doc.xpath("//tree"):
                    node.set('create', "true")
                    node.set('modifiers', """{"create": "true"}""")
                    node.set('delete', "false")
                    node.set('modifiers', """{"delete": "false"}""")
                res['arch'] = etree.tostring(doc)

        # TODO group_nv_nganh_hang

        if self.env.user.has_group('tts_modifier_access_right.group_nv_nganh_hang'):
            if view_type == 'form':
                for node in doc.xpath("//button[@name='action_view_picking']"):
                    node.set('invisible', "true")
                    node.set('modifiers', """{"invisible": "true"}""")
                for node in doc.xpath("//button[@name='action_view_invoice']"):
                    node.set('invisible', "true")
                    node.set('modifiers', """{"invisible": "true"}""")
                for node in doc.xpath("//form"):
                    node.set('create', "true")
                    node.set('modifiers', """{"create": "true"}""")
                    node.set('edit', "true")
                    node.set('modifiers', """{"edit": "true"}""")
                res['arch'] = etree.tostring(doc)
            if view_type == 'tree':
                for node in doc.xpath("//tree"):
                    node.set('create', "true")
                    node.set('modifiers', """{"create": "true"}""")
                    node.set('edit', "true")
                    node.set('modifiers', """{"edit": "true"}""")
                res['arch'] = etree.tostring(doc)

        # TODO group_nv_mua_hang

        if self.env.user.has_group('tts_modifier_access_right.group_nv_mua_hang'):
            if view_type == 'form':
                for node in doc.xpath("//button[@name='action_view_picking']"):
                    node.set('invisible', "true")
                    node.set('modifiers', """{"invisible": "true"}""")
                for node in doc.xpath("//button[@name='action_view_invoice']"):
                    node.set('invisible', "true")
                    node.set('modifiers', """{"invisible": "true"}""")
                res['arch'] = etree.tostring(doc)


        # TODO group_nvkd

        if self.env.user.has_group('tts_modifier_access_right.group_nvkd'):
            if view_type == 'form':
                for node in doc.xpath("//button[@name='action_view_picking']"):
                    node.set('invisible', "true")
                    node.set('modifiers', """{"invisible": "true"}""")
                for node in doc.xpath("//button[@name='action_view_invoice']"):
                    node.set('invisible', "true")
                    node.set('modifiers', """{"invisible": "true"}""")
                res['arch'] = etree.tostring(doc)


        return res
