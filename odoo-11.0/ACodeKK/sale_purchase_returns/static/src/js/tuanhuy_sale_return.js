odoo.define('sale_purchase_returns.sale_return', function (require) {
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
        var self = this;
        if (self.get_fields_values().sale_order_return == true) {
          setTimeout(function () {
            $(".o_td_label .class_date_return").text('Thời gian trả hàng');
          },200)
        }
      }
      if (self.model == 'purchase.order') {
        var self = this;
        if (self.get_fields_values().purchase_order_return == true) {
          setTimeout(function () {
            $(".o_td_label .class_date_return").text('Thời gian trả hàng');
          },200)
        }
      }
    },
  });

});


