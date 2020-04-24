# -*- coding: utf-8 -*-

from odoo import models, fields, api
from lxml import etree
from odoo import SUPERUSER_ID
import types
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

                employee_ceo = self.env['hr.employee'].search([('job_id.name', '=', 'CEO')])
                if self.env.user not in employee_ceo.mapped('user_id') and self._uid != SUPERUSER_ID:
                    menu_list = [
                        'tts_sale_report.menu_dashboard_widget_doanh_so',
                    ]
                    id_list = []
                    for menu in menu_list:
                        menu_id = self.env.ref(menu)
                        if menu_id and menu_id.id in res.ids:
                            id_list.append(menu_id.id)
                    filter_id = [par.id for par in res if par.id not in id_list]
                    res = self.browse(filter_id)

                employee_kd = self.env['hr.employee'].search( ['|', ('job_id.name', '=', 'Nhân viên kinh doanh'), ('job_id.name', '=', 'Trưởng nhóm kinh doanh')])
                if self.env.user not in employee_kd.mapped('user_id') and self._uid != SUPERUSER_ID:
                    menu_list = [
                        'tts_sale_report.menu_dashboard_widget_doanh_so',
                    ]
                    id_list = []
                    for menu in menu_list:
                        menu_id = self.env.ref(menu)
                        if menu_id and menu_id.id in res.ids:
                            id_list.append(menu_id.id)
                    filter_id = [par.id for par in res if par.id not in id_list]
                    res = self.browse(filter_id)


                # TODO PURCHASE MENU

                # # TODO group_giam_doc_kd
                if self.env.user.has_group('tts_modifier_access_right.group_giam_doc_kd'):
                    menu_list = [
                        'tuanhuy_sale.sale_order_line_menu',
                        'product_pack.menu_product_pack_core',
                        'tuanhuy_sale.sale_order_line_return_menu',
                        'tuanhuy_sale.sale_order_line_report_menu',
                        'bao_cao_doanh_thu.bao_cao_doanh_thu_menu',
                        'website_crm_partner_assign.menu_report_crm_opportunities_assign_tree',
                        'website_crm_partner_assign.menu_report_crm_partner_assign_tree',
                        'tuanhuy_sale.sale_order_summaries_menu_parent',
                        'sale.menu_report_product_all',
                        'sales_team.menu_sale_general_settings',
                        'tuanhuy_product.product_group_sale_menu_parent',
                        'tuanhuy_import_sale_purchase.import_sale_order_menu_parent',
                        'tuanhuy_import_sale_purchase.check_sale_purchase_menu_parent',
                        'tts_zalo_api.zalo_api_root',
                        'delivery.sale_menu_action_delivery_carrier_form',
                        'sale.menu_product_pricelist_main',
                        'tuanhuy_sale_modifier.menu_product_to_date'
                    ]
                    id_list = []
                    for menu in menu_list:
                        menu_id = self.env.ref(menu)
                        if menu_id and menu_id.id in res.ids:
                            id_list.append(menu_id.id)
                    filter_id = [par.id for par in res if par.id not in id_list]
                    res = self.browse(filter_id)

                # # TODO group_nv_nganh_hang
                if self.env.user.has_group('tts_modifier_access_right.group_nv_nganh_hang'):
                    menu_list = [
                        'tuanhuy_sale.sale_order_line_menu',
                        'crm.menu_crm_opportunities',
                        'crm.crm_lead_menu_activities',
                        'tts_sms_to_email.sms_inbox_menu',
                        'product_pack.menu_product_pack_core',
                        'tuanhuy_sale.sale_order_line_return_menu',
                        # 'tuanhuy_sale.sale_order_line_report_menu',
                        # 'bao_cao_doanh_thu.bao_cao_doanh_thu_menu',
                        # 'website_crm_partner_assign.menu_report_crm_opportunities_assign_tree',
                        # 'website_crm_partner_assign.menu_report_crm_partner_assign_tree',
                        'tuanhuy_sale.sale_order_summaries_menu_parent',
                        # 'sale.menu_report_product_all',
                        'sales_team.menu_sale_general_settings',
                        'tuanhuy_product.product_group_sale_menu_parent',
                        'tuanhuy_import_sale_purchase.import_sale_order_menu_parent',
                        'tuanhuy_import_sale_purchase.check_sale_purchase_menu_parent',
                        'tts_zalo_api.zalo_api_root',
                        'sales_team.sales_team_config',
                        'sale.menu_product_pricelist_main',
                        'tuanhuy_sale_modifier.menu_product_to_date',
                        'crm.menu_crm_config_lead',
                        'delivery.sale_menu_delivery',
                        'sale_attachment.sale_attachment',
                    ]
                    id_list = []
                    for menu in menu_list:
                        menu_id = self.env.ref(menu)
                        if menu_id and menu_id.id in res.ids:
                            id_list.append(menu_id.id)

                    # id_list += self.env['ir.ui.menu'].get_list_menu_hide('sales_team.menu_sale_report', [
                    #     'tts_modifier_accounting.menu_sale_gross_proifit',
                    # ])
                    filter_id = [par.id for par in res if par.id not in id_list]
                    res = self.browse(filter_id)

                # # TODO group_nv_mua_hang
                if self.env.user.has_group('tts_modifier_access_right.group_nv_mua_hang'):
                    menu_list = [
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
                        'tuanhuy_sale.sale_order_line_menu',
                        'product_pack.menu_product_pack_core',
                        'tuanhuy_sale.sale_order_line_return_menu',
                        'tuanhuy_sale.sale_order_line_report_menu',
                        'bao_cao_doanh_thu.bao_cao_doanh_thu_menu',
                        # 'website_crm_partner_assign.menu_report_crm_opportunities_assign_tree',
                        # 'website_crm_partner_assign.menu_report_crm_partner_assign_tree',
                        'tuanhuy_sale.sale_order_summaries_menu_parent',
                        # 'sale.menu_report_product_all',
                        'sales_team.menu_sale_general_settings',
                        'tuanhuy_product.product_group_sale_menu_parent',
                        'tuanhuy_import_sale_purchase.import_sale_order_menu_parent',
                        'tuanhuy_import_sale_purchase.check_sale_purchase_menu_parent',
                        'tts_zalo_api.zalo_api_root',
                        'delivery.sale_menu_action_delivery_carrier_form',
                        'sale.prod_config_main',
                        'sale.menu_product_pricelist_main',
                        'tuanhuy_sale_modifier.menu_product_to_date',
                        'crm.menu_crm_config_lead',
                        'tts_transport_delivery.delivery_sope_view_menu',
                        'sale.menu_sale_quotations',
                        'sale.menu_sale_order',
                        # 'tts_modifier_accounting.menu_sale_gross_proifit'
                    ]
                    id_list = []
                    for menu in menu_list:
                        menu_id = self.env.ref(menu)
                        if menu_id and menu_id.id in res.ids:
                            id_list.append(menu_id.id)
                    # id_list += self.env['ir.ui.menu'].get_list_menu_hide('sales_team.menu_sale_report', [
                    #     'tts_modifier_accounting.menu_sale_gross_proifit',
                    # ])
                    filter_id = [par.id for par in res if par.id not in id_list]
                    res = self.browse(filter_id)

                # # TODO group_nvkd
                if self.env.user.has_group('tts_modifier_access_right.group_nvkd'):
                    menu_list = [
                        'tuanhuy_sale.sale_order_line_menu',
                        'product_pack.menu_product_pack_core',
                        'tuanhuy_sale.sale_order_line_return_menu',
                        'tuanhuy_sale.sale_order_line_report_menu',
                        'bao_cao_doanh_thu.bao_cao_doanh_thu_menu',
                        'website_crm_partner_assign.menu_report_crm_opportunities_assign_tree',
                        'website_crm_partner_assign.menu_report_crm_partner_assign_tree',
                        'tuanhuy_sale.sale_order_summaries_menu_parent',
                        'sale.menu_report_product_all',
                        'sales_team.menu_sale_general_settings',
                        'tuanhuy_product.product_group_sale_menu_parent',
                        'tuanhuy_import_sale_purchase.import_sale_order_menu_parent',
                        'tuanhuy_import_sale_purchase.check_sale_purchase_menu_parent',
                        'tts_zalo_api.zalo_api_root',
                        'sales_team.sales_team_config',
                        'delivery.sale_menu_action_delivery_carrier_form',
                        'sale.prod_config_main',
                        'sale.menu_product_pricelist_main',
                        'tuanhuy_sale_modifier.menu_product_to_date',
                        'crm.menu_crm_config_lead',
                        'tts_transport_delivery.delivery_sope_view_menu',
                        'tts_modifier_accounting.menu_sale_gross_proifit',
                        'sale.menu_sale_quotations',
                        'sale.menu_sale_order'
                    ]
                    id_list = []
                    for menu in menu_list:
                        menu_id = self.env.ref(menu)
                        if menu_id and menu_id.id in res.ids:
                            id_list.append(menu_id.id)
                    filter_id = [par.id for par in res if par.id not in id_list]
                    res = self.browse(filter_id)

                # TC - KT
                # # TODO group_ketoan_tonghop
                if self.env.user.has_group('tts_modifier_access_right.group_ketoan_tonghop'):
                    menu_list = [
                        # 'sales_team.menu_sales',
                        # 'sale_purchase_returns.sale_order_return_menu_parent',
                        'tuanhuy_sale.sale_order_summaries_menu_parent',
                    ]
                    id_list = []
                    for menu in menu_list:
                        menu_id = self.env.ref(menu)
                        if menu_id and menu_id.id in res.ids:
                            id_list.append(menu_id.id)
                    id_list += self.env['ir.ui.menu'].get_list_menu_hide('sales_team.menu_sale_report', [
                        'tts_modifier_accounting.menu_sale_gross_proifit',
                    ])
                    filter_id = [par.id for par in res if par.id not in id_list]
                    res = self.browse(filter_id)

                # # TODO group_ketoan_kho
                if self.env.user.has_group('tts_modifier_access_right.group_ketoan_kho'):
                    menu_list = [
                        # 'sales_team.menu_sales',
                        # 'sale_purchase_returns.sale_order_return_menu_parent',
                        'tuanhuy_sale.sale_order_summaries_menu_parent',
                    ]
                    id_list = []
                    for menu in menu_list:
                        menu_id = self.env.ref(menu)
                        if menu_id and menu_id.id in res.ids:
                            id_list.append(menu_id.id)
                    id_list += self.env['ir.ui.menu'].get_list_menu_hide('sales_team.menu_sale_report', [
                        'tts_modifier_accounting.menu_sale_gross_proifit',
                    ])
                    filter_id = [par.id for par in res if par.id not in id_list]
                    res = self.browse(filter_id)

                # Kho - Giao nhận
                # # TODO group_ql_kho
                if self.env.user.has_group('tts_modifier_access_right.group_ql_kho'):
                    menu_list = [
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
                    ]
                    id_list = []
                    for menu in menu_list:
                        menu_id = self.env.ref(menu)
                        if menu_id and menu_id.id in res.ids:
                            id_list.append(menu_id.id)
                    filter_id = [par.id for par in res if par.id not in id_list]
                    res = self.browse(filter_id)

                # # TODO group_khach_hang
                if self.env.user.has_group('tts_modifier_access_right.group_khach_hang'):
                    menu_list = [
                        'mail.mail_channel_menu_root_chat',
                        'calendar.mail_menu_calendar',
                        'hr.menu_hr_root',
                        'hr_expense.menu_hr_expense_root',
                        'sales_team.menu_base_partner',
                        # 'website.menu_website'
                    ]
                    id_list = []
                    for menu in menu_list:
                        menu_id = self.env.ref(menu)
                        if menu_id and menu_id.id in res.ids:
                            id_list.append(menu_id.id)
                    filter_id = [par.id for par in res if par.id not in id_list]
                    res = self.browse(filter_id)

        return res


