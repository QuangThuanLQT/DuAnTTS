odoo.define('tts_modifier_sale_return.sale_order', function (require) {
    var time = require('web.time');
    var core = require('web.core');
    var data = require('web.data');
    var session = require('web.session');
    var utils = require('web.utils');
    var Model = require('web.Model');
    var ListView = require('web.ListView');
    var FormView = require('web.FormView');
    var datepicker = require('web.datepicker');
    var ViewManager = require('web.ViewManager')
    var framework = require('web.framework');
    var crash_manager = require('web.crash_manager');
    var _t = core._t;
    var _lt = core._lt;
    var QWeb = core.qweb;
    // var checkState = false;
    var domainRemove = [];

    FormView.include({
        // load_record: function (record) {
        //     var self = this;
        //     self._super.apply(self, arguments);
        //     if (self.model == 'sale.order') {
        //         if (self.get_fields_values().reason_cancel) {
        //             setTimeout(function () {
        //                 $(".o_form_button_edit").addClass('hidden');
        //             }, 900)
        //         }
        //     }
        // },
        //
        load_record: function (record) {
            var self = this;
            self._super.apply(self, arguments);
            if (self.model == 'sale.order') {
                if (self.get_fields_values().trang_thai_dh && (self.get_fields_values().trang_thai_dh == 'delivery'
                    || self.get_fields_values().trang_thai_dh == 'done' || self.get_fields_values().trang_thai_dh == 'reverse_tranfer'
                    || self.get_fields_values().trang_thai_dh == 'cancel')) {

                    setTimeout(function () {
                        $(".o_form_button_edit").addClass('hidden');
                    }, 400)

                }
                else {

                    setTimeout(function () {
                        $(".o_form_button_edit").removeClass('hidden');
                    }, 400)
                }
            }
        }
    });
});