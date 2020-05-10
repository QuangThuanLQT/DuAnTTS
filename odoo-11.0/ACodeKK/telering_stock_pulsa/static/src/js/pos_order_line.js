odoo.define('pos_sarangoci_modifier_orderline', function (require) {

    var PosBaseWidget = require('point_of_sale.BaseWidget');
    var chrome = require('point_of_sale.chrome');
    var gui = require('point_of_sale.gui');
    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');
    var floors = require('pos_restaurant.floors');
    var core = require('web.core');
    var Model = require('web.DataModel');
    var PopupWidget = require('point_of_sale.popups');


    var QWeb = core.qweb;
    var _t = core._t;

    screens.OrderWidget.include({
        render_orderline: function(orderline) {
            var self = this;
            var node = this._super(orderline);
            var button_view = node.querySelector("button.show-note");
            if(button_view){
                button_view.addEventListener('click',function () {
                    var line = self.pos.get_order().get_selected_orderline();
                    self.pos.gui.show_popup('ViewNotePopup', {
                        'title': _t("View note"),
                        'value': line.get_note(),
                    });

                });
            }

            return node;
        },

    });

    models.load_fields("pos.config", "orderline_symbol");
    PosBaseWidget.include({
        format_currency_orderline : function (amount, precision) {
            this.pos.dp['precision'] = 1;
            precision = -1;
            if(this.pos && this.pos.config && this.pos.config.orderline_symbol) {
                return this.format_currency(amount, precision);
            }
            return this.format_currency_no_symbol(amount,precision);
        },
        format_currency_no_symbol:function (amount,precision) {
            var result = this._super(amount,precision);
            if(result.indexOf(".") >= 0){
                return result.substring(0,result.length - 3)
            }
            return result

        }


    });

    var ViewNotePopup = PopupWidget.extend({
        template: 'ViewNotePopup',
        events: _.extend({}, PopupWidget.prototype.events, {

        }),
        init: function(parent, options){
            this._super(parent, options);
        },
        show: function(options){
            options = options || {};
            this._super(options);
        },

    });

    gui.define_popup({name:'ViewNotePopup', widget: ViewNotePopup});
    return ViewNotePopup;

});
