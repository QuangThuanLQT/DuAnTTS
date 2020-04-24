odoo.define('cptuanhuy_modifier_sale_purchase.sale', function (require) {
    "use strict";

    var core = require('web.core');
    var FormView = require('web.FormView');
    var ListView = require('web.ListView');
    var Model = require('web.Model');

    var _t = core._t;
    var QWeb = core.qweb;

    FormView.include({
        load_record: function (record) {
            var self = this;
            self._super.apply(self, arguments);
            if (self.model == 'sale.order') {
                setTimeout(function () {
                    $(".breadcrumb li:contains('Trả Hàng Bán')").css('background-color', 'Red');
                }, 200)
                var self = this;
                if (self.get_fields_values().state == 'sale' || self.get_fields_values().state == 'done' || self.get_fields_values().state == 'cancel') {
                    setTimeout(function () {
                        $(".o_form_button_edit").removeClass('hidden');
                    }, 400)
                }
                // else {
                //     setTimeout(function () {
                //         $(".o_form_button_edit").removeClass('hidden');
                //     }, 400)
                // }
            }
            ;
            if (self.model == 'purchase.order') {
                var self = this;
                if (self.get_fields_values().state == 'purchase' || self.get_fields_values().state == 'done' || self.get_fields_values().state == 'cancel') {
                    setTimeout(function () {
                        $(".o_form_button_edit").removeClass('hidden');
                    }, 400)
                }
                // else {
                //     setTimeout(function () {
                //         $(".o_form_button_edit").removeClass('hidden');
                //     }, 400)
                // }
            }

        },
    });

    var Dropdown_item = require('web.form_common');
    var utils = require('web.utils');
    console.log('drop');
    Dropdown_item.CompletionFieldMixin.init = function () {

        this.limit = 12;
        this.orderer = new utils.DropMisordered();
        this.can_create = this.node.attrs.can_create == "false" ? false : true;
        this.can_write = this.node.attrs.can_write == "false" ? false : true;

    };

});
// (function () {
//     var instance = openerp;
//     var _t = instance.web._t,
//         _lt = instance.web._lt;
//     var QWeb = instance.web.qweb;
//
//
//     core.form.CompletionFieldMixin = {
//         init: function () {
//             this.limit = 1;
//             this.orderer = new instance.web.DropMisordered();
//
//         },
//     };
// })();

