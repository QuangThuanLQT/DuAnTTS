odoo.define('job_quotation.custom_list_view', function (require) {
    "use strict";

    var core = require('web.core');
    var ListView = require('web.ListView');
    var Model = require('web.Model');

    var _t = core._t;
    var QWeb = core.qweb;

    // var One2ManyListView = core.one2many_view_registry.get('list');
    // One2ManyListView.include({
    //     _on_blur_one2many: function() {
    //         if (this.model == 'job.quotaion.line')
    //     }
    // })
    // ListView.include

    ListView.List.include({
        init: function(group, opts) {
            var self = this;
            var res = self._super(group, opts);
            self.$current
                .undelegate('tr','click')
                .delegate('tr', 'click', function(e) {
                    var row_id = self.row_id(e.currentTarget);
                    if (row_id) {
                        e.stopPropagation();
                        if (!self.dataset.select_id(row_id)) {
                            if (self.view.model != "job.quotaion.line") {
                                throw new Error(_t("Could not find id in dataset"));
                            }
                        }
                        if (self.dataset.select_id(row_id)) {
                            self.row_clicked(e);
                        }
                    }
                });
        },
        render_record: function(record) {
            var self = this;
            var res = self._super(record);
            if (self.view.model == "job.quotaion.line") {
                _.each(record.attributes.child_ids, function(r) {
                    new Model('job.quotaion.line')
                        .query()
                        .filter([['id', '=', r]])
                        .all()
                        .then(function (data) {
                            var _clone = _.clone(record);
                            _clone.attributes = data[0];
                            console.log(_clone);
                            var data_id = $(res).attr('data-id');
                            var target = self.$current.find('tr[data-id="'+ data_id +'"]');
                            // var html = QWeb.render('ListView.row', {
                            //     columns: self.columns,
                            //     options: self.options,
                            //     record: _clone,
                            //     row_parity: 'odd',
                            //     view: self.view,
                            //     render_cell: function() {
                            //         return self.render_cell.apply(self, arguments);
                            //     }
                            // });
                            // $('tr[data-id="'+ _clone.attributes.id +'"').remove();
                            // target.after(html);
                        });
                });
            }

            return res;
        }
    })

});