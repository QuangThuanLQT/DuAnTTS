# -*- coding: utf-8 -*-

from odoo import models, fields, api


class sale_customers(models.Model):
    _inherit = 'res.partner'

    ref = fields.Char(string='Mã KH Nội Bộ', readonly=True, required=True, copy=False, default='New')
    maKH = fields.Char(string='Mã KH')
    kh_birthday = fields.Date(string='Sinh nhật')
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

    #Sale
    property_payment_term_id = fields.Many2one('account.payment.term', company_dependent=True,
                                               string='Customer Payment Terms',
                                               help="This payment term will be used instead of the default one for sale orders and customer invoices",
                                               oldname="property_payment_term")
    credit = fields.Monetary(compute='_credit_debit_get',
                             string='Total Receivable', help="Total amount this customer owes you.")
    trust = fields.Selection([('good', 'Good Debtor'), ('normal', 'Normal Debtor'), ('bad', 'Bad Debtor')],
                             string='Degree of trust you have in this debtor', default='normal', company_dependent=True)
    #Purchase
    property_supplier_payment_term_id = fields.Many2one('account.payment.term', company_dependent=True,
                                                        string='Vendor Payment Terms',
                                                        help="This payment term will be used instead of the default one for purchase orders and vendor bills",
                                                        oldname="property_supplier_payment_term")
    debit = fields.Monetary(compute='_credit_debit_get', string='Total Payable',
                            help="Total amount you have to pay to this vendor.")
    currency_id = fields.Many2one('res.currency', compute='_get_company_currency', readonly=True,
                                  string="Currency", help='Utility field to express amount currency')
    #Fiscal Information
    property_account_position_id = fields.Many2one('account.fiscal.position', company_dependent=True,
                                                   string="Fiscal Position",
                                                   help="The fiscal position will determine taxes and accounts used for the partner.",
                                                   oldname="property_account_position")
    #Accounting Entries
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
