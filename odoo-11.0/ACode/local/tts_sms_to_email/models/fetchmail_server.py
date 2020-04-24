import poplib
import base64
import datetime
import dateutil
import email
import hashlib
import hmac
import lxml
import logging
import pytz
import re
import socket
import time
import xmlrpclib
import re

from collections import namedtuple
from email.message import Message
from email.utils import formataddr
from lxml import etree
from werkzeug import url_encode

from odoo import _, api, exceptions, fields, models, tools
from odoo.tools.safe_eval import safe_eval
from datetime import datetime, timedelta, date
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

from imaplib import IMAP4, IMAP4_SSL
from poplib import POP3, POP3_SSL

_logger = logging.getLogger(__name__)
MAX_POP_MESSAGES = 50
MAIL_TIMEOUT = 60

# Workaround for Python 2.7.8 bug https://bugs.python.org/issue23906
poplib._MAXLINE = 65536

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError


class FetchmailServer(models.Model):
    _inherit = 'fetchmail.server'

    @api.model
    def _fetch_mails_sms(self):
        """ Method called by cron to fetch mails from servers """
        return self.search([('state', '=', 'done'), ('type', 'in', ['pop', 'imap'])]).fetch_mail_sms()

    @api.multi
    def fetch_mail_sms(self):
        """ WARNING: meant for cron usage only - will commit() after each email! """
        additionnal_context = {
            'fetchmail_cron_running': True
        }
        end_date = datetime.datetime.now() - datetime.timedelta(minutes=30)
        MailThread = self.env['mail.thread']
        for server in self:
            _logger.info('start checking for new emails on %s server %s', server.type, server.name)
            additionnal_context['fetchmail_server_id'] = server.id
            additionnal_context['server_type'] = server.type
            count, failed = 0, 0
            imap_server = None
            pop_server = None
            if server.type == 'imap':
                try:
                    imap_server = server.connect()
                    imap_server.select()
                    result, data = imap_server.search(None, '(SEEN)')
                    for num in list(reversed(data[0].split())):
                        res_id = None
                        result, data = imap_server.fetch(num, '(RFC822)')
                        try:
                            res_id = MailThread.with_context(**additionnal_context).message_process_sms(end_date,
                                                                                                        data[0][1],
                                                                                                        save_original=server.original)

                        except Exception:
                            _logger.info('Failed to process mail from %s server %s.', server.type, server.name,
                                         exc_info=True)
                            failed += 1
                        if res_id == 'stop':
                            break
                        # if res_id and server.action_id:
                        #     server.action_id.with_context({
                        #         'active_id': res_id,
                        #         'active_ids': [res_id],
                        #         'active_model': self.env.context.get("thread_model", server.object_id.model)
                        #     }).run()
                        # self._cr.commit()
                        count += 1
                    _logger.info("Fetched %d email(s) on %s server %s; %d succeeded, %d failed.", count, server.type,
                                 server.name, (count - failed), failed)
                except Exception:
                    _logger.info("General failure when trying to fetch mail from %s server %s.", server.type,
                                 server.name, exc_info=True)
                finally:
                    if imap_server:
                        imap_server.close()
                        imap_server.logout()
        return True


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    @api.model
    def message_process_sms(self, end_date, message, save_original=False):

        if isinstance(message, xmlrpclib.Binary):
            message = str(message.data)
        # Warning: message_from_string doesn't always work correctly on unicode,
        # we must use utf-8 strings here :-(
        if isinstance(message, unicode):
            message = message.encode('utf-8')
        msg_txt = email.message_from_string(message)

        # parse the message, verify we are not in a loop by checking message_id is not duplicated
        msg = self.message_parse(msg_txt, save_original=save_original)

        # thread_id = self.message_route_process_sms(msg_txt, msg)
        values = {}
        format = re.compile('<.*?>')
        message = re.sub(format, '', msg.get('body', False))
        data = self.env['tts.sms.inbox'].get_data_from_message(message)
        if len(data) >= 3:
            phone = data[1].strip()
            body = data[2].strip()
            date = msg.get('date')
            # customer_data = self._get_customer_data(body)
            values.update({
                'date': date if date else False,
                'phone': phone,
                'body': body,
            })
            if datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S") < end_date:
                return 'stop'
            sms_id = False
            if body[:3] in ['(1)', '(0)']:
                sms_id = self.env['tts.sms.inbox'].search([('phone', '=', phone), ('date', '=', date)], limit=1)
                if not sms_id:
                    domain = [('phone', '=', phone)]
                    if body[0:3] == '(0)':
                        date_start = (
                            datetime.strptime(date, DEFAULT_SERVER_DATETIME_FORMAT) - timedelta(seconds=1)).strftime(
                            DEFAULT_SERVER_DATETIME_FORMAT)
                        domain.append(('body', '=like', '(1)%'))
                        domain.append(('date', '<=', date))
                        domain.append(('date', '>=', date_start))
                    elif body[0:3] == '(1)':
                        date_start = (
                            datetime.strptime(date, DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(seconds=1)).strftime(
                            DEFAULT_SERVER_DATETIME_FORMAT)
                        domain.append(('body', '=like', '(0)%'))
                        domain.append(('date', '>=', date))
                        domain.append(('date', '<=', date_start))
                    sms_id = self.search(domain, limit=1)
            else:
                date_end = date
                date_start = (
                    datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S") - datetime.timedelta(seconds=5)).strftime(
                    "%Y-%m-%d %H:%M:%S")
                sms_ids = self.env['tts.sms.inbox'].search([('phone', '=', phone), ('date', '>=', date_start), ('date', '<=', date_end)],
                                      order='date desc')
                if sms_ids:
                    sms_id = sms_ids[0]
            if sms_id and sms_id.created_voucher == False:
                if body[0:3] == '(0)':
                    body_html = body[3:]
                    if body_html in sms_id.body:
                        return True
                    body_sms = sms_id.body[3:] + body_html
                elif body[0:3] == '(1)':
                    if body[3:] in sms_id.body:
                        return True
                    body_sms = body[3:] + sms_id.body[3:] if len(sms_id.body) > 3 else ''
                else:
                    if body in sms_id.body:
                        return True
                    body_sms = sms_id.body + body

                data_write = {'body': body_sms}
                sms_id.write(data_write)
                return sms_id.id
            if not sms_id:
                self.env['tts.sms.inbox'].create(values)
        return True
