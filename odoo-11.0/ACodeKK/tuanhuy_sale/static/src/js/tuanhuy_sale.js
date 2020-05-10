odoo.define('tuanhuy_sale.sale', function (require) {
    "use strict";

    var core = require('web.core');
    var FormView = require('web.FormView');
    var ListView = require('web.ListView');
    var Model = require('web.Model');

    var _t = core._t;
    var QWeb = core.qweb;

    ListView.include({
        load_list: function () {
            var self = this;
            var result = self._super();
            setTimeout(function () {
                $(".breadcrumb li:contains('Trả Hàng Bán')").css('background-color', 'Red');
                $(".breadcrumb li:contains('Trả Hàng Mua')").css('background-color', 'Red');
            }, 200)
            return result;
        },
    });

    // ListView.ColumnMonetary.include({
    //   _format: function (row_data, options) {
    //       var options = pyeval.py_eval(this.options || '{}');
    //       //name of currency field is defined either by field attribute, in view options or we assume it is named currency_id
    //       var currency_field = (_.isEmpty(options) === false && options.currency_field) || this.currency_field || 'currency_id';
    //       var currency_id = row_data[currency_field] && row_data[currency_field].value[0];
    //       var currency = session.get_currency(currency_id);
    //       var digits_precision = this.digits || [0,0];
    //       var value = formats.format_value(row_data[this.id].value || 0, {type: this.type, digits: digits_precision}, options.value_if_empty);
    //       if (currency) {
    //           if (currency.position === "after") {
    //               value += '&nbsp;' + currency.symbol;
    //           } else {
    //               value = currency.symbol + '&nbsp;' + value;
    //           }
    //       }
    //       return value;
    //   },
    // })

    ListView.Groups.include({
        render_groups: function (datagroups) {
            var self = this;
            var placeholder = this.make_fragment();
            _(datagroups).each(function (group) {
                if (self.children[group.value]) {
                    self.records.proxy(group.value).reset();
                    delete self.children[group.value];
                }
                var child = self.children[group.value] = new (self.view.options.GroupsType)(self.view, {
                    records: self.records.proxy(group.value),
                    options: self.options,
                    columns: self.columns
                });
                self.bind_child_events(child);
                child.datagroup = group;

                var $row = child.$row = $('<tr class="o_group_header">');
                if (group.openable && group.length) {
                    $row.click(function (e) {
                        if (!$row.data('open')) {
                            $row.data('open', true)
                                .find('span.fa')
                                .removeClass('fa-caret-right')
                                .addClass('fa-caret-down');
                            child.open(self.point_insertion(e.currentTarget));
                        } else {
                            $row.removeData('open')
                                .find('span.fa')
                                .removeClass('fa-caret-down')
                                .addClass('fa-caret-right');
                            child.close();
                            // force recompute the selection as closing group reset properties
                            var selection = self.get_selection();
                            $(self).trigger('selected', [selection.ids, this.records]);
                        }
                    });
                }
                placeholder.appendChild($row[0]);

                var $group_column = $('<th class="o_group_name">').appendTo($row);
                // Don't fill this if group_by_no_leaf but no group_by
                if (group.grouped_on) {
                    var row_data = {};
                    row_data[group.grouped_on] = group;
                    var group_label = _t("Undefined");
                    var group_column = _(self.columns).detect(function (column) {
                        return column.id === group.grouped_on;
                    });
                    if (group_column) {
                        try {
                            group_label = group_column.format(row_data, {
                                value_if_empty: _t("Undefined"),
                                process_modifiers: false
                            });
                        } catch (e) {
                            group_label = _.str.escapeHTML(row_data[group_column.id].value);
                        }
                    } else {
                        group_label = group.value;
                        var grouped_on_field = self.view.fields_get[group.grouped_on];
                        if (grouped_on_field && grouped_on_field.type === 'selection') {
                            group_label = _.find(grouped_on_field.selection, function (selection) {
                                return selection[0] === group.value;
                            });
                        }
                        if (group_label instanceof Array) {
                            group_label = group_label[1];
                        }
                        if (group_label === false) {
                            group_label = _t('Undefined');
                        }
                        group_label = _.str.escapeHTML(group_label);
                    }

                    // group_label is html-clean (through format or explicit
                    // escaping if format failed), can inject straight into HTML
                    $group_column.html(_.str.sprintf("%s (%d)",
                        group_label, group.length));

                    if (group.length && group.openable) {
                        // Make openable if not terminal group & group_by_no_leaf
                        $group_column.prepend('<span class="fa fa-caret-right" style="padding-right: 5px;">');
                    } else {
                        $group_column.prepend('<span class="fa">');
                    }
                }
                self.indent($group_column, group.level);

                if (self.options.selectable) {
                    $row.append('<td>');
                }
                _(self.columns).chain()
                    .filter(function (column) {
                        return column.invisible !== '1';
                    })
                    .each(function (column) {
                        if (column.meta) {
                            // do not do anything
                        } else if (column.id in group.aggregates) {
                            var r = {};
                            r[column.id] = {value: group.aggregates[column.id]};
                            if (column.id !== 'order_partner_id' && column.id !== 'partner_id') {
                                $('<td class="oe_number o_list_number">')
                                    .html(column.format(r, {process_modifiers: false}))
                                    .appendTo($row);
                            }
                            else {
                                $('<td>').html(group.aggregates[column.id]).appendTo($row);
                            }
                        } else {
                            $row.append('<td>');
                        }
                    });
                if (self.options.deletable) {
                    $row.append('<td class="oe_list_group_pagination">');
                }
            });
            return placeholder;
        },
    });

    FormView.include({
        load_record: function (record) {
            var self = this;
            self._super.apply(self, arguments);

            if (self.model == 'purchase.order') {
                setTimeout(function () {
                    $(".breadcrumb li:contains('Trả Hàng Mua')").css('background-color', 'Red');
                }, 200)
            }
            ;

            if (self.model == 'sale.order') {
                setTimeout(function () {
                    $(".breadcrumb li:contains('Trả Hàng Bán')").css('background-color', 'Red');
                }, 200)
                var self = this;
                if (self.get_fields_values().state == 'sale' || self.get_fields_values().state == 'done' || self.get_fields_values().state == 'cancel') {
                    setTimeout(function () {
                        $(".btn-group button:contains('In')").removeClass('hidden');
                    }, 400)
                    console.log('edit');
                    setTimeout(function () {
                        $(".o_form_button_edit").addClass('hidden');
                    }, 400)
                }
                else {
                    setTimeout(function () {
                        $(".btn-group button:contains('In')").addClass('hidden');
                    }, 400)
                    setTimeout(function () {
                        $(".o_form_button_edit").removeClass('hidden');
                    }, 400)
                }
            }
            ;
            if (self.model == 'purchase.order') {
                var self = this;
                if (self.get_fields_values().state == 'purchase' || self.get_fields_values().state == 'done' || self.get_fields_values().state == 'cancel') {
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

