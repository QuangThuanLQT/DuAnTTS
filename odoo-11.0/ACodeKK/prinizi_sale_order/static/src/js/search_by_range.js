odoo.define('prinizi_sale_order.tree', function (require) {
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
    var QWeb = core.qweb;
    var _t = core._t;
    var _lt = core._lt;
    // var checkState = false;
    var NewListView = require('rowno_in_tree.ListNumber');

    ListView.List.include(/** @lends instance.web.ListView.List# */{
        pad_table_to: function (count) {
            count = 0
            if (this.records.length >= count ||
                    _(this.columns).any(function(column) { return column.meta; })) {
                return;
            }
            var cells = [];
            cells.push('<td title="#">&nbsp;</td>');
            if (this.options.selectable) {
                cells.push('<td class="o_list_record_selector"></td>');
            }
            _(this.columns).each(function(column) {
                if (column.invisible === '1') {
                    return;
                }
                cells.push('<td title="' + column.string + '">&nbsp;</td>');
            });
            if (this.options.deletable) {
                cells.push('<td class="o_list_record_delete"></td>');
            }
            cells.unshift('<tr>');
            cells.push('</tr>');

            var row = cells.join('');
            this.$current
                .children('tr:not([data-id])').remove().end()
                .append(new Array(count - this.records.length + 1).join(row));
        },
    });
    ListView.include({
        render_buttons: function ($node) {
            var self = this;
            this._super.apply(this, arguments);

            if (self.model == 'sale.order' && (self.ViewManager.action.xml_id == 'sale.action_quotations'
                || self.ViewManager.action.xml_id == 'sale.action_orders')) {

                self.prinizi_sale_export_print = $(QWeb.render('prinizi_sale_export_print', {}));
                self.prinizi_sale_export_print.click(function () {
                    var domain = self.dataset.domain;
                    session.get_file({
                        url: '/prinizi_sale_export_print',
                        dataType: 'json',
                        data: {
                            'action': self.ViewManager.action.xml_id,
                            domain: JSON.stringify(domain),
                        },
                        complete: framework.unblockUI,
                        error: crash_manager.rpc_error.bind(crash_manager),
                    });
                });
                if (self.$buttons[0].getElementsByClassName('o_prinizi_sale_print').length == 0) {
                     setTimeout(function () {
                         self.$buttons.append(self.prinizi_sale_export_print)
                     }, 100);
                }
            }
        }
    });
});