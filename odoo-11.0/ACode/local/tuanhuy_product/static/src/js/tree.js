odoo.define('tuanhuy_product.tree', function (require) {
    "use strict";

    var core = require('web.core');
    var form_common = require('web.form_common');
    var Model = require('web.Model');
    var ListView = require('web.ListView');
    var DataExport_inherit = require('web.DataExport');
    ListView.include({
        load_list: function () {
            var self = this;
            var result = self._super();
            if (self.model != 'stock.move')
                $(".product_onhand").addClass('hidden');
            else {
                if (self.options && self.options.action && self.options.action.context && self.options.action.context && self.options.action.context.active_model == 'product.template') {
                    $(".product_onhand").removeClass('hidden');
                    var active_id = self.options.action.context.active_id
                    new Model('product.template').call('get_onhand_show', [active_id]).then(function (onhand) {
                        $(".product_onhand_value").text(onhand)
                    })
                }
                else {
                    $(".product_onhand").addClass('hidden');
                }
            }
            return result;
        }
    });

    DataExport_inherit.include({
        start: function() {
        var self = this;
        var waitFor = [this._super.apply(this, arguments)];

        this.$fields_list = this.$('.o_fields_list');
        this.$import_compat_radios = this.$('.o_import_compat input');

        waitFor.push(this.rpc('/web/export/formats', {}).then(do_setup_export_formats1));

        var got_fields = new $.Deferred();
        this.$import_compat_radios.change(function(e) {
            self.$('.o_field_tree_structure').remove();

            self.rpc("/web/export/get_fields", {
                model: self.dataset.model,
                import_compat: !!$(e.target).val(),
            }).done(function (records) {
                var compatible_fields = _.map(records, function (record) {return record.id});
                self.$fields_list
                    .find('option')
                    .filter(function () {
                        var option_field = $(this).attr('value');
                        if (compatible_fields.indexOf(option_field) === -1) {
                            return true;
                        }
                    })
                    .remove();
                got_fields.resolve();
                self.on_show_data(records);
            });
        }).eq(0).change();
        waitFor.push(got_fields);

        waitFor.push(this.getParent().get_active_domain().then(function (domain) {
            if (domain === undefined) {
                self.ids_to_export = self.getParent().get_selected_ids();
                self.domain = self.dataset.domain;
            } else {
                self.ids_to_export = false;
                self.domain = domain;
            }
            self.on_show_domain();
        }));

        // waitFor.push(this.show_exports_list());

        return $.when.apply($, waitFor);

        function do_setup_export_formats1(formats) {
            console.log('log2');
            var $fmts = self.$('.o_export_format');

            // _.each(formats, function(format, i) {
            //     var $radio = $('<input/>', {type: 'radio', value: format.tag, name: 'o_export_format_name'});
            //     var $label = $('<label/>', {html: format.label});
            //
            //     if (format.error) {
            //         $radio.prop('disabled', true);
            //         $label.html(_.str.sprintf("%s — %s", format.label, format.error));
            //     }
            //
            //     $fmts.append($("<div/>").append($radio, $label));
            // });

            self.$export_format_inputs = $fmts.find('input');
            self.$export_format_inputs.last().prop('checked', true);
        }
    }
    });
});