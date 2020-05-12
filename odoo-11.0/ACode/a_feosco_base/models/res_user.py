import simplejson
from lxml import etree

from odoo import SUPERUSER_ID, models, api


class res_users(models.Model):
    _inherit = 'res.users'

    # @api.model
    # def _get_group_id(self, group_ext_id):
    #
    #     assert group_ext_id and '.' in group_ext_id, "External ID must be fully qualified"
    #     module, ext_id = group_ext_id.split('.')
    #     self.env.cr.execute("""SELECT res_id FROM ir_model_data WHERE module=%s AND name=%s""", (module, ext_id))
    #     return int(self.env.cr.fetchone()[0])
    #
    # def fields_view_get(self, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
    #     result = super(res_users, self).fields_view_get(view_id, view_type, context, toolbar, submenu)
    #
    #     user_pool = self.env['res.users']
    #     if not user_pool.has_group('base.group_erp_manager') \
    #             and not user_pool.has_group('base.group_system') \
    #             and not self.env.uid == SUPERUSER_ID:
    #
    #         group_erp_manager_id = self._get_group_id('base.group_erp_manager')
    #         group_system_id = self._get_group_id('base.group_system')
    #         group_name = 'sel_groups_' + '_'.join(map(str, sorted([group_erp_manager_id, group_system_id])))
    #
    #         arch = result.get('arch')
    #         if arch:
    #             doc = etree.XML(arch)
    #             invisible = 'invisible' if view_type == 'form' else 'tree_invisible'
    #             for node in doc.xpath("//field[@name='%s']" % (group_name,)):
    #                 node.set('modifiers', '{%s :true}' % (simplejson.dumps(invisible)))
    #                 node.set('invisible', '1')
    #
    #             result['arch'] = etree.tostring(doc)
    #     return result
    #
    # @api.onchange('')
    # def on_change_district(self, cr, uid, ids, feosco_district, addressOrtemp=1, context=None):
    #     if feosco_district:
    #         district_pool = self.pool.get('feosco.district').read(cr, uid, feosco_district, ['city_id'])
    #         tupe_city_id = district_pool['city_id']
    #         country_pool = self.pool.get('feosco.city').read(cr, uid, tupe_city_id[0], ['country'])
    #     if addressOrtemp == 1:
    #         return {'value': {'city': district_pool['city_id'], 'country_id': country_pool['country']}}
    #     if addressOrtemp == 2:
    #         return {'value': {'feosco_temp_city': district_pool['city_id'],
    #                           'feosco_temp_country_id': country_pool['country']}}
