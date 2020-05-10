odoo.define('hidden_onchange.form_view', function (require) {
    var FormView = require('web.FormView');
    var time = require('web.time');
    var core = require('web.core');
    var data = require('web.data');
    var session = require('web.session');
    var utils = require('web.utils');
    var Model = require('web.Model');
    var ListView = require('web.ListView');
    var datepicker = require('web.datepicker');
    var ViewManager = require('web.ViewManager');
    var framework = require('web.framework');
    var crash_manager = require('web.crash_manager');
    var _t = core._t;
    var _lt = core._lt;
    var QWeb = core.qweb;

    FormView.include({
        do_onchange: function(widget) {
            var self = this;
            if (self._onchange_specs === undefined) {
                self._build_onchange_specs();
            }
            var onchange_specs = self._onchange_specs;
            try {
                var def = $.when({});
                var change_spec = widget ? onchange_specs[widget.name] : null;
                if (!widget || (!_.isEmpty(change_spec) && change_spec !== "0")) {
                    var ids = []
                      , trigger_field_name = widget ? widget.name : self._onchange_fields
                      , values = self._get_onchange_values()
                      , context = new data.CompoundContext(self.dataset.get_context());
                    if (widget && widget.build_context()) {
                        context.add(widget.build_context());
                    }
                    if (self.dataset.parent_view) {
                        var parent_name = self.dataset.parent_view.get_field_desc(self.dataset.child_name).relation_field;
                        context.add({
                            field_parent: parent_name
                        });
                    }
                    if (self.datarecord.id && !data.BufferedDataSet.virtual_id_regex.test(self.datarecord.id)) {
                        ids.push(self.datarecord.id);
                    }
                    if (!((self.model == 'purchase.order') && (trigger_field_name == 'order_line'))){
                        def = self.alive(self.dataset.call("onchange", [ids, values, trigger_field_name, onchange_specs, context]));
                    }

                }
                this.onchanges_mutex.exec(function() {
                    return def.then(function(response) {
                        var fields = {};
                        if (widget) {
                            fields[widget.name] = widget.field;
                        } else {
                            fields = self.fields_view.fields;
                        }
                        var defs = [];
                        _.each(fields, function(field, fieldname) {
                            if (field && field.change_default) {
                                var value_;
                                if (response.value && (fieldname in response.value)) {
                                    value_ = response.value[fieldname];
                                } else {
                                    value_ = self.fields[fieldname].get_value();
                                }
                                var condition = fieldname + '=' + value_;
                                if (value_) {
                                    defs.push(self.alive(new Model('ir.values').call('get_defaults', [self.model, condition])).then(function(results) {
                                        if (!results.length) {
                                            return response;
                                        }
                                        if (!response.value) {
                                            response.value = {};
                                        }
                                        for (var i = 0; i < results.length; ++i) {
                                            var triplet = results[i];
                                            response.value[triplet[1]] = triplet[2];
                                        }
                                        return response;
                                    }));
                                }
                            }
                        });
                        return _.isEmpty(defs) ? response : $.when.apply(null, defs);
                    }).then(function(response) {
                        return self.on_processed_onchange(response);
                    });
                });
                return this.onchanges_mutex.def;
            } catch (e) {
                console.error(e);
                crash_manager.show_message(e);
                return $.Deferred().reject();
            }
        },
    });

});