class sale_order(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_confirm_order(self):
        if self.env.user.has_group('tts_modifier_access_right.group_nvkd'):
            for rec in self:
                if rec.create_uid.id != self._uid and rec.create_uid.id != 1 and not rec.create_uid.has_group('tts_modifier_access_right.group_khach_hang'):
                    raise UserError('Bạn không có quyền thực hiện trên phiếu này.')
        res = super(sale_order, self).action_confirm_order()
        return res

    @api.multi
    def write(self, val):
        if self.env.user.has_group('tts_modifier_access_right.group_nvkd'):
            for rec in self:
                if rec.create_uid.id != self._uid and rec.create_uid.id != 1 and not rec.create_uid.has_group('tts_modifier_access_right.group_khach_hang'):
                    raise UserError('Bạn không có quyền thực hiện trên phiếu này.')
        res = super(sale_order, self).write(val)
        return res

    @api.multi
    def action_sale_cancel(self):
        if self.env.user.has_group('tts_modifier_access_right.group_nvkd'):
            for rec in self:
                if rec.create_uid.id != self._uid and rec.create_uid.id != 1 and not rec.create_uid.has_group('tts_modifier_access_right.group_khach_hang'):
                    raise UserError('Bạn không có quyền thực hiện trên phiếu này.')
        res = super(sale_order, self).action_sale_cancel()
        return res

    def _get_domain_saleperson(self):
        group_giam_doc_kd = self.env.ref('tts_modifier_access_right.group_giam_doc_kd').users
        group_truong_kd = self.env.ref('tts_modifier_access_right.group_truong_kd').users
        group_nvkd = self.env.ref('tts_modifier_access_right.group_nvkd').users
        return [('id', 'in', group_giam_doc_kd.ids + group_truong_kd.ids + group_nvkd.ids)]

    user_id = fields.Many2one(domain=_get_domain_saleperson)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(sale_order, self).fields_view_get(view_id, view_type, toolbar=toolbar,
                                                                    submenu=False)
        doc = etree.XML(res['arch'])

        # TODO group_ketoan_kho
        hide_access_right = False
        if self.env.context.get('params',False):
            if self.env.context['params'].get('action',False) == self.env.ref("sale.action_quotations")[0].id and not self.env.user.has_group("sales_team.group_sale_manager"):
                hide_access_right = True
        if self.env.user.has_group('tts_modifier_access_right.group_ketoan_kho') and self._context.get(
                'sale_order_return', False) and not self.env.user.has_group("sales_team.group_sale_manager") or hide_access_right:
            if view_type == 'form':
                for node in doc.xpath("//form"):
                    node.set('create', "false")
                    node.set('modifiers', """{"create": "false"}""")
                    node.set('edit', "false")
                    node.set('modifiers', """{"edit": "false"}""")
                    node.set('delete', "false")
                    node.set('modifiers', """{"delete": "false"}""")
                for node in doc.xpath("//form/header/button"):
                    node.set('invisible', "1")
                    node.set('modifiers', """{"invisible": true}""")
                res['arch'] = etree.tostring(doc)
            if view_type == 'tree':
                for node in doc.xpath("//tree"):
                    node.set('create', "false")
                    node.set('modifiers', """{"create": "false"}""")
                    node.set('delete', "false")
                    node.set('modifiers', """{"delete": "false"}""")
                res['arch'] = etree.tostring(doc)

        if self.env.user.has_group('tts_modifier_access_right.group_ketoan_kho') and not self.env.user.has_group(
            "sales_team.group_sale_manager") or hide_access_right:
            if view_type == 'form':
                for node in doc.xpath("//form"):
                    node.set('create', "false")
                    node.set('modifiers', """{"create": "false"}""")
                    node.set('edit', "false")
                    node.set('modifiers', """{"edit": "false"}""")
                    node.set('delete', "false")
                    node.set('modifiers', """{"delete": "false"}""")
                for node in doc.xpath("//form/header/button"):
                    node.set('invisible', "1")
                    node.set('modifiers', """{"invisible": true}""")
                res['arch'] = etree.tostring(doc)
            if view_type == 'tree':
                for node in doc.xpath("//tree"):
                    node.set('create', "false")
                    node.set('modifiers', """{"create": "false"}""")
                    node.set('delete', "false")
                    node.set('modifiers', """{"delete": "false"}""")
                res['arch'] = etree.tostring(doc)

        # TODO group_ketoan_tonghop

        if self.env.user.has_group('tts_modifier_access_right.group_ketoan_tonghop') and self._context.get(
                'sale_order_return', False) and not self.env.user.has_group("sales_team.group_sale_manager") or hide_access_right:
            if view_type == 'form':
                for node in doc.xpath("//form"):
                    node.set('create', "false")
                    node.set('modifiers', """{"create": "false"}""")
                    node.set('edit', "false")
                    node.set('modifiers', """{"edit": "false"}""")
                    node.set('delete', "false")
                    node.set('modifiers', """{"delete": "false"}""")
                for node in doc.xpath("//form/header/button"):
                    node.set('invisible', "1")
                    node.set('modifiers', """{"invisible": true}""")
                res['arch'] = etree.tostring(doc)
            if view_type == 'tree':
                for node in doc.xpath("//tree"):
                    node.set('create', "false")
                    node.set('modifiers', """{"create": "false"}""")
                    node.set('delete', "false")
                    node.set('modifiers', """{"delete": "false"}""")
                res['arch'] = etree.tostring(doc)
        if self.env.user.has_group('tts_modifier_access_right.group_ketoan_tonghop') and not self.env.user.has_group(
            "sales_team.group_sale_manager") or hide_access_right:
            if view_type == 'form':
                for node in doc.xpath("//form"):
                    node.set('create', "false")
                    node.set('modifiers', """{"create": "false"}""")
                    node.set('edit', "false")
                    node.set('modifiers', """{"edit": "false"}""")
                    node.set('delete', "false")
                    node.set('modifiers', """{"delete": "false"}""")
                for node in doc.xpath("//form/header/button"):
                    node.set('invisible', "1")
                    node.set('modifiers', """{"invisible": true}""")
                res['arch'] = etree.tostring(doc)
            if view_type == 'tree':
                for node in doc.xpath("//tree"):
                    node.set('create', "false")
                    node.set('modifiers', """{"create": "false"}""")
                    node.set('delete', "false")
                    node.set('modifiers', """{"delete": "false"}""")
                res['arch'] = etree.tostring(doc)
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
                for node in doc.xpath("//button[@name='action_view_delivery']"):
                    node.set('invisible', "true")
                    node.set('modifiers', """{"invisible": "true"}""")
                for node in doc.xpath("//button[@name='action_view_invoice']"):
                    node.set('invisible', "true")
                    node.set('modifiers', """{"invisible": "true"}""")
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

        # TODO group_nv_mua_hang

        if self.env.user.has_group('tts_modifier_access_right.group_nv_mua_hang'):
            if view_type == 'form':
                for node in doc.xpath("//button[@name='action_view_delivery']"):
                    node.set('invisible', "true")
                    node.set('modifiers', """{"invisible": "true"}""")
                for node in doc.xpath("//button[@name='action_view_invoice']"):
                    node.set('invisible', "true")
                    node.set('modifiers', """{"invisible": "true"}""")
                res['arch'] = etree.tostring(doc)

        # TODO group_nvkd

        if self.env.user.has_group('tts_modifier_access_right.group_nvkd'):
            if view_type == 'form':
                for node in doc.xpath("//button[@name='action_view_delivery']"):
                    node.set('invisible', "true")
                    node.set('modifiers', """{"invisible": "true"}""")
                for node in doc.xpath("//button[@name='action_view_invoice']"):
                    node.set('invisible', "true")
                    node.set('modifiers', """{"invisible": "true"}""")
                res['arch'] = etree.tostring(doc)
        return res

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if self.env.user.has_group('tts_modifier_access_right.group_nvkd'):
            domain.append(('user_id', '=', self.env.uid))
        if self.env.user.has_group('tts_modifier_access_right.group_truong_kd'):
            group_truong_kd_users = self.env.ref('tts_modifier_access_right.group_nvkd').users.ids
            domain.append(('user_id', 'in', group_truong_kd_users))
        res = super(sale_order, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit,
                                                     order=order)
        return res



class res_partner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(res_partner, self).fields_view_get(view_id, view_type, toolbar=toolbar,
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
            if view_type == 'kanban':
                for node in doc.xpath("//kanban"):
                    node.set('create', "false")
                    node.set('modifiers', """{"create": "false"}""")
                res['arch'] = etree.tostring(doc)

        return res



class product_template(models.Model):
    _inherit = 'product.template'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(product_template, self).fields_view_get(view_id, view_type, toolbar=toolbar,
                                                                 submenu=False)
        doc = etree.XML(res['arch'])

        # TODO group_nvkd

        if self.env.user.has_group('tts_modifier_access_right.group_nvkd'):
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

        # TODO group_truong_kd

        if self.env.user.has_group('tts_modifier_access_right.group_truong_kd'):
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

        # TODO group_ketoan_tonghop

        if self.env.user.has_group('tts_modifier_access_right.group_ketoan_tonghop'):
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

        #TODO group_ketoan_kho

        if self.env.user.has_group('tts_modifier_access_right.group_ketoan_kho'):
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




class product_product(models.Model):
    _inherit = 'product.product'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(product_product, self).fields_view_get(view_id, view_type, toolbar=toolbar,
                                                                 submenu=False)
        doc = etree.XML(res['arch'])

        # TODO group_nvkd

        if self.env.user.has_group('tts_modifier_access_right.group_nvkd'):
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

        # TODO group_truong_kd

        if self.env.user.has_group('tts_modifier_access_right.group_truong_kd'):
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