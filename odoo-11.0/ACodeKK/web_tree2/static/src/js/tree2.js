odoo.define('web_tree2.Tree2View', function (require) {
"use strict";

var ajax = require('web.ajax');
var core = require('web.core');
var formats = require('web.formats');
var time = require('web.time');
var View = require('web.View');
var Model = require('web.Model');
var data = require('web.data');

var _t = core._t;
var _lt = core._lt;
var QWeb = core.qweb;
var list_widget_registry = core.list_widget_registry;

var Tree2View = View.extend({
    display_name: _lt('Tree2'),
    template: 'Tree2View',

    init: function(group, opts) {
        var self = this;
        this._super.apply(this, arguments);
        this.has_been_loaded = $.Deferred();
        this.tree_id = _.uniqueId();

        console.log('this.tree_id', this.tree_id);

        // The type of the view:
        // gantt = classic gantt view (default)
        // consolidate = values of the first children are consolidated in the gantt's task
        // planning = children are displayed in the gantt's task
        this.type = this.fields_view.arch.attrs.type || 'tree2';
        this.group_by = this.fields_view.arch.attrs.group_by || 'categ_id';
        this.parent_group_by = this.fields_view.arch.attrs.parent_group_by || 'parent_categ_id';
        this.group_by_model = this.fields_view.arch.attrs.group_by_model || 'product.category';

        this.columns = [];
        this.setup_columns(this.fields_view.fields, this.grouped);

        this.tasks = [];

        // gather the fields to get
        var fields = [];
        fields.concat(['name']);
        this.fields_to_fetch = fields;
    },
    defaults: _.extend({}, View.prototype.defaults, {
        // records can be selected one by one
        selectable: false,
        // list rows can be deleted
        deletable: false,
        // whether the column headers should be displayed
        header: true,
        // display addition button, with that label
        addable: _lt("Create"),
        // whether the list view can be sorted, note that once a view has been
        // sorted it can not be reordered anymore
        sortable: false,
        // whether the view rows can be reordered (via vertical drag & drop)
        reorderable: false,
        action_buttons: true,
        //whether the editable property of the view has to be disabled
        disable_editable_mode: false,
    }),
    willStart: function () {
        var self = this;

        var defs = [];
        defs.push(this._super());

        if (!$.isFunction($.fn.tree)) {
            defs.push(ajax.loadJS('/web_tree2/static/lib/jqTree/tree.jquery.js'));
            defs.push(ajax.loadCSS('/web_tree2/static/lib/jqTree/tree.css'));
        }

        return $.when.apply($, defs);
    },

    start: function () {
        this.$el.addClass(this.fields_view.arch.attrs.class);
        // this.load_gantt();
        this.has_been_loaded.resolve();
        return this._super();
    },

    do_search: function (domains, contexts, group_bys) {
        var self = this;

        console.log('do_search', domains, contexts, group_bys);

        self.last_domains = domains;
        self.last_contexts = contexts;
        self.last_group_bys = group_bys;

        // select the group by
        var n_group_bys = [];
        if (this.fields_view.arch.attrs.default_group_by) {
            n_group_bys = this.fields_view.arch.attrs.default_group_by.split(',');
        }
        if (group_bys.length) {
            n_group_bys = group_bys;
        }

        console.log('n_group_bys', n_group_bys);

        var fields = self.fields_to_fetch.concat(n_group_bys);

        return $.when(this.has_been_loaded).then(function() {
            return new Model(self.dataset.model)
                .query()
                .filter(domains)
                .context(contexts)
                .group_by(n_group_bys);
        }).then(function(data) {
            self.first_groups = data;
            return self.dataset.read_slice(fields, {
                domain: domains,
                context: contexts
            }).then(function (data) {
                _.each(data, function(d) {return d.model = self.dataset.model;})
                self.tasks = data;
                return self.prepare_data(data, n_group_bys);
            });
        });
    },

    prepare_data: function (tasks, group_bys) {
        var self = this;
        if (self.type === 'tree2' || group_bys.length === 0) {
            return self.on_data_loaded(tasks, group_bys);
        }
    },

    on_data_loaded: function (tasks, group_bys, color_by_group) {
        var self = this;
        this.$div_with_id = $('<div>').attr('id', this.tree_id);
        this.$div_with_id.wrap('<div></div>');
        this.$div = this.$div_with_id.parent().css({});
        this.$div.prependTo(document.body);

        if (this.group_by_model) {
            new Model(this.group_by_model)
                .query()
                .all()
                .then(function(data) {
                    var datas=[];
                    if (data.length) {
                        this.raw_data = data;
                        function prepare_group(item) {
                            var childs_data = [];
                            var product_count = _.filter(self.tasks, function(t) { return t[self.group_by][0] == item.id }).length;

                            var childs = _.filter(data, function(c) {
                              return c.parent_id[0] == item.id
                            })
                            var child_len = childs.length;
                            if (len>0) {
                                for(var i=0;i<child_len;i++) {
                                    var child_data = prepare_group(childs[i]);
                                    childs_data.push(child_data)
                                    product_count += child_data.product_count
                                }
                            }

                            return {
                                name : item.name,
                                id : item.id,
                                children: childs_data,
                                product_count: product_count,
                                parent_id: item[self.parent_group_by] && item[self.parent_group_by][0] || false
                            };
                        }

                        for (var i=0,len=data.length;i<len;i++) {
                            if (!data[i].parent_id) {
                                datas.push(prepare_group(data[i]))
                            }
                        }
                        this.datas = datas;
                        self.render_tree2_view(datas);
                    }
                });
        }
    },
    render_tree2_view: function(datas) {
        var self = this;
        var raw_conrent = $(QWeb.render('Tree2ViewContent', this));

        for(var i=0,len=datas.length;i<len;i++) {
            raw_conrent.find('table').append(self.render_content(datas[i]));
        }

        // add listen event group header click
        var group_headers = $(raw_conrent).find('.o_group_header');
        for(var i=0,len=group_headers.length;i<len;i++) {
            $(group_headers[i]).on('click', {self: self}, self.group_header_click);
            $(group_headers[i]).on('dragover', {self: self}, self.drag_over);
            $(group_headers[i]).on('dragenter', {self: self}, self.header_drag_enter);
            $(group_headers[i]).on('dragleave', {self: self}, self.header_drag_leave);
            $(group_headers[i]).on('drop', {self: self}, self.header_drag_drop);
        }

        self.$el.empty();
        self.$el.append(raw_conrent)
    },
    render_content: function(item, space) {
        var self = this;
        var html = '';
        space = space || 0;
        if (item.product_count>0) {
            var header = $(QWeb.render('Tree2ViewGroup', {item: item, parent: item.parent_id, count_columns: this.count_columns}));
            header.find('.o_group_name').prepend($('<span>').css({
                'float': 'left',
                'white-space': 'pre'
            }).text(new Array(space).join('   ')))
            html += header[0].outerHTML;

            // html += QWeb.render('Tree2ViewItems', {items: item.products, parent: item.id, columns: self.columns, render_cell: this.render_cell});
        }

        if (item.children.length) {
            for(var i=0,len=item.children.length;i<len;i++) {
                html += self.render_content(item.children[i], space+3);
            }
        }
        return html;
    },
    group_header_click: function(e) {
        var self = e.data.self;
        var target_id = $(this).attr('data-id');
        var caret = $(this).find('span.fa');
        var childs_target = self.$el.find('tr[parent-id="'+ target_id +'"]');

        if (caret.hasClass('fa-caret-right')) {
            caret.removeClass('fa-caret-right').addClass('fa-caret-down');
            childs_target.show();
            $(this).parent().after(self.render_products(parseInt(target_id)));

            // add event row drag drop
            var drag_drop_items = self.$el.find('tbody[data-id="'+ target_id +'"] tr.o_item_drag_drop');
            for(var i=0,len=drag_drop_items.length;i<len;i++) {
                $(drag_drop_items[i]).on('dragstart', {self: self}, self.drag_start);
                $(drag_drop_items[i]).on('dragover', {self: self}, self.drag_over);
                $(drag_drop_items[i]).on('dragenter', {self: self}, self.drag_enter);
                $(drag_drop_items[i]).on('dragleave', {self: self}, self.drag_leave);
                $(drag_drop_items[i]).on('drop', {self: self}, self.drag_drop);
                $(drag_drop_items[i]).on('click', {self: self}, self.record_clicked);
            }
        } else {
            for (var i=0,len=childs_target.length;i<len;i++) {
                caret.removeClass('fa-caret-down').addClass('fa-caret-right');
                if ($(childs_target[i]).hasClass('o_group_header') && $(childs_target[i]).find('span.fa').hasClass('fa-caret-down')) {
                    $(childs_target[i]).trigger('click');
                }
            }
            $('tbody[data-id="'+ target_id +'"]').remove()
            childs_target.hide();
        }
    },
    render_products: function(target_id) {
        var self = this;
        var html = '';
        var products = _.filter(self.tasks, function(t) { return t[self.group_by][0] == target_id });
        if (products.length) {
            html += QWeb.render('Tree2ViewItems', {items: products, parent: target_id, columns: self.columns, render_cell: self.render_cell});
        }
        return html;
    },
    get_parent_id: function(child_id) {
        var self = this;
        var relation = []
        var child = _.filter(self.raw_data, function(r) {return r.id == child_id})
        if (child[self.parent_group_by]) {
            relation.concat(self.get_parent_id(child[self.parent_group_by]))
        }
        return relation.concat(child_id)
    },
    drag_start: function(e) {
        var self = e.data.self;
        self.drag_item = this.outerHTML;
        self.drag_item_id = parseInt($(this).attr('data-id'));
        self.drag_item_parent_id = parseInt($(this).attr('parent-id'));
        $(this).addClass('fake-drag-drop')[0];
    },
    drag_over: function(e) {
        var self = e.data.self;
        e.preventDefault();
    },
    drag_enter: function(e) {
        var self = e.data.self;
        $(this).addClass('custom-drag-enter');
    },
    drag_leave: function(e) {
        var self = e.data.self;
        $(this).removeClass('custom-drag-enter');
    },
    drag_drop: function(e) {
        var self = e.data.self;
        var target_parent = parseInt($(this).attr('parent-id'));
        $(this).before(self.drag_item);

        // add event for drag item
        var drag_item = self.$el.find('tr[data-id="'+ self.drag_item_id +'"]');
        drag_item.on('dragstart', {self: self}, self.drag_start);
        drag_item.on('dragover', {self: self}, self.drag_over);
        drag_item.on('dragenter', {self: self}, self.drag_enter);
        drag_item.on('dragleave', {self: self}, self.drag_leave);
        drag_item.on('drop', {self: self}, self.drag_drop);
        drag_item.on('click', {self: self}, self.record_clicked);

        // change group
        if (target_parent != self.drag_item_parent_id) {
            var args = {};
            args[self.group_by] = target_parent;
            new Model(self.dataset.model)
                .call("write", [[self.drag_item_id], args])
                .done(function(data) {
                    drag_item.attr('parent-id',target_parent);
                    // remove class and item
                    self.$el.find('.custom-drag-enter').removeClass('custom-drag-enter');
                    self.$el.find('.fake-drag-drop').remove();
                    self.drag_item = false;
                    console.log(data);
                    _.map(self.tasks, function(task) {
                        if (task.id == parseInt(self.drag_item_id)) {
                            task[self.group_by][0] = parseInt(target_parent);
                        }
                        return  task
                    })
                })
                .fail(function(err) {
                    self.$el.find('.custom-drag-enter').removeClass('custom-drag-enter');
                    self.$el.find('.fake-drag-drop').removeClass('fake-drag-drop');
                    self.drag_item = false;
                })
        }

        // remove class and item
        self.$el.find('.custom-drag-enter').removeClass('custom-drag-enter');
        self.$el.find('.fake-drag-drop').remove();
        self.drag_item = false;
    },
    header_drag_enter: function(e) {
        var self = e.data.self;
        $(this).addClass('custom-drag-enter');
    },
    header_drag_leave: function(e) {
        var self = e.data.self;
        $(this).removeClass('custom-drag-enter');
    },
    header_drag_drop: function(e) {
        var self = e.data.self;
        var target_id = parseInt($(this).attr('data-id'));
        self.$el.find('tbody[data-id="'+ target_id +'"]').append(self.drag_item);

        // add event for drag item
        var drag_item = self.$el.find('tr[data-id="'+ self.drag_item_id +'"]');
        drag_item.on('dragstart', {self: self}, self.drag_start);
        drag_item.on('dragover', {self: self}, self.drag_over);
        drag_item.on('dragenter', {self: self}, self.drag_enter);
        drag_item.on('dragleave', {self: self}, self.drag_leave);
        drag_item.on('drop', {self: self}, self.drag_drop);
        drag_item.on('click', {self: self}, self.record_clicked);

        // change group
        if (target_id != self.drag_item_parent_id) {
            var args = {};
            args[self.group_by] = target_id;
            new Model(self.dataset.model)
                .call("write", [[self.drag_item_id], args])
                .done(function(data) {
                    drag_item.attr('parent-id',target_id);
                    // remove class and item
                    self.$el.find('.custom-drag-enter').removeClass('custom-drag-enter');
                    self.$el.find('.fake-drag-drop').remove();
                    self.drag_item = false;
                    _.map(self.tasks, function(task) {
                        if (task.id == parseInt(self.drag_item_id)) {
                            task[self.group_by][0] = parseInt(target_id);
                        }
                        return  task
                    })
                })
                .fail(function(err) {
                    self.$el.find('.custom-drag-enter').removeClass('custom-drag-enter');
                    self.$el.find('.fake-drag-drop').removeClass('fake-drag-drop');
                    self.drag_item = false;
                })
        }
    },
    record_clicked: function(e) {
        var self = e.data.self;
        var target_id = parseInt($(this).attr('data-id'));
        self.do_action({
            type:'ir.actions.act_window',
            view_type: 'form',
            view_mode: 'form',
            views: [[false, 'form']],
            res_model: self.dataset.model,
            res_id: target_id,
        })
    },
    setup_columns: function (fields, grouped) {
        this.columns.splice(0, this.columns.length);
        this.columns.push.apply(this.columns,
            _(this.fields_view.arch.children).map(function (field) {
                var id = field.attrs.name;
                return for_(id, fields[id], field);
        }));
        if (grouped) {
            this.columns.unshift(new ListView.MetaColumn('_group'));
        }

        this.visible_columns = _.filter(this.columns, function (column) {
            return column.invisible !== '1';
        });

        this.aggregate_columns = _(this.visible_columns).invoke('to_aggregate');
        this.count_columns = this.visible_columns.length + (this.options.selectable ? 1 : 0) + (this.options.deletable ? 1 : 0)
    },
    render_cell: function (record, column) {
        if (column.type == 'many2one') {
            return record[column['id']][1]
        } else {
            return record[column['id']]
        }
    },
});

core.view_registry.add('tree2', Tree2View);

function for_ (id, field, node) {
    var description = _.extend({tag: node.tag}, field, node.attrs);
    var tag = description.tag;
    var Type = list_widget_registry.get_any([
        tag + '.' + description.widget,
        tag + '.'+ description.type,
        tag
    ]);
    return new Type(id, node.tag, description);
}

return Tree2View;
});