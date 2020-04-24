# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
import json


class update_quotation_product(models.Model):
    _name = 'update.quotaion.product'

    key_word = fields.Char(string="Từ khoá")
    nha_san_xuat = fields.Char(string="Nhà sản xuất")
    ma_san_pham = fields.Char(string="Mã sản phẩm")
    ma_dat_hang = fields.Char(string="Mã Đặt Hàng")
    product_id = fields.Many2one('product.product', string="Sản phẩm")
    job_quotaion_ids = fields.Many2many('job.quotaion',string='Định mức')
    job_quotaion_line_id = fields.Many2one('job.quotaion.line')
    product_ids = fields.Char()
    description = fields.Text(string="Mô tả")

    @api.onchange('key_word', 'nha_san_xuat', 'ma_san_pham', 'ma_dat_hang')
    def onchange_product_id(self):
        for record in self:
            domain = []
            if record.nha_san_xuat and record.nha_san_xuat != 'Nêu rõ':
                nha_san_xuat = []
                for nsx in record.nha_san_xuat.split(','):
                    if nsx.strip():
                        self.env.cr.execute(
                            "SELECT id FROM brand_name WHERE lower(name) = '%s'" % (nsx.strip().lower()))
                        brand_names = self.env.cr.fetchall()
                        for brand_name in brand_names:
                            nha_san_xuat.append(brand_name)
                domain.append(('product_tmpl_id.brand_name_select', 'in', nha_san_xuat))
            if record.ma_san_pham and record.ma_san_pham != 'Nêu rõ':
                domain.append(('default_code', '=', record.ma_san_pham))
            if record.ma_dat_hang and record.ma_dat_hang != 'Nêu rõ':
                domain.append(('purchase_code', '=', record.ma_dat_hang))
            if record.key_word and record.key_word != 'Nêu rõ':
                for key in record.key_word.split(' '):
                    product_key_word = []
                    if key:
                        self.env.cr.execute(
                            "SELECT id FROM product_template WHERE lower(name) LIKE '%s'" % ("%" + key.lower() + "%"))
                        products = self.env.cr.fetchall()
                        for product in products:
                            product_key_word.append(product[0])
                        domain.append(('product_tmpl_id', 'in', product_key_word))

            product_ids = self.env['product.product'].search(domain)
            record.product_ids = json.dumps(product_ids.ids)

    @api.onchange('product_ids')
    def onchange_product_ids(self):
        return {'domain': {
            'product_id': [('id', 'in', json.loads(self.product_ids))]}}

    @api.model
    def default_get(self, fields):
        res = super(update_quotation_product, self).default_get(fields)
        if 'job_quotaion_line' in self._context and self._context.get('job_quotaion_line',False):
            job_quotaion_line_id = self.env['job.quotaion.line'].browse(self._context.get('job_quotaion_line',False))
            res['key_word'] = job_quotaion_line_id.key_word
            res['nha_san_xuat'] = job_quotaion_line_id.nha_san_xuat
            res['ma_san_pham'] = job_quotaion_line_id.ma_san_pham
            res['description'] = job_quotaion_line_id.description
            res['product_id'] = job_quotaion_line_id.product_id.id
            res['job_quotaion_line_id'] = job_quotaion_line_id.id
            res['product_ids'] = job_quotaion_line_id.product_ids
        return res

    @api.multi
    def action_update_product(self):
        if self.product_id:
            description = self.description or ''
            key_word = self.key_word or ''
            nha_san_xuat = self.nha_san_xuat or ''
            ma_san_pham = self.ma_san_pham or ''
            for job_quotaion_id in self.job_quotaion_ids:
                domain = [('id','in',job_quotaion_id.line_ids.ids)]
                if key_word != '':
                    domain.append(('key_word','=',key_word))
                if description != '':
                    domain.append(('description','=',description))
                if nha_san_xuat != '':
                    domain.append(('nha_san_xuat','=',nha_san_xuat))
                if ma_san_pham != '':
                    domain.append(('ma_san_pham','=',ma_san_pham))
                job_quotaion_line_ids = self.env['job.quotaion.line'].search(domain)
                for line in job_quotaion_line_ids:
                    line.product_id = self.product_id
                    print "update---%s-%s"%(job_quotaion_id.id,line.product_id.name)