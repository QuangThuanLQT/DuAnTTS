# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError


class product_search_keyword(models.Model):
    _name = "product.search.keyword"
    _order = "sequence asc"

    sequence = fields.Integer('Sequence', required=False)
    key = fields.Char('Keyword', required=True)
    product_ids = fields.Many2many('product.template', string='Product Suggestions', required=False)
    count = fields.Integer(string='Số lần Search', readonly=True)
    type = fields.Selection([('key', 'Key'), ('product', 'Product')], 'Type')

    @api.constrains('ref')
    def _check_public_holiday(self):
        for rec in self:
            if rec.ref:
                ids = rec.search([('key', '=', rec.key)])
                if ids and len(ids) > 1:
                    raise ValidationError(_('Keyword phải là duy nhất!'))

    @api.multi
    def name_get(self):
        res = []
        for field in self:
            res.append((field.id, '%s' % (field.key)))
        return res

    @api.model
    def do_action(self, data):
        if data.get('key', False):
            if data.get('key') == 'keyword':
                keyword_id = self.browse(data.get('data').get('id'))
                if keyword_id:
                    # keyword_id.count += 1
                    self.browse(data.get('data').get('id')).count += 1
                    history_id = self.env['product.search.history'].search([('user_id', '=', self.env.uid), ('keyword_id', '=', keyword_id.id), ('key', '=', data.get('value'))])
                    if not history_id:
                        history_id = self.env['product.search.history'].create({
                            'date': datetime.now(),
                            'user_id': self.env.uid,
                            'keyword_id': keyword_id.id,
                            'key': data.get('value'),
                        })
                    else:
                        history_id.date = datetime.now()
            elif data.get('key') == 'product':
                product_tmpl_id = self.env['product.template'].browse(data.get('data').get('id'))
                if product_tmpl_id:
                    history_id = self.env['product.search.history'].search([('user_id', '=', self.env.uid), ('product_tmpl_id', '=', product_tmpl_id.id), ('key', '=', data.get('value'))])
                    if not history_id:
                        history_id = self.env['product.search.history'].create({
                            'date': datetime.now(),
                            'user_id': self.env.uid,
                            'product_tmpl_id': product_tmpl_id.id,
                            'key': data.get('value'),
                        })
                    else:
                        history_id.date = datetime.now()
            elif data.get('key') == 'key_product':
                key_product_id = self.browse(data.get('data').get('id'))
                if key_product_id:
                    history_id = self.env['product.search.history'].search([('user_id', '=', self.env.uid), ('keyword_id', '=', key_product_id.id), ('key', '=', data.get('value'))])
                    if not history_id:
                        history_id = self.env['product.search.history'].create({
                            'date': datetime.now(),
                            'user_id': self.env.uid,
                            'keyword_id': key_product_id.id,
                            'key': data.get('value'),
                        })
                    else:
                        history_id.date = datetime.now()
        elif data.get('key') == 'history':
            True
        True
