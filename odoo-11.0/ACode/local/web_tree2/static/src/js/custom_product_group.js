odoo.define('web_tree2.custom_product_group', function(require) {
	"use strict";

    var core = require('web.core');
    var ListView = require('web.ListView');
    var Model = require('web.Model');
    var _t = core._t;
    var _lt = core._lt;
    var QWeb = core.qweb;

    ListView.List.include({
        render: function () {
            var self = this;
            if (self.view.$el.parents('.o_form_field.o_form_field_one2many').hasClass('custom-group-by') || self.view.$el.parents('.o_form_field.o_form_field_many2many').hasClass('custom-group-by')) {
                this.group_by = 'categ_id';
                this.parent_group_by = 'parent_id';
                this.group_by_model = 'product.category';
                new Model(this.group_by_model)
                    .query()
                    .all()
                    .then(function(data) {
                        var datas=[];
                        if (data.length) {
                            self.raw_data = data;
                            function prepare_group(item) {
                                var childs_data = [];
                                var product_count = item.product_count;
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
                            self.datas = datas;
                            self.render_tree2_view(datas);
                            self.pad_table_to(4);
                        }
                    });
//                this.view.$el.find('th.oe_list_header_group_by').removeClass('oe_sortable').empty();
            } else {
                this._super.apply(this, arguments);
            }
        },
        render_tree2_view: function(datas) {
            var self = this;
            var raw_conrent = '';
            for(var i=0,len=datas.length;i<len;i++) {
                raw_conrent += self.render_content(datas[i]);
            }
            this.$current.html(raw_conrent);
            // add listen event group header click
//            var group_headers = this.view.$el.find('.o_group_header');
//            this.$current.delegate('tr.o_group_header', 'click', {self: self}, self.group_header_click)
//            for(var i=0,len=group_headers.length;i<len;i++) {
//                $(group_headers[i]).de('click', {self: self}, self.group_header_click);
//                $(group_headers[i]).on('dragover', {self: self}, self.drag_over);
//                $(group_headers[i]).on('dragenter', {self: self}, self.header_drag_enter);
//                $(group_headers[i]).on('dragleave', {self: self}, self.header_drag_leave);
//                $(group_headers[i]).on('drop', {self: self}, self.header_drag_drop);
//            }
        },
        render_content: function(item, space) {
            var self = this;
            var html = '';
            space = space || 0;
            if (item.product_count>0) {
                var header = $(QWeb.render('CustomGroupByView', {
                    item: item,
                    parent: item.parent_id,
                    count_columns: _.filter(self.columns, function(c) {return !c.invisible}).length})
                    );
                header.find('.o_group_name').prepend($('<span>').css({
                    'float': 'left',
                    'white-space': 'pre'
                }).text(new Array(space).join('   ')))
                html += header[0].outerHTML;
            }

            if (item.children.length) {
                for(var i=0,len=item.children.length;i<len;i++) {
                    html += self.render_content(item.children[i], space+3);
                }
            }
            return html;
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
            console.log('123123');

            // add event for drag item
            var drag_item = self.view.$el.find('tr[data-id="'+ self.drag_item_id +'"]');
            drag_item.on('dragstart', {self: self}, self.drag_start);
            drag_item.on('dragover', {self: self}, self.drag_over);
            drag_item.on('dragenter', {self: self}, self.drag_enter);
            drag_item.on('dragleave', {self: self}, self.drag_leave);
            drag_item.on('drop', {self: self}, self.drag_drop);
            drag_item.on('click', {self: self}, self.row_clicked);

            // change group
            if (target_parent != self.drag_item_parent_id) {
                var args = {};
                args[self.group_by] = target_parent;
                new Model(self.dataset.model)
                    .call("write", [[self.drag_item_id], args])
                    .done(function(data) {
                        drag_item.attr('parent-id',target_parent);
                        // remove class and item
                        self.view.$el.find('.custom-drag-enter').removeClass('custom-drag-enter');
                        self.view.$el.find('.fake-drag-drop').remove();
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
                        self.view.$el.find('.custom-drag-enter').removeClass('custom-drag-enter');
                        self.view.$el.find('.fake-drag-drop').removeClass('fake-drag-drop');
                        self.drag_item = false;
                    })
            }

            // remove class and item
            self.view.$el.find('.custom-drag-enter').removeClass('custom-drag-enter');
            self.view.$el.find('.fake-drag-drop').remove();
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
        row_clicked: function (e, view) {
            var self = this;
            var target = $(e.currentTarget);
            if (target.hasClass('o_group_header')) {
                var data_id = target.attr('data-id');
                var caret = target.find('span.fa');
                var childs_target = self.view.$el.find('tr[parent-id="'+ data_id +'"]');
                this.selected_data_id = data_id;

                if (caret.hasClass('fa-caret-right')) {
                    caret.removeClass('fa-caret-right').addClass('fa-caret-down');
                    childs_target.show();

                    // render product
                    var html = QWeb.render('CustomGroupBy.rows', _.extend({}, this, {
                        render_cell: function () { return self.render_cell.apply(self, arguments); }
                    }));
                    target.after(html);

                    // add event row drag drop
                    var drag_drop_items = self.view.$el.find('tr[parent-id="'+ data_id +'"].o_item_drag_drop');
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
                    console.log('12321');
                    $('tr[parent-id="'+ data_id +'"].o_item_drag_drop').remove()
                    childs_target.hide();
                }
            } else {
                this._super.apply(this, arguments);
            }
        }
    });

});