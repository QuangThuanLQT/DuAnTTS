# -*- coding: utf-8 -*-

from odoo import models, fields, api

class config_product_print(models.Model):
    _name = 'config.product.print'

    def chat_lieu_in_hinh(self):
        chat_lieu_in_hinh = self.env.ref('prinizi_sales_config_print_attribute.chat_lieu_in_hinh')
        return [('attribute','=',chat_lieu_in_hinh.id)]

    product_id = fields.Many2one('product.template', required=1)
    attribute_value_id = fields.Many2one('product.attribute.value', string='Attributes', ondelete='restrict')
    name = fields.Char(compute='get_product_print_name', string="Name", store=True)

    lung_ao_its_ids = fields.One2many('lung.ao.its','config_product_print_id')
    lung_ao_in_hinh = fields.Many2many('prinizi.product.attribute.value', 'lung_ao_in_hinh_rel', 'config_product_id', 'product_attribute_print_id',domain=chat_lieu_in_hinh, string='Chất liệu in hình')

    mat_truoc_ao_its_ids = fields.One2many('mat.truoc.ao.its', 'config_product_print_id')
    mat_truoc_ao_in_hinh = fields.Many2many('prinizi.product.attribute.value', 'mat_truoc_ao_in_hinh_rel', 'config_product_id', 'product_attribute_print_id',domain=chat_lieu_in_hinh, string='Chất liệu in hình')

    ong_quan_its_ids = fields.One2many('ong.quan.its', 'config_product_print_id')
    ong_quan_in_hinh = fields.Many2many('prinizi.product.attribute.value', 'ong_quan_in_hinh_rel', 'config_product_id', 'product_attribute_print_id',domain=chat_lieu_in_hinh, string='Chất liệu in hình')

    ong_tay_ao_its_ids = fields.One2many('ong.tay.ao.its', 'config_product_print_id')
    ong_tay_ao_in_hinh = fields.Many2many('prinizi.product.attribute.value', 'ong_tay_ao_in_hinh_rel', 'config_product_id', 'product_attribute_print_id',domain=chat_lieu_in_hinh, string='Chất liệu in hình')

    @api.depends('product_id','attribute_value_id')
    def get_product_print_name(self):
        for rec in self:
            rec.name = "%s (%s)" % (rec.product_id.name,rec.attribute_value_id.name)


class lung_ao_its(models.Model):
    _name = 'lung.ao.its'

    def chat_lieu_in_ten_so(self):
        chat_lieu_in_ten_so = self.env.ref('prinizi_sales_config_print_attribute.chat_lieu_in_ten_so')
        return [('attribute','=',chat_lieu_in_ten_so.id)]

    def mau_in_ten_so(self):
        mau_in_ten_so = self.env.ref('prinizi_sales_config_print_attribute.mau_in_ten_so')
        return [('attribute','=',mau_in_ten_so.id)]

    chat_lieu_in_ten_so = fields.Many2one('prinizi.product.attribute.value',domain=chat_lieu_in_ten_so, string='Chất liệu in tên số')
    mau_in_ten_so = fields.Many2many('prinizi.product.attribute.value', 'mau_in_lung_ao_its_rel', 'config_product_id', 'product_attribute_print_id',domain=mau_in_ten_so, string='Màu in tên số')
    config_product_print_id = fields.Many2one('config.product.print')

class mat_truoc_ao_its(models.Model):
    _name = 'mat.truoc.ao.its'

    def chat_lieu_in_ten_so(self):
        chat_lieu_in_ten_so = self.env.ref('prinizi_sales_config_print_attribute.chat_lieu_in_ten_so')
        return [('attribute', '=', chat_lieu_in_ten_so.id)]

    def mau_in_ten_so(self):
        mau_in_ten_so = self.env.ref('prinizi_sales_config_print_attribute.mau_in_ten_so')
        return [('attribute', '=', mau_in_ten_so.id)]

    chat_lieu_in_ten_so = fields.Many2one('prinizi.product.attribute.value', domain=chat_lieu_in_ten_so, string='Chất liệu in tên số')
    mau_in_ten_so = fields.Many2many('prinizi.product.attribute.value', 'mau_in_mat_truoc_ao_its_rel', 'config_product_id', 'product_attribute_print_id', domain=mau_in_ten_so, string='Màu in tên số')
    config_product_print_id = fields.Many2one('config.product.print')

class ong_quan_its(models.Model):
    _name = 'ong.quan.its'

    def chat_lieu_in_ten_so(self):
        chat_lieu_in_ten_so = self.env.ref('prinizi_sales_config_print_attribute.chat_lieu_in_ten_so')
        return [('attribute', '=', chat_lieu_in_ten_so.id)]

    def mau_in_ten_so(self):
        mau_in_ten_so = self.env.ref('prinizi_sales_config_print_attribute.mau_in_ten_so')
        return [('attribute', '=', mau_in_ten_so.id)]

    chat_lieu_in_ten_so = fields.Many2one('prinizi.product.attribute.value', domain=chat_lieu_in_ten_so, string='Chất liệu in tên số')
    mau_in_ten_so = fields.Many2many('prinizi.product.attribute.value', 'mau_in_ong_quan_its_rel', 'config_product_id', 'product_attribute_print_id', domain=mau_in_ten_so, string='Màu in tên số')
    config_product_print_id = fields.Many2one('config.product.print')

class ong_tay_ao_its(models.Model):
    _name = 'ong.tay.ao.its'

    def chat_lieu_in_ten_so(self):
        chat_lieu_in_ten_so = self.env.ref('prinizi_sales_config_print_attribute.chat_lieu_in_ten_so')
        return [('attribute', '=', chat_lieu_in_ten_so.id)]

    def mau_in_ten_so(self):
        mau_in_ten_so = self.env.ref('prinizi_sales_config_print_attribute.mau_in_ten_so')
        return [('attribute', '=', mau_in_ten_so.id)]

    chat_lieu_in_ten_so = fields.Many2one('prinizi.product.attribute.value', domain=chat_lieu_in_ten_so, string='Chất liệu in tên số')
    mau_in_ten_so = fields.Many2many('prinizi.product.attribute.value', 'mau_in_ong_tay_ao_its_rel', 'config_product_id', 'product_attribute_print_id', domain=mau_in_ten_so, string='Màu in tên số')
    config_product_print_id = fields.Many2one('config.product.print')

