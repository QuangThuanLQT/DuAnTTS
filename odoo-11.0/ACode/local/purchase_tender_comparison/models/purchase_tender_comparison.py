# -*- coding: utf-8 -*-

from odoo import models, api


class PurchaseTenderComparison(models.Model):
    _inherit = 'purchase.requisition'

    def get_rating_configuration(self):
        configs = []
        for purchase in self.purchase_ids:
            ratings = self.env['supplier.rating'].search(
                [('partner_id', '=', purchase.partner_id.id), ('state', '=', 'validate')])

            rating_lines = self.env['ratings.lines'].read_group([('rating_id', 'in', ratings.ids)],
                                                                ['config_id', 'value_value'], groupby=['config_id'])
            for line in rating_lines:
                rating_name = line.get('config_id')[1]
                if not rating_name in configs:
                    configs.append(rating_name)
        configs.append('Average Rating')

        return configs

    def get_suppliers(self):
        suppliers = []
        for purchase in self.purchase_ids:
            ratings = self.env['supplier.rating'].search(
                [('partner_id', '=', purchase.partner_id.id), ('state', '=', 'validate')])

            rating_lines = self.env['ratings.lines'].read_group([('rating_id', 'in', ratings.ids)],
                                                                ['config_id', 'value_value'], groupby=['config_id'])
            if rating_lines:
                suppliers.append(str(purchase.partner_id.name))
        return suppliers

    def get_supplier_rating_details(self):
        partner_rating = {}
        for purchase in self.purchase_ids:
            rating_dic = {}
            ratings = self.env['supplier.rating'].search(
                [('partner_id', '=', purchase.partner_id.id), ('state', '=', 'validate')])

            rating_lines = self.env['ratings.lines'].read_group([('rating_id', 'in', ratings.ids)],
                                                                ['config_id', 'value_value'], groupby=['config_id'])

            for line in rating_lines:
                rating_name = line.get('config_id')[1]
                rating_value = line.get('value_value') / line.get('config_id_count')
                rating_dic.update({
                    rating_name: rating_value
                })

            if rating_dic:
                rating_dic.update({
                    'Average Rating': '%.2f' % ((sum(rating_dic.values())) / len(rating_dic))
                })
                partner_rating.update({
                    purchase.partner_id.name: rating_dic
                })
        return partner_rating

    def get_last_purchase_label(self):
        labels = ['Product', 'Last Purchase On', 'Last Purchase qty',
                  'Last Purchase Amount', 'Last Purchase Supplier', 'Last PO Status']

        return labels

    def _get_last_po_dict(self, last_line):
        '''
         prepare labels for RFQ comparison report to generate
         last purchase details table
        :param last_line: (Object)last purchase order line
        :return: (Dict) last purchase order details
        '''
        if last_line.product_id.default_code and last_line.product_id.name:
            product_name = '[' + last_line.product_id.default_code + ']' + last_line.product_id.name
        else:
            product_name = last_line.product_id.name
        state = dict(self.env['purchase.order'].fields_get(allfields=['state'])['state']['selection'])
        last_po_line = {
            'Product': product_name,
            'Last Purchase On': last_line.order_id.date_order,
            'Last Purchase qty': last_line.product_qty,
            'Last Purchase Amount': last_line.price_subtotal,
            'Last Purchase Supplier': last_line.order_id.partner_id.name,
            'Last PO Status': state.get(last_line.state)
        }
        return last_po_line

    def get_last_purchase_details(self):
        purchase_dic = {}
        last_po_lines = []
        purchase_orderlines = []
        purchase_line_obj = self.env['purchase.order.line']
        states = ['draft', 'cancel', 'rfq_reject', 'pending']
        products = [line.product_id.id for line in self.line_ids]

        tender_purchase_orders = self.env['purchase.order'].search_read([('id', 'in', self.purchase_ids.ids)],
                                                                        ['partner_id'])
        partners = list(set([value['partner_id'][0] for value in tender_purchase_orders]))
        last_purchase_orders = self.env['purchase.order'].search([('create_date', '<=', self.create_date),
                                                                  ('partner_id', 'in', partners),
                                                                  ('state', 'not in', states),
                                                                  ('id', 'not in', self.purchase_ids.ids),
                                                                  ('product_id', 'in', products)])

        purchases = self.env['purchase.order'].search_read([('id', 'in', last_purchase_orders.ids)],
                                                           ['partner_id', 'order_line'])
        for po in purchases:
            partner_id = po.get('partner_id')[0]
            if purchase_dic.has_key(partner_id):
                purchase_orderlines.extend(po['order_line'])
            else:
                purchase_orderlines = po.get('order_line')

            purchase_dic.update({
                partner_id: purchase_orderlines
            })

        for key in purchase_dic:
            line_ids = purchase_dic.get(key)
            po_lines = purchase_line_obj.read_group([('id', 'in', line_ids)], ['product_id'],
                                                    groupby=['product_id'])
            for line in po_lines:
                # in filtered po lines if product occurrence is one
                if line.get('product_id_count') == 1:
                    last_line = self.env['purchase.order.line'].search(
                        [('id', '=', line_ids), ('product_id', '=', line.get('product_id')[0])], order='id desc')
                    last_po_line = self._get_last_po_dict(last_line)
                    last_po_lines.append(last_po_line)

                # in filtered po lines if product occurrence more then one
                if line.get('product_id_count') > 1:
                    last_line = self.env['purchase.order.line'].search(
                        [('id', '=', line_ids), ('product_id', '=', line.get('product_id')[0])], order='id desc')[0]
                    last_po_line = self._get_last_po_dict(last_line)
                    last_po_lines.append(last_po_line)

        return last_po_lines
