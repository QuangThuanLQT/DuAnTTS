# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

class res_partner_inherit(models.Model):
    _inherit = 'res.partner'

    @api.model
    def check_date_type(self, field, model):
        field = self.env['ir.model.fields'].search([
            ('name','=',field),
            ('model_id.model','=',model)
        ])
        if field:
            return field.ttype

    @api.model
    def get_customer_name_search(self, name):
        customerIds = []
        customers = self.env['res.partner'].search([('name','=',name)])
        if customers:
            customerIds = customers.ids
        else:
            self.env.cr.execute("SELECT id FROM res_partner WHERE UPPER(name) LIKE '%s'" % ("%" + name.upper() + "%"))
            customers = self.env.cr.fetchall()
            for customer in customers:
                customerIds.append(customer[0])
        return customerIds

    @api.model
    def get_customer_list(self,model):
        customerIds = []
        if model in ('sale.order'):
            self.env.cr.execute("SELECT name FROM res_partner WHERE customer = TRUE")
        elif model in ('purchase.order'):
            self.env.cr.execute("SELECT name FROM res_partner WHERE supplier = TRUE")
        else:
            self.env.cr.execute("SELECT name FROM res_partner")
        customers = self.env.cr.fetchall()
        for customer in customers:
            customerIds.append(customer[0])
        return customerIds

    @api.model
    def get_origin_text_search(self, name, field, model):
        record_ids = []
        if field == 'origin':
            self.env.cr.execute("select id from stock_picking where UPPER(origin) LIKE '%s'" % ("%" + name.upper() + "%"))
        if field == 'number_origin':
            self.env.cr.execute("select id from account_invoice where number_origin LIKE '%s'" % ("%" + name + "%"))
        if field == 'note' and model == 'stock.picking':
            self.env.cr.execute("select id from stock_picking where UPPER(note) LIKE '%s'" % ("%" + name.upper() + "%"))
        if field == 'note' and model == 'sale.order':
            self.env.cr.execute("select id from sale_order where UPPER(note) LIKE '%s'" % ("%" + name.upper() + "%"))
        if field == 'notes' and model == 'purchase.order':
            self.env.cr.execute("select id from purchase_order where UPPER(notes) LIKE '%s'" % ("%" + name.upper() + "%"))
        res_trans = self.env.cr.fetchall()
        for line in res_trans:
            record_ids.append(line[0])
        return record_ids

