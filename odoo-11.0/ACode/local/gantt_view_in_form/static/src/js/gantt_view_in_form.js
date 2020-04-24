odoo.define('gantt_view_in_form.gantt_view_in_form', function (require) {
    "use strict";

var ControlPanel = require('web.ControlPanel');
var core = require('web.core');
var data = require('web.data');
var Dialog = require('web.Dialog');
var common = require('web.form_common');
var ListView = require('web.ListView');
require('web.ListEditor'); // one must be sure that the include of ListView are done (for eg: add start_edition methods)
var Model = require('web.DataModel');
var session = require('web.session');
var utils = require('web.utils');
var ViewManager = require('web.ViewManager');
var WebClient = require('web.WebClient');
var _t = core._t;
var QWeb = core.qweb;
var COMMANDS = common.commands;
var list_widget_registry = core.list_widget_registry;
var AbstractManyField = require('web.form_relational').AbstractManyField;

var action_manager = null;

var X2ManyViewManager = ViewManager.extend({
    custom_events: {
        // Catch event scrollTo to prevent scrolling to the top when using the
        // pager of List and Kanban views in One2Many fields
        'scrollTo': function() {},
    },
    init: function(parent, dataset, views, flags, x2many_views) {
        // By default, render buttons and pager in X2M fields, but no sidebar
        flags = _.extend({}, flags, {
            headless: false,
            search_view: false,
            action_buttons: true,
            pager: true,
            sidebar: false,
        });
        this.control_panel = new ControlPanel(parent, "X2ManyControlPanel");
        this.set_cp_bus(this.control_panel.get_bus());
        this._super(parent, dataset, views, flags);
        this.registry = core.view_registry.extend(x2many_views);
    },
    start: function() {
        this.control_panel.prependTo(this.$el);
        return this._super();
    },
    switch_mode: function(mode, unused) {
        if (mode !== 'form') {
            return this._super(mode, unused);
        }
        var self = this;
        var id = self.x2m.dataset.index !== null ? self.x2m.dataset.ids[self.x2m.dataset.index] : null;
        var pop = new common.FormViewDialog(this, {
            res_model: self.x2m.field.relation,
            res_id: id,
            context: self.x2m.build_context(),
            title: _t("Open: ") + self.x2m.string,
            create_function: function(data, options) {
                return self.x2m.data_create(data, options);
            },
            write_function: function(id, data, options) {
                return self.x2m.data_update(id, data, options).done(function() {
                    self.x2m.reload_current_view();
                });
            },
            alternative_form_view: self.x2m.field.views ? self.x2m.field.views.form : undefined,
            parent_view: self.x2m.view,
            child_name: self.x2m.name,
            read_function: function(ids, fields, options) {
                return self.x2m.data_read(ids, fields, options);
            },
            form_view_options: {'not_interactible_on_create':true},
            readonly: self.x2m.get("effective_readonly")
        }).open();
        pop.on("elements_selected", self, function() {
            self.x2m.reload_current_view();
        });
    },
});
var FieldX2Many = AbstractManyField.extend({
    multi_selection: false,
    disable_utility_classes: true,
    x2many_views: {},
    view_options: {},
    default_view: 'tree',
    init: function(field_manager, node) {
        this._super(field_manager, node);

        this.is_loaded = $.Deferred();
        this.initial_is_loaded = this.is_loaded;
        this.is_started = false;
        this.set_value([]);
    },
    start: function() {
        this._super.apply(this, arguments);
        var self = this;

        this.load_views();
        var destroy = function() {
            self.is_loaded = self.is_loaded.then(function() {
                self.renderElement();
                self.viewmanager.destroy();
                return $.when(self.load_views()).done(function() {
                    self.reload_current_view();
                });
            });
        };
        this.is_loaded.done(function() {
            self.on("change:effective_readonly", self, destroy);
        });
        this.view.on("on_button_cancel", this, destroy);
        this.is_started = true;
        this.reload_current_view();
    },
    load_views: function() {
        var self = this;

        var view_types = this.node.attrs.mode;
        view_types = !!view_types ? view_types.split(",") : [this.default_view];
        var views = [];
        _.each(view_types, function(view_type) {
            if (! _.include(["list", "tree", "graph", "kanban"], view_type)) {
                throw new Error(_.str.sprintf(_t("View type '%s' is not supported in X2Many."), view_type));
            }
            var view = {
                view_id: false,
                view_type: view_type === "tree" ? "list" : view_type,
                fields_view: self.field.views && self.field.views[view_type],
                options: {},
            };
            if(view.view_type === "list") {
                _.extend(view.options, {
                    action_buttons: false, // to avoid 'Save' and 'Discard' buttons to appear in X2M fields
                    addable: null,
                    selectable: self.multi_selection,
                    sortable: true,
                    import_enabled: false,
                    deletable: true
                });
                if (self.get("effective_readonly")) {
                    _.extend(view.options, {
                        deletable: null,
                        reorderable: false,
                    });
                }
            } else if (view.view_type === "kanban") {
                _.extend(view.options, {
                    action_buttons: true,
                    confirm_on_delete: false,
                });
                if (self.get("effective_readonly")) {
                    _.extend(view.options, {
                        action_buttons: false,
                        quick_creatable: false,
                        creatable: false,
                        read_only_mode: true,
                    });
                }
            }
            views.push(view);
        });
        this.views = views;

        this.viewmanager = new X2ManyViewManager(this, this.dataset, views, this.view_options, this.x2many_views);
        this.viewmanager.x2m = self;
        var def = $.Deferred().done(function() {
            self.initial_is_loaded.resolve();
        });
        this.viewmanager.on("controller_inited", self, function(view_type, controller) {
            controller.x2m = self;
            if (view_type == "list") {
                if (self.get("effective_readonly")) {
                    controller.on('edit:before', self, function (e) {
                        e.cancel = true;
                    });
                    _(controller.columns).find(function (column) {
                        if (!(column instanceof list_widget_registry.get('field.handle'))) {
                            return false;
                        }
                        column.modifiers.invisible = true;
                        return true;
                    });
                }
            } else if (view_type == "graph") {
                self.reload_current_view();
            }
            def.resolve();
        });
        this.viewmanager.on("switch_mode", self, function(n_mode) {
            $.when(self.commit_value()).done(function() {
                if (n_mode === "list") {
                    utils.async_when().done(function() {
                        self.reload_current_view();
                    });
                }
            });
        });
        utils.async_when().done(function () {
            self.$el.addClass('o_view_manager_content');
            self.alive(self.viewmanager.attachTo(self.$el));
        });
        return def;
    },
    reload_current_view: function() {
        var self = this;
        self.is_loaded = self.is_loaded.then(function() {
            var view = self.get_active_view();
            if (view.type === "list") {
                view.controller.current_min = 1;
                return view.controller.reload_content();
            } else if (view.controller.do_search) {
                return view.controller.do_search(self.build_domain(), self.dataset.get_context(), []);
            }
        }, undefined);
        return self.is_loaded;
    },
    get_active_view: function () {
        /**
         * Returns the current active view if any.
         */
        return (this.viewmanager && this.viewmanager.active_view);
    },
    set_value: function(value_) {
        var self = this;
        this._super(value_).then(function () {
            if (self.is_started && !self.no_rerender) {
                return self.reload_current_view();
            }
        });
    },
    commit_value: function() {
        var view = this.get_active_view();
        if (view && view.type === "list" && view.controller.__focus) {
            return $.when(this.mutex.def, view.controller._on_blur_one2many());
        }
        return this.mutex.def;
    },
    is_syntax_valid: function() {
        var view = this.get_active_view();
        if (!view){
            return true;
        }
        switch (this.viewmanager.active_view.type) {
        case 'form':
            return _(view.controller.fields).chain()
                .invoke('is_valid')
                .all(_.identity)
                .value();
        case 'list':
            return view.controller.is_valid();
        }
        return true;
    },
    is_false: function() {
        return _(this.dataset.ids).isEmpty();
    },
    is_set: function() {
        // always consider that field is "set" hence displayed
        return true;
    },
});
var FieldOne2ManyGantt = FieldX2Many.extend({
    init: function() {
        this._super.apply(this, arguments);
        this.x2many_views = {
            kanban: core.view_registry.get('one2many_kanban'),
            list: core.one2many_view_registry.get('list'),
            // gantt: core.view_registry.get('gantt'),

        };
    },
    start: function() {
        // var dataset = new data.DataSetSearch(action_manager,'project.planning',JSON.parse('{"lang":"vi_VN","tz":"Asia/Ho_Chi_Minh","uid":1,"params":{"action":1052,"view_type":"gantt","model":"project.planning","_push_me":false}}'),false);
        // var views = [[false,"list"],[false,"form"],[false,"pivot"],[false,"gantt"]];
        // var flags = {
        //     action_buttons: true,
        //     auto_search: true,
        //     display_title: true,
        //     headless: false,
        //     pager: true,
        //     search_disable_custom_filters: undefined,
        //     search_view: true,
        //     sidebar: true,
        //     views_switcher: true
        // };
        // console.log('action_manager',action_manager);
        // var options = {};
        // options.action_manager = action_manager;
        // options.action = JSON.parse('{"groups_id":[],"domain":false,"xml_id":"cptuanhuy_project.action_project_planning","create_date":"2018-12-13 03:39:28","help":false,"res_model":"project.planning","search_view_id":false,"write_uid":[1,"Administrator"],"id":1052,"create_uid":[1,"Administrator"],"display_name":"Kế Hoạch","__last_update":"2018-12-21 07:31:47","views":[[false,"list"],[false,"form"],[false,"pivot"],[false,"gantt"]],"src_model":false,"usage":false,"flags":{"views_switcher":true,"search_view":true,"action_buttons":true,"sidebar":true,"pager":true,"display_title":true,"headless":false,"auto_search":true},"res_id":0,"view_id":false,"view_mode":"list,form,pivot,gantt","write_date":"2018-12-21 07:31:47","view_ids":[],"name":"Kế Hoạch","multi":false,"target":"current","auto_search":true,"type":"ir.actions.act_window","filter":false,"limit":80,"context":{"lang":"vi_VN","tz":"Asia/Ho_Chi_Minh","uid":1,"params":{"action":1052,"view_type":"gantt","model":"project.planning","_push_me":false}},"menu_id":null}');
        // var self = new ViewManager(action_manager,dataset,views,flags,options);
        // var view = JSON.parse('{"button_label":"Gantt view","controller":null,"fields_view":{"name":"project.planning.gantt","arch":{"tag":"gantt","attrs":{"date_start":"date_start","date_stop":"date_end","string":"Kế Hoạch","round_dnd_dates":"true","consolidation":"progress","progress":"progress"},"children":[]},"view_id":1683,"fields":{},"model":"project.planning","type":"gantt","toolbar":{"print":[],"action":[],"relate":[]},"field_parent":false},"icon":"fa-tasks","label":{},"mobile_friendly":false,"multi_record":true,"options":{"action":{"groups_id":[],"domain":false,"xml_id":"cptuanhuy_project.action_project_planning","create_date":"2018-12-13 03:39:28","help":false,"res_model":"project.planning","search_view_id":false,"write_uid":[1,"Administrator"],"id":1052,"create_uid":[1,"Administrator"],"display_name":"Kế Hoạch","__last_update":"2018-12-21 02:39:31","views":[[false,"list"],[false,"form"],[false,"pivot"],[false,"gantt"]],"src_model":false,"usage":false,"flags":{"views_switcher":true,"search_view":true,"action_buttons":true,"sidebar":true,"pager":true,"display_title":true,"headless":false,"auto_search":true},"res_id":0,"view_id":false,"view_mode":"list,form,pivot,gantt","write_date":"2018-12-21 02:39:31","view_ids":[],"name":"Kế Hoạch","multi":false,"target":"current","auto_search":true,"type":"ir.actions.act_window","filter":false,"limit":80,"context":{"lang":"vi_VN","tz":"Asia/Ho_Chi_Minh","uid":1,"params":{"action":1052,"view_type":"gantt","model":"project.planning","_push_me":false}},"menu_id":null},"views_switcher":true,"search_view":true,"action_buttons":true,"sidebar":true,"pager":true,"display_title":true,"headless":false,"auto_search":true},"require_fields":true,"title":"Kế Hoạch","type":"gantt"}');
        // // var node = self.create_view(view, undefined);
        // // view.$fragment = $('<div>');
        // if (view.multi_record) {
        //     self.view_stack = [];
        // } else if (self.view_stack.length > 0 && !(_.last(self.view_stack).multi_record)) {
        //     self.view_stack.pop();
        // }
        // self.view_stack.push(view);
        // self.active_view = view;
        // if (!view.loaded) {
        //     if (!view.controller) {
        //         view.controller = self.create_view(view, undefined);
        //     }
        //     view.$fragment = $('<div>');
        //     view.loaded = view.controller.appendTo(view.$fragment).done(function() {
        //         view.$fragment = view.$fragment.contents();
        //         self.trigger("controller_inited", view.type, view.controller);
        //     });
        // }
        // self.active_search = $.Deferred();
        // if (self.search_view_loaded && self.flags.auto_search && view.controller.searchable !== false) {
        //     $.when(self.search_view_loaded, view.loaded).done(function() {
        //         self.searchview.do_search();
        //     });
        // } else {
        //     self.active_search.resolve();
        // }
        // $.when(view.loaded, self.active_search, self.search_view_loaded).then(function() {
        //     self._display_view(undefined,null).then(function() {
        //         self.trigger('switch_mode', 'gantt', undefined);
        //     })
        //     });


        this.$el.addClass('o_form_field_one2many');
        return this._super.apply(this, arguments);
    },
    commit_value: function() {
        var self = this;
        $('button.gantt_view_in_form_button').remove();
        $('.ifarme_gantt_view').remove();
        var action_id = $('a[data-menu-name="Kế Hoạch"]').attr('data-action-id');
        var origin = window.location.origin;
        var url =  origin + '/web#view_type=gantt&amp;model=project.planning&amp;action='+action_id;
        var element = $('<iframe src="'+url+'" style="width:100%;height: 1700px" class="ifarme_gantt_view">');
        var button_gantt_element = $('<button type="button" class="btn btn-icon fa fa-lg fa-tasks o_cp_switch_gantt gantt_view_in_form_button" style="float:right" data-original-title="Gantt"/>');
        var button_tree_element = $('<button type="button" class="btn btn-icon fa fa-lg fa-list-ul o_cp_switch_list gantt_view_in_form_button active" style="float:right" data-original-title="Danh sách"/>');
        button_gantt_element.click(function () {
            element.removeClass('hidden');
            self.$el.addClass('hidden');
            button_gantt_element.addClass('active');
            button_tree_element.removeClass('active');
        });
        button_tree_element.click(function () {
            element.addClass('hidden');
            self.$el.removeClass('hidden');
            button_gantt_element.removeClass('active');
            button_tree_element.addClass('active');
        });
        self.$el.before(button_gantt_element);
        self.$el.before(button_tree_element);
        element.addClass('hidden');
        self.$el.after(element);
        setTimeout(function(){
            try{
                element.contents().find(".o_control_panel").remove();
                element.contents().find("header").remove();
            }catch (error){}
        }, 5000);
        return this.is_loaded.then(function() {
            var view = self.viewmanager.active_view;
            if(view.type === "list" && view.controller.editable()) {
                return self.mutex.def.then(function () {
                    return view.controller.save_edition();
                });
            }
            return self.mutex.def;
        });
    },
    is_false: function() {
        return false;
    },
});

// var AbstractWebClient = require('web.AbstractWebClient');
// AbstractWebClient.include({
//     set_action_manager: function () {
//         this._super();
//         action_manager = this;
//     }
// });

core.form_widget_registry
    .add('one2many_gantt', FieldOne2ManyGantt);
});