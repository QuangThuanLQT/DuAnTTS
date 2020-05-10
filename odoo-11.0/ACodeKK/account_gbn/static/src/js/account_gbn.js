odoo.define('account_gbn.gbn', function (require) {
    "use strict";

    var core = require('web.core');
    var FormView = require('web.FormView');
    var ListView = require('web.ListView');
    var Model = require('web.Model');

    var _t = core._t;
    var QWeb = core.qweb;
    FormView.include({
	load_record: function(record) {
        var self = this;
        self._super.apply(self, arguments);
        if (self.model == 'account.payment.gbn') {
            if (self.get_fields_values().state == 'done' || self.get_fields_values().state == 'cancel') {
                self.$buttons.find('.o_form_button_edit').addClass('hidden')
                // console.log('This is my function js first');
            }
            else {
                self.$buttons.find('.o_form_button_edit').removeClass('hidden');
                // console.log('This is my function js first');
            }

        }
    },
  });

});