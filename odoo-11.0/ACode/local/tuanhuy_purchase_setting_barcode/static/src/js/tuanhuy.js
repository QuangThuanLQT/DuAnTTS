odoo.define('tuanhuy_purchase_setting_barcode.sale_purchase', function (require) {
    "use strict";

    var core = require('web.core');
    var FormView = require('web.FormView');
    var ListView = require('web.ListView');
    var Model = require('web.Model');

    var _t = core._t;
    var QWeb = core.qweb;

    var form_widgets = require('web.form_widgets');
    form_widgets.FieldChar.include({
        store_dom_value: function () {
            this._super();
            if(this.$input && this.$input.hasClass("sale_ma_bin_input")) {
               new Model("purchase.order").call("get_check_add_line", [this.$input.val(),"sale.order"]).then(function (result) {
                  if (result) {
                    setTimeout(function () {
                      $('.order_tree .o_form_field_x2many_list_row_add').addClass('hidden')
                    }, 300);
                  }
                  else {
                    setTimeout(function () {
                      $('.order_tree .o_form_field_x2many_list_row_add').removeClass('hidden')
                    }, 300);
                  }
              });
            }
            if(this.$input && this.$input.hasClass("purchase_ma_bin_input")) {
               new Model("purchase.order").call("get_check_add_line", [this.$input.val(),"purchase.order"]).then(function (result) {
                  if (result) {
                    setTimeout(function () {
                      $('.order_tree .o_form_field_x2many_list_row_add').addClass('hidden')
                    }, 300);
                  }
                  else {
                    setTimeout(function () {
                    $('.order_tree .o_form_field_x2many_list_row_add').removeClass('hidden')
                    }, 300);
                  }
              });
            }
        }
    })

    FormView.include({
          load_record: function (record) {
              var self = this;
              self._super.apply(self, arguments);
              if (self.model == 'purchase.order.line' || self.model == 'purchase.order' || self.model == 'sale.order' || self.model == 'sale.order.line') {
                if ($('.ma_bin_input').length == 0 || ($('.ma_bin_input').length != 0 && !$('.ma_bin_input')[0].value)) {
                  new Model("purchase.order").call("get_check_add_line", ["",self.model]).then(function (result) {
                    if (result) {
                      setTimeout(function () {
                        $('.order_tree .o_form_field_x2many_list_row_add').addClass('hidden')
                      }, 300);
                    }
                    else {
                      setTimeout(function () {
                        $('.order_tree .o_form_field_x2many_list_row_add').removeClass('hidden')
                      }, 300);
                    }
                  });
                }
              }
          },
          start: function() {
            var self = this;
            if (self.model == 'purchase.order.line' || self.model == 'purchase.order' || self.model == 'sale.order' || self.model == 'sale.order.line') {
              if ($('.ma_bin_input').length == 0 || ($('.ma_bin_input').length != 0 && !$('.ma_bin_input')[0].value)) {
                new Model("purchase.order").call("get_check_add_line", ["",self.model]).then(function (result) {
                  if (result) {
                    setTimeout(function () {
                      $('.order_tree .o_form_field_x2many_list_row_add').addClass('hidden')
                    }, 300);
                  }
                  else {
                    setTimeout(function () {
                      $('.order_tree .o_form_field_x2many_list_row_add').removeClass('hidden')
                    }, 300);
                  }
                });
              }
            }
            return this._super();
          },
      });
});

