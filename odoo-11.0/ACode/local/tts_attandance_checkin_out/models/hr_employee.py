# -*- coding: utf-8 -*-

from odoo import models, fields, api, SUPERUSER_ID, _
import re, uuid
from odoo import exceptions
import socket
import json
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import netifaces
from getmac import getmac
from odoo.http import request
from urllib2 import urlopen
import socket



class hr_employee_inherit(models.Model):
    _inherit = 'hr.employee'

    @api.multi
    def attendance_manual(self, next_action, entered_pin=None, mac_address=None):
        data = request.httprequest
        mac_address = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
        gws = netifaces.gateways()
        mac_address = getmac.get_mac_address(ip=gws['default'].values()[0][0], network_request=False)
        attendances_config_id = self.env['attendances.config'].search([('name', '=', mac_address)], limit=1)
        if not attendances_config_id:
            remote_addr = realip_remote_addr = False
            try:
                remote_addr = data.remote_addr
            except:
                True
            try:
                realip_remote_addr = data.realip_remote_addr
            except:
                True
            result = {
                'remote_addr': remote_addr,
                'realip_remote_addr': realip_remote_addr,
            }
            environ = {}
            for key, value in data.environ.items():
                if type(value) == str:
                    environ.update({
                        key: value
                    })
            result.update({
                'environ': environ
            })
            return {'warning': _(mac_address + "____" + json.dumps(result))}
        res = super(hr_employee_inherit, self).attendance_manual(next_action, entered_pin)
        return res

    @api.multi
    def attendance_action_change(self):
        """ Check In/Check Out action
            Check In: create a new attendance record
            Check Out: modify check_out field of appropriate attendance record
        """
        if len(self) > 1:
            raise exceptions.UserError(_('Cannot perform check in or check out on multiple employees.'))
        action_date = fields.Datetime.now()

        mac_address = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
        attendances_config_id = self.env['attendances.config'].search([('name', '=', mac_address)], limit=1)

        if self.attendance_state != 'checked_in':
            vals = {
                'employee_id': self.id,
                'check_in': action_date,
                'location_in': attendances_config_id.location_name,
                'mac_address_in': mac_address,
                'device_info_in': socket.gethostname(),
            }
            return self.env['hr.attendance'].create(vals)
        else:
            attendance = self.env['hr.attendance'].search([('employee_id', '=', self.id), ('check_out', '=', False)],
                                                          limit=1)
            if attendance:
                attendance.check_out = action_date
                attendance.write({
                    'location_out': attendances_config_id.location_name,
                    'mac_address_out': mac_address,
                    'device_info_out': socket.gethostname(),
                })
            else:
                raise exceptions.UserError(
                    _('Cannot perform check out on %(empl_name)s, could not find corresponding check in. '
                      'Your attendances have probably been modified manually by human resources.') % {
                        'empl_name': self.name, })
            return attendance

    @api.model
    def cron_checkout_user(self):
        attendance_ids = self.env['hr.attendance'].search([('check_out', '=', False)])
        date_now = datetime.now()
        for attendance_id in attendance_ids:
            attendance_id.employee_id.attendance_action('hr_attendance.hr_attendance_action_my_attendances')
            attendance_id.check_out = date_now.date().strftime(DEFAULT_SERVER_DATE_FORMAT) + " 15:00:00"
