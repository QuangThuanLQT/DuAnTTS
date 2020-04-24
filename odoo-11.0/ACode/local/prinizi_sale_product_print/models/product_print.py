# -*- coding: utf-8 -*-

from odoo import models, fields, api
import json

class PrintAttributeValue_ihr(models.Model):
    _inherit = 'prinizi.product.attribute.value'

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        field_related_one2many = self._context.get('field_related_one2many',False)
        field_related_many2many = self._context.get('field_related_many2many',False)
        field_value = self._context.get('field_value',False)
        product_id = self._context.get('product_id', False)
        attribute_value_id = self._context.get('attribute_value_id', False)
        so_product_id = self._context.get('so_product_id', False)
        if so_product_id:
            product_print_id = self.env['product.print'].browse(so_product_id)
            product_id = product_print_id.product_id.id
            attribute_value_id = product_print_id.attribute_value_id.id
        if product_id and attribute_value_id:
            config_product_print_id = self.env['config.product.print'].search([('product_id', '=', product_id),('attribute_value_id', '=', attribute_value_id)])
            if field_related_one2many:
                chat_lieu = self._context.get('chat_lieu',False)
                mode_chat_lieu = self._context.get('mode_chat_lieu',False)
                if chat_lieu and mode_chat_lieu:
                    line_id = self.env[mode_chat_lieu].search([('chat_lieu_in_ten_so', '=', chat_lieu), ('config_product_print_id', '=', config_product_print_id.id)])
                    domain_ids = line_id.mapped('mau_in_ten_so')
                else:
                    domain_ids = config_product_print_id.mapped(field_related_one2many).mapped(field_value)
                args = [('id', 'in', domain_ids.ids)]
            if field_related_many2many:
                domain_ids = config_product_print_id.mapped(field_related_many2many)
                args = [('id', 'in', domain_ids.ids)]
        return super(PrintAttributeValue_ihr, self).name_search(name=name, args=args, operator=operator, limit=limit)

class vi_tri_in(models.Model):
    _name = 'vi.tri.in'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if 'product_id' in self._context:
            product_id = self._context.get('product_id', False)
            if product_id:
                domain_vi_tri_in = self.env['product.print'].get_vi_tri_its_sp(product_id)
                args += [('code', 'in', domain_vi_tri_in)]
            else:
                args += [('code', 'in', [])]

        if 'vt_in_hinh_product_id' in self._context:
            vt_in_hinh_product_id = self._context.get('vt_in_hinh_product_id', False)
            if vt_in_hinh_product_id:
                domain_vi_tri_in = self.env['product.print'].get_vi_tri_hinh_sp(vt_in_hinh_product_id)
                args += [('code', 'in', domain_vi_tri_in)]
            else:
                args += [('code', 'in', [])]

        res = super(vi_tri_in, self).name_search(name=name, args=args, operator=operator, limit=limit)
        return res

