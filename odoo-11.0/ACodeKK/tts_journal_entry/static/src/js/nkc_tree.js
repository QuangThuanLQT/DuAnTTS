odoo.define('tts_journal_entry.nkc_tree', function (require) {
    "use strict";

    var time = require('web.time');
    var core = require('web.core');
    var data = require('web.data');
    var session = require('web.session');
    var utils = require('web.utils');
    var Model = require('web.Model');
    var ListView = require('web.ListView');
    var datepicker = require('web.datepicker');
    var ViewManager = require('web.ViewManager')
    var _t = core._t;
    var QWeb = core.qweb;
    var FormView = require('web.FormView');
    var framework = require('web.framework');
    var crash_manager = require('web.crash_manager');

    ListView.include({
        render_buttons: function ($node) {
            var self = this;
            this._super.apply(this, arguments);

            self.$buttons.find('.o_nkc_print_excel').remove();

            if (self.model == 'tts_journal_entry.nhatkychung') {
                self.$nkc_print = $(QWeb.render('nkc.buttons_print_excel', {}));
                self.$nkc_print.click(function () {
                   session.get_file({
                                url: '/print_nkc_excel',
                                dataType: 'json',
                                data: {
                                },
                                complete: framework.unblockUI,
                                error: crash_manager.rpc_error.bind(crash_manager),
                            });
                });
                self.$buttons.append(self.$nkc_print)
            }
        }
    });
});