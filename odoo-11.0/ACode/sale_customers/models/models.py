# -*- coding: utf-8 -*-

from odoo import models, fields, api


class sale_customers(models.Model):
    _inherit = 'res.partner'
    _name = "res.partner"

    ref = fields.Char(string='Mã KH Nội Bộ', readonly=True, required=True, copy=False, default='New')
    maKH = fields.Char(string='Mã KH', required=True)
    kh_birthday = fields.Date(string='Sinh nhật')
    feosco_business_license = fields.Char(u'Giấy phép kinh doanh')
    group_kh1_id = fields.Many2one('partner.group.hk1', string='PK theo Danh Mục KD')
    group_kh2_id = fields.Many2one('partner.group.hk2', string='PK theo Mô Hình KD')
    sale_type = fields.Selection([('allow', 'Cho phép kinh doanh'), ('stop', 'Ngừng kinh doanh')], string='Trạng thái',
                                 default='allow')
    payment_method = fields.Many2one('account.journal', string='Hình thức thanh toán')
    fax = fields.Char(string='Fax')

    pt_giao_hang = fields.Selection(
        [('1', 'Tới kho lấy hàng'), ('2', 'Giao tới tận nơi'), ('3', 'Giao tới tận nhà')],
        string="Phương thức giao hàng", default='1')
    transport_route_id = fields.Many2one('tuyen.xe', string='Tuyến xe')
    delivery_scope_id = fields.Many2one('pham.vi.giao.hang', string='Phạm vi giao hàng')

    # Sale
    property_payment_term_id = fields.Many2one('account.payment.term', company_dependent=True,
                                               string='Customer Payment Terms',
                                               help="This payment term will be used instead of the default one for sale orders and customer invoices",
                                               oldname="property_payment_term")
    credit = fields.Monetary(compute='_credit_debit_get',
                             string='Total Receivable', help="Total amount this customer owes you.")
    trust = fields.Selection([('good', 'Good Debtor'), ('normal', 'Normal Debtor'), ('bad', 'Bad Debtor')],
                             string='Degree of trust you have in this debtor', default='normal', company_dependent=True)
    # Purchase
    property_supplier_payment_term_id = fields.Many2one('account.payment.term', company_dependent=True,
                                                        string='Vendor Payment Terms',
                                                        help="This payment term will be used instead of the default one for purchase orders and vendor bills",
                                                        oldname="property_supplier_payment_term")
    debit = fields.Monetary(compute='_credit_debit_get', string='Total Payable',
                            help="Total amount you have to pay to this vendor.")
    currency_id = fields.Many2one('res.currency', compute='_get_company_currency', readonly=True,
                                  string="Currency", help='Utility field to express amount currency')
    # Fiscal Information
    property_account_position_id = fields.Many2one('account.fiscal.position', company_dependent=True,
                                                   string="Fiscal Position",
                                                   help="The fiscal position will determine taxes and accounts used for the partner.",
                                                   oldname="property_account_position")
    # Accounting Entries
    property_account_receivable_id = fields.Many2one('account.account', company_dependent=True,
                                                     string="Account Receivable", oldname="property_account_receivable",
                                                     domain="[('internal_type', '=', 'receivable'), ('deprecated', '=', False)]",
                                                     help="This account will be used instead of the default one as the receivable account for the current partner",
                                                     required=True)
    property_account_payable_id = fields.Many2one('account.account', company_dependent=True,
                                                  string="Account Payable", oldname="property_account_payable",
                                                  domain="[('internal_type', '=', 'payable'), ('deprecated', '=', False)]",
                                                  help="This account will be used instead of the default one as the payable account for the current partner",
                                                  required=True)

    @api.model
    def create(self, vals):
        if vals.get('ref', 'New') == 'New':
            vals['ref'] = self.env['ir.sequence'].next_by_code('res.partner') or 'New'
        result = super(sale_customers, self).create(vals)
        return result

    # thêm makh sau tên cho khách hàng
    @api.multi
    def name_get(self):
        res = []
        for record in self:
            if record.ref:
                res.append((record.id, "%s - %s" % (record.ref, record.name)))
            else:
                res.append((record.id, "%s" % (record.name)))
        return res

    # cập nhập địa chỉ
    @api.model
    def _get_default_country_id(self):
        search_country = [('code', '=', 'VN')]
        country = self.env['res.country'].search(search_country, limit=1)
        return country.id if country else False

    @api.onchange('country_id')
    def event_country_change(self):
        if self.country_id:
            self.city = None
            self.district_id = None

    @api.onchange('city')
    def event_city_change(self):
        if self.city:
            self.street2 = None
        else:
            return {}

    street = fields.Many2one('feosco.city', u'Thành phố')
    street2 = fields.Many2one('feosco.district', u'Quận (huyện)',
                              domain="[('city_id', '=', street)]")
    city = fields.Many2one('feosco.ward', 'Phường/Xã', domain="[('district_id.id', '=', street2)]")
    country_id = fields.Many2one('res.country', u'Quốc gia', domain="[('code', '=', 'VN')]",
                                 default=_get_default_country_id)