class product_print(models.Model):
    _name = 'product.print'

    def font_chu_so(self):
        font_chu_so = self.env.ref('prinizi_sales_config_print_attribute.font_chu_so')
        return [('attribute','=',font_chu_so.id)]

    product_id = fields.Many2one('product.template', required=1)
    attribute_value_id = fields.Many2one('product.attribute.value', string='Attributes', ondelete='restrict')
    name = fields.Char(compute='get_product_print_name', string="Name", store=True)
    font_chu_so = fields.Many2one('prinizi.product.attribute.value',domain=font_chu_so, string='Font chữ/số mặc định')

    @api.model
    def get_vi_tri_its_sp(self, product_print_id):
        list_vi_tri = [
            'lung_ao_tren_ten_so',
            'lung_ao_giua_ten_so',
            'lung_ao_duoi_ten_so',
            'mat_truoc_ao_nguc_phai_ten_so',
            'mat_truoc_ao_nguc_trai_ten_so',
            'mat_truoc_ao_bung_ten_so',
            'ong_quan_trai_ten_so',
            'ong_quan_phai_ten_so',
            'tay_ao_trai_ten_so',
            'tay_ao_phai_ten_so',
        ]
        list_code = [
            'lung_ao_tren',
            'lung_ao_giua',
            'lung_ao_duoi',
            'mat_truoc_ao_nguc_phai',
            'mat_truoc_ao_nguc_trai',
            'mat_truoc_ao_bung',
            'ong_quan_trai',
            'ong_quan_phai',
            'tay_ao_trai',
            'tay_ao_phai',
        ]
        domain_vi_tri_in = []
        product_print_id = self.browse(product_print_id)
        for i in range(0,len(list_vi_tri)):
            if product_print_id.mapped(list_vi_tri[i]) and product_print_id.mapped(list_vi_tri[i])[0]:
                domain_vi_tri_in.append(list_code[i])
        return domain_vi_tri_in

    @api.model
    def get_vi_tri_hinh_sp(self, product_print_id):
        list_vi_tri = [
            'lung_ao_tren_hinh',
            'lung_ao_giua_hinh',
            'lung_ao_duoi_hinh',
            'mat_truoc_ao_nguc_phai_hinh',
            'mat_truoc_ao_nguc_trai_hinh',
            'mat_truoc_ao_bung_hinh',
            'ong_quan_trai_hinh',
            'ong_quan_phai_hinh',
            'tay_ao_trai_hinh',
            'tay_ao_phai_hinh',
        ]
        list_code = [
            'lung_ao_tren',
            'lung_ao_giua',
            'lung_ao_duoi',
            'mat_truoc_ao_nguc_phai',
            'mat_truoc_ao_nguc_trai',
            'mat_truoc_ao_bung',
            'ong_quan_trai',
            'ong_quan_phai',
            'tay_ao_trai',
            'tay_ao_phai',
        ]
        domain_vi_tri_in = []
        product_print_id = self.browse(product_print_id)
        for i in range(0, len(list_vi_tri)):
            if product_print_id.mapped(list_vi_tri[i]) and product_print_id.mapped(list_vi_tri[i])[0]:
                domain_vi_tri_in.append(list_code[i])
        return domain_vi_tri_in

    @api.multi
    def write(self, val):
        if 'lung_ao_tren' in val and not val.get('lung_ao_tren',False):
            val.update({
                'lung_ao_tren_ten_so' : False,
                'lung_ao_tren_hinh' : False
            })
        if 'lung_ao_giua' in val and not val.get('lung_ao_giua',False):
            val.update({
                'lung_ao_giua_ten_so' : False,
                'lung_ao_giua_hinh' : False
            })
        if 'lung_ao_duoi' in val and not val.get('lung_ao_duoi', False):
            val.update({
                'lung_ao_duoi_ten_so': False,
                'lung_ao_duoi_hinh': False
            })

        if 'mat_truoc_ao_nguc_phai' in val and not val.get('mat_truoc_ao_nguc_phai', False):
            val.update({
                'mat_truoc_ao_nguc_phai_ten_so': False,
                'mat_truoc_ao_nguc_phai_hinh': False
            })
        if 'mat_truoc_ao_nguc_trai' in val and not val.get('mat_truoc_ao_nguc_trai', False):
            val.update({
                'mat_truoc_ao_nguc_trai_ten_so': False,
                'mat_truoc_ao_nguc_trai_hinh': False
            })
        if 'mat_truoc_ao_bung' in val and not val.get('mat_truoc_ao_bung', False):
            val.update({
                'mat_truoc_ao_bung_ten_so': False,
                'mat_truoc_ao_bung_hinh': False
            })

        if 'ong_quan_trai' in val and not val.get('ong_quan_trai', False):
            val.update({
                'ong_quan_trai_ten_so': False,
                'ong_quan_trai_hinh': False
            })
        if 'ong_quan_phai' in val and not val.get('ong_quan_phai', False):
            val.update({
                'ong_quan_phai_ten_so': False,
                'ong_quan_phai_hinh': False
            })

        if 'tay_ao_trai' in val and not val.get('tay_ao_trai', False):
            val.update({
                'tay_ao_trai_ten_so': False,
                'tay_ao_trai_hinh': False
            })
        if 'tay_ao_phai' in val and not val.get('tay_ao_phai', False):
            val.update({
                'tay_ao_phai_ten_so': False,
                'tay_ao_phai_hinh': False
            })

        res = super(product_print, self).write(val)
        return res

    #TODO lung ao
    def chat_lieu_in_ten_so(self):
        chat_lieu_in_ten_so = self.env.ref('prinizi_sales_config_print_attribute.chat_lieu_in_ten_so')
        return [('attribute', '=', chat_lieu_in_ten_so.id)]

    def mau_in_ten_so(self):
        mau_in_ten_so = self.env.ref('prinizi_sales_config_print_attribute.mau_in_ten_so')
        return [('attribute', '=', mau_in_ten_so.id)]

    def chat_lieu_in_hinh(self):
        chat_lieu_in_hinh = self.env.ref('prinizi_sales_config_print_attribute.chat_lieu_in_hinh')
        return [('attribute','=',chat_lieu_in_hinh.id)]

    lung_ao_chat_lieu_its = fields.Many2one('prinizi.product.attribute.value',domain=chat_lieu_in_ten_so, string='Chất liệu in tên số')
    lung_ao_mau_its = fields.Many2one('prinizi.product.attribute.value', domain=mau_in_ten_so, string='Màu in tên số')
    lung_ao_chat_lieu_in_hinh = fields.Many2one('prinizi.product.attribute.value', domain=chat_lieu_in_hinh, string='Chất liệu in hình')

    lung_ao_tren = fields.Boolean(string="Lưng trên")
    lung_ao_tren_ten_so = fields.Boolean(string="Tên và số")
    lung_ao_tren_hinh = fields.Boolean(string="Hình")

    lung_ao_giua = fields.Boolean(string="Lưng giữa")
    lung_ao_giua_ten_so = fields.Boolean(string="Tên và số")
    lung_ao_giua_hinh = fields.Boolean(string="Hình")

    lung_ao_duoi = fields.Boolean(string="Lưng dưới")
    lung_ao_duoi_ten_so = fields.Boolean(string="Tên và số")
    lung_ao_duoi_hinh = fields.Boolean(string="Hình")

    @api.onchange('lung_ao_tren')
    def onchange_lung_ao_tren(self):
        if self.lung_ao_tren == False:
            self.lung_ao_tren_ten_so = False
            self.lung_ao_tren_hinh = False

    @api.onchange('lung_ao_giua')
    def onchange_lung_ao_giua(self):
        if self.lung_ao_giua == False:
            self.lung_ao_giua_ten_so = False
            self.lung_ao_giua_hinh = False

    @api.onchange('lung_ao_duoi')
    def onchange_lung_ao_duoi(self):
        if self.lung_ao_duoi == False:
            self.lung_ao_duoi_ten_so = False
            self.lung_ao_duoi_hinh = False

    @api.onchange('lung_ao_tren_ten_so','lung_ao_giua_ten_so','lung_ao_duoi_ten_so')
    def onchange_lung_ao_chat_lieu_its(self):
        if self.lung_ao_tren_ten_so == False and self.lung_ao_giua_ten_so == False and self.lung_ao_duoi_ten_so == False:
            self.lung_ao_chat_lieu_its = False
            self.lung_ao_mau_its = False

    @api.onchange('lung_ao_tren_hinh', 'lung_ao_giua_hinh', 'lung_ao_duoi_hinh')
    def onchange_lung_ao_chat_lieu_in_hinh(self):
        if self.lung_ao_tren_hinh == False and self.lung_ao_giua_hinh == False and self.lung_ao_duoi_hinh == False:
            self.lung_ao_chat_lieu_in_hinh = False

    # TODO mat truoc ao
    mat_truoc_ao_chat_lieu_its = fields.Many2one('prinizi.product.attribute.value', domain=chat_lieu_in_ten_so,
                                            string='Chất liệu in tên số')
    mat_truoc_ao_mau_its = fields.Many2one('prinizi.product.attribute.value', domain=mau_in_ten_so, string='Màu in tên số')
    mat_truoc_ao_chat_lieu_in_hinh = fields.Many2one('prinizi.product.attribute.value', domain=chat_lieu_in_hinh,
                                                string='Chất liệu in hình')
    mat_truoc_ao_nguc_phai = fields.Boolean(string="Ngực phải")
    mat_truoc_ao_nguc_phai_ten_so = fields.Boolean(string="Tên và số")
    mat_truoc_ao_nguc_phai_hinh = fields.Boolean(string="Hình")

    mat_truoc_ao_nguc_trai = fields.Boolean(string="Ngực trái")
    mat_truoc_ao_nguc_trai_ten_so = fields.Boolean(string="Tên và số")
    mat_truoc_ao_nguc_trai_hinh = fields.Boolean(string="Hình")

    mat_truoc_ao_bung = fields.Boolean(string="Bụng")
    mat_truoc_ao_bung_ten_so = fields.Boolean(string="Tên và số")
    mat_truoc_ao_bung_hinh = fields.Boolean(string="Hình")

    @api.onchange('mat_truoc_ao_nguc_phai')
    def onchange_mat_truoc_ao_nguc_phai(self):
        if self.mat_truoc_ao_nguc_phai == False:
            self.mat_truoc_ao_nguc_phai_ten_so = False
            self.mat_truoc_ao_nguc_phai_hinh = False

    @api.onchange('mat_truoc_ao_nguc_trai')
    def onchange_mat_truoc_ao_nguc_trai(self):
        if self.mat_truoc_ao_nguc_trai == False:
            self.mat_truoc_ao_nguc_trai_ten_so = False
            self.mat_truoc_ao_nguc_trai_hinh = False

    @api.onchange('mat_truoc_ao_bung')
    def onchange_mat_truoc_ao_bung(self):
        if self.mat_truoc_ao_bung == False:
            self.mat_truoc_ao_bung_ten_so = False
            self.mat_truoc_ao_bung_hinh = False

    @api.onchange('mat_truoc_ao_nguc_phai_ten_so', 'mat_truoc_ao_nguc_trai_ten_so', 'mat_truoc_ao_bung_ten_so')
    def onchange_mat_truoc_ao_chat_lieu_its(self):
        if self.mat_truoc_ao_nguc_phai_ten_so == False and self.mat_truoc_ao_nguc_trai_ten_so == False and self.mat_truoc_ao_bung_ten_so == False:
            self.mat_truoc_ao_chat_lieu_its = False
            self.mat_truoc_ao_mau_its = False

    @api.onchange('mat_truoc_ao_nguc_phai_hinh', 'mat_truoc_ao_nguc_trai_hinh', 'mat_truoc_ao_bung_hinh')
    def onchange_mat_truoc_ao_chat_lieu_in_hinh(self):
        if self.mat_truoc_ao_nguc_phai_hinh == False and self.mat_truoc_ao_nguc_trai_hinh == False and self.mat_truoc_ao_bung_hinh == False:
            self.mat_truoc_ao_chat_lieu_in_hinh = False

    # TODO ong quan
    ong_quan_chat_lieu_its = fields.Many2one('prinizi.product.attribute.value', domain=chat_lieu_in_ten_so,
                                                 string='Chất liệu in tên số')
    ong_quan_mau_its = fields.Many2one('prinizi.product.attribute.value', domain=mau_in_ten_so,
                                           string='Màu in tên số')
    ong_quan_chat_lieu_in_hinh = fields.Many2one('prinizi.product.attribute.value', domain=chat_lieu_in_hinh,
                                                     string='Chất liệu in hình')

    ong_quan_trai = fields.Boolean(string="Ống quần trái")
    ong_quan_trai_ten_so = fields.Boolean(string="Tên và số")
    ong_quan_trai_hinh = fields.Boolean(string="Hình")

    ong_quan_phai = fields.Boolean(string="Ống quần phải")
    ong_quan_phai_ten_so = fields.Boolean(string="Tên và số")
    ong_quan_phai_hinh = fields.Boolean(string="Hình")

    @api.onchange('ong_quan_trai')
    def onchange_ong_quan_trai(self):
        if self.ong_quan_trai == False:
            self.ong_quan_trai_ten_so = False
            self.ong_quan_trai_hinh = False

    @api.onchange('ong_quan_phai')
    def onchange_ong_quan_phai(self):
        if self.ong_quan_phai == False:
            self.ong_quan_phai_ten_so = False
            self.ong_quan_phai_hinh = False

    @api.onchange('ong_quan_trai_ten_so', 'ong_quan_phai_ten_so')
    def onchange_ong_quan_chat_lieu_its(self):
        if self.ong_quan_trai_ten_so == False and self.ong_quan_trai_ten_so == False:
            self.ong_quan_chat_lieu_its = False
            self.ong_quan_mau_its = False

    @api.onchange('ong_quan_trai_hinh', 'ong_quan_phai_hinh')
    def onchange_ong_quan_chat_lieu_in_hinh(self):
        if self.ong_quan_trai_hinh == False and self.ong_quan_phai_hinh == False:
            self.ong_quan_chat_lieu_in_hinh = False

    # TODO tay ao
    tay_ao_chat_lieu_its = fields.Many2one('prinizi.product.attribute.value', domain=chat_lieu_in_ten_so,
                                             string='Chất liệu in tên số')
    tay_ao_mau_its = fields.Many2one('prinizi.product.attribute.value', domain=mau_in_ten_so,
                                       string='Màu in tên số')
    tay_ao_chat_lieu_in_hinh = fields.Many2one('prinizi.product.attribute.value', domain=chat_lieu_in_hinh,
                                                 string='Chất liệu in hình')

    tay_ao_trai = fields.Boolean(string="Tay áo trái")
    tay_ao_trai_ten_so = fields.Boolean(string="Tên và số")
    tay_ao_trai_hinh = fields.Boolean(string="Hình")

    tay_ao_phai = fields.Boolean(string="Tay áo phải")
    tay_ao_phai_ten_so = fields.Boolean(string="Tên và số")
    tay_ao_phai_hinh = fields.Boolean(string="Hình")

    @api.onchange('tay_ao_trai')
    def onchange_tay_ao_trai(self):
        if self.tay_ao_trai == False:
            self.tay_ao_trai_ten_so = False
            self.tay_ao_trai_hinh = False

    @api.onchange('tay_ao_phai')
    def onchange_tay_ao_phai(self):
        if self.tay_ao_phai == False:
            self.tay_ao_phai_ten_so = False
            self.tay_ao_phai_hinh = False

    @api.onchange('tay_ao_trai_ten_so', 'tay_ao_phai_ten_so')
    def onchange_tay_ao_chat_lieu_its(self):
        if self.tay_ao_trai_ten_so == False and self.tay_ao_phai_ten_so == False:
            self.tay_ao_chat_lieu_its = False
            self.tay_ao_mau_its = False

    @api.onchange('tay_ao_trai_hinh', 'tay_ao_phai_hinh')
    def onchange_tay_ao_chat_lieu_in_hinh(self):
        if self.tay_ao_trai_hinh == False and self.tay_ao_phai_hinh == False:
            self.tay_ao_chat_lieu_in_hinh = False

    @api.depends('product_id', 'attribute_value_id')
    def get_product_print_name(self):
        for rec in self:
            rec.name = "%s (%s)" % (rec.product_id.name,rec.attribute_value_id.name)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if 'product_ids' in self._context:
            product_ids = self._context.get('product_ids', False)
            if product_ids:
                product_ids = json.loads(product_ids)
                args += [('id', 'in', product_ids)]
            else:
                args += [('id', 'in', [])]
        res = super(product_print, self).name_search(name=name, args=args, operator=operator, limit=limit)
        return res

