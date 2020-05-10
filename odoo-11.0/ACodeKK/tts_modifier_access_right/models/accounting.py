from odoo import models, fields, api
from lxml import etree
from odoo import SUPERUSER_ID
import types


class IrUiMenu_account_ihr(models.Model):
    _inherit = 'ir.ui.menu'

    def search(self, args, offset=0, limit=None, order=None, count=False):
        res = super(IrUiMenu_account_ihr, self).search(args, offset, limit, order, count=count)
        if 'search_menu' not in self._context:
            if type(res) != int:
                pass
                # TODO ACCOUNTING MENU

                if self.env.user.has_group('tts_modifier_access_right.group_nv_giao_hang'):
                    menu_list = [
                        'account.menu_finance',
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
                        'account.menu_finance_receivables',
                        'account.menu_finance_payables',
                        'account.menu_finance_entries',
                        'account.menu_finance_reports',
                        'account.menu_finance_configuration',
                        'tts_salary_delivery_income.xem_luong_menu',
                        # 'tts_modifier_accounting.menu_sale_order_in_account',
                        'tts_account_khoan_thu_khac.khoan_thu_khac_menu',
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