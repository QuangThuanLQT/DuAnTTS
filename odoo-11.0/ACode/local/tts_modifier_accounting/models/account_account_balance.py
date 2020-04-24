# -*- coding: utf-8 -*-

from odoo import models, fields, api
from xlrd import open_workbook
from odoo.exceptions import UserError
import base64
from odoo.tools import float_compare


class account_beginning_balance(models.Model):
    _name = 'account.beginning.balance'

    name = fields.Char(default='Nhập đầu kỳ',string='Tên')
    date = fields.Date(default=fields.Date.context_today, string='Ngày nhập',required=1)
    line_ids = fields.One2many('account.beginning.balance.line','beginning_balance_id')
    type = fields.Selection([('all','All'),('cus','Cus'),('ven','Ven'),('empl','Empl')])
    move_id = fields.Many2one('account.move')
    state = fields.Selection([('draft','Draft'),('done','Done')],default='draft')

    import_data = fields.Binary(string="File Import")

    @api.multi
    def import_data_excel(self):
        for record in self:
            try:
                if record.import_data:
                    data = base64.b64decode(record.import_data)
                    wb = open_workbook(file_contents=data)
                    sheet = wb.sheet_by_index(0)
                    line_data = []
                    for row_no in range(sheet.nrows):
                        if row_no >= 1:
                            line = (
                            map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value),
                                sheet.row(row_no)))
                            if record.type == 'all':
                                try:
                                    code = str(int(float(line[0].strip())))
                                except:
                                    code = line[0].strip()
                                tai_khoan = self.env['account.account'].search([('code','=',code)],limit=1)
                                so_du_no = float(line[1]) if line[1] else 0
                                so_du_co = float(line[2]) if line[2] else 0
                                data = {
                                    'tai_khoan' : tai_khoan.id,
                                    'so_du_no' : so_du_no,
                                    'so_du_co' : so_du_co
                                }
                                line_data.append((0,0,data))
                            else:
                                try:
                                    code = str(int(float(line[0].strip())))
                                except:
                                    code = line[0].strip()
                                tai_khoan = self.env['account.account'].search([('code', '=', code)], limit=1)
                                partner_id = self.env['res.partner'].search(['|',('ref','=',line[1].strip()),('name','=',line[1].strip())], limit=1)
                                so_du_no = float(line[2]) if line[2] else 0
                                so_du_co = float(line[3]) if line[3] else 0
                                data = {
                                    'tai_khoan' : tai_khoan.id,
                                    'partner_id' : partner_id.id,
                                    'so_du_no' : so_du_no,
                                    'so_du_co' : so_du_co
                                }
                                line_data.append((0, 0, data))

                    self.line_ids = None
                    if line_data:
                        self.line_ids = line_data
            except:
                raise UserError('Lỗi format file nhập')

    @api.multi
    def action_import(self):
        for rec in self:
            if not all(line.tai_khoan for line in rec.line_ids):
                raise UserError('Vui lòng điền đủ tài khoản trong các dòng!')
            elif float_compare(sum(rec.line_ids.mapped('so_du_no')),sum(rec.line_ids.mapped('so_du_co')),precision_rounding=2) != 0:
                raise UserError('Tổng số dư nợ phải bằng tổng số dư có!')
            else:
                journal_id = self.env['account.journal'].search([('sequence_id.name', '=', "Miscellaneous Operations")],
                                                                limit=1)
                line_data = []
                for line in rec.line_ids:
                    line_data.append((0,0,{
                        'account_id' : line.tai_khoan.id,
                        'partner_id' : line.partner_id.id,
                        'debit' : line.so_du_no,
                        'credit' : line.so_du_co,
                        'name' : rec.name or '/',
                    }))
                account_move_data = {
                    'journal_id' : journal_id.id,
                    'date' : rec.date,
                    'line_ids' : line_data
                }
                rec.move_id = self.env['account.move'].create(account_move_data)
                rec.move_id.post()
                self.state = 'done'

class account_beginning_balance_line(models.Model):
    _name = 'account.beginning.balance.line'

    beginning_balance_id = fields.Many2one('account.beginning.balance')
    tai_khoan = fields.Many2one('account.account', required=1, string='Tài khoản')
    partner_id = fields.Many2one('res.partner')
    so_du_no = fields.Float(string='Số dư có')
    so_du_co = fields.Float(string='Số dư nợ')


class res_partner_ihr(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def name_get(self):
        res = []
        for record in self:
            if record.ref:
                res.append((record.id,"%s - %s" % (record.ref, record.name)))
            else:
                res.append((record.id,"%s" % (record.name)))
        return res

    @api.depends('is_company', 'name', 'parent_id.name', 'type', 'company_name', 'ref')
    def _compute_display_name(self):
        res = super(res_partner_ihr, self)._compute_display_name()
        return res