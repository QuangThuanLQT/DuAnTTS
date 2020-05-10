odoo.define('access_right.sidebar', function (require) {
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
    var Sidebar = require('web.Sidebar');
    var _t = core._t;
    var _lt = core._lt;
    var QWeb = core.qweb;


    Sidebar.include({
        init: function () {
            this._super.apply(this, arguments);
            var view = this.getParent();
            var self = this;
            if (view.fields_view && view.fields_view.type === "form") {
                if (session.is_superuser) {
                    true
                } else {
                    var model_res_users = new Model("res.users");
                    model_res_users.call("has_group", ["tts_modifier_access_right.group_soan_donggoi"]).done(function (can_export) {
                        if (can_export == true) {
                            self.sections.splice(1, 2);
                        }
                    });
                    // model_res_users.call("has_group", ["tts_modifier_access_right.group_nv_nhap_hang"]).done(function (can_export) {
                    //     if (can_export == true) {
                    //         self.sections.splice(1, 2);
                    //     }
                    // });
                    model_res_users.call("has_group", ["tts_modifier_access_right.group_nv_giao_hang"]).done(function (can_export) {
                        if (can_export == true) {
                            self.sections.splice(1, 2);
                        }
                    });
                }

            }
            if (view.fields_view && view.fields_view.type === "tree") {
                if (session.is_superuser) {
                    true
                } else {
                    var model_res_users = new Model("res.users");
                    model_res_users.call("has_group", ["tts_modifier_access_right.group_soan_donggoi"]).done(function (can_export) {
                        if (can_export == true) {
                            self.sections.splice(1, 2);
                        }
                    });
                    model_res_users.call("has_group", ["tts_modifier_access_right.group_nv_nhap_hang"]).done(function (can_export) {
                        if (can_export == true) {
                            self.sections.splice(1, 2);
                        }
                    });
                    model_res_users.call("has_group", ["tts_modifier_access_right.group_nv_giao_hang"]).done(function (can_export) {
                        if (can_export == true) {
                            self.sections.splice(1, 2);
                        }
                    });
                }
            }
        },
        // add_items: function(section_code, items) {
        //     var self = this;
        //     var _super = this._super;
        //     if (session.is_superuser) {
        //         _super.apply(this, arguments);
        //     } else {
        //         var model_res_users = new Model("res.users");
        //         model_res_users.call("has_group", ["tts_modifier_access_right.group_soan_donggoi"]).done(function(can_export) {
        //             if (can_export) {
        //                 var new_items = items;
        //                 if (section_code === "other") {
        //                     new_items = [];
        //
        //                 }
        //                  _super.call(self, section_code, new_items);
        //             } else {
        //                 _super.apply(this, arguments);
        //             }
        //         });
        //
        //         model_res_users.call("has_group", ["tts_modifier_access_right.access_group_nv_nhap_hang"]).done(function(can_export) {
        //             if (can_export) {
        //                 var new_items = items;
        //                 if (section_code === "other") {
        //                     new_items = [];
        //
        //                 }
        //                  _super.call(self, section_code, new_items);
        //             } else {
        //                 _super.apply(this, arguments);
        //             }
        //         });
        //
        //         model_res_users.call("has_group", ["tts_modifier_access_right.group_nv_giao_hang"]).done(function(can_export) {
        //             if (can_export) {
        //                 var new_items = items;
        //                 if (section_code === "other") {
        //                     new_items = [];
        //
        //                 }
        //                 _super.call(self, section_code, new_items);
        //             } else {
        //                _super.apply(this, arguments);
        //             }
        //         });
        //     }
        // }
    });

    FormView.include({
        load_record: function (record) {
            var self = this;
            self._super.apply(self, arguments);
            if (self.model && self.model === "stock.picking") {
                if (!session.is_superuser) {
                    if ((self.datarecord.state_delivery == 'done' && self.datarecord.check_is_delivery) || (self.datarecord.state_pick == 'done' && self.datarecord.check_is_pick) ||
                        (self.datarecord.state_pack == 'done' && self.datarecord.check_is_pack) || (self.datarecord.state == 'done' && self.datarecord.is_orther_picking) || (self.datarecord.receipt_state == 'done' && self.datarecord.picking_type_code == 'incoming') ||
                        (self.datarecord.internal_transfer_state == 'done' && self.datarecord.is_internal_transfer)) {
                        var model_res_users = new Model("res.users");
                        model_res_users.call("has_group", ["tts_modifier_access_right.group_nv_giao_hang"]).then(function (can_export) {
                            if (can_export == true) {
                                setTimeout(function () {
                                    $(".o_form_button_edit").addClass('hidden');
                                }, 1000)
                            }
                        });
                        model_res_users.call("has_group", ["tts_modifier_access_right.group_soan_donggoi"]).then(function (can_export) {
                            if (can_export == true) {
                                setTimeout(function () {
                                    $(".o_form_button_edit").addClass('hidden');
                                }, 1000)
                            }
                        });
                        model_res_users.call("has_group", ["tts_modifier_access_right.group_nv_nhap_hang"]).then(function (can_export) {
                            if (can_export == true) {
                                setTimeout(function () {
                                    $(".o_form_button_edit").addClass('hidden');
                                }, 1000)
                            }
                        });
                        model_res_users.call("has_group", ["tts_modifier_access_right.group_ql_kho"]).then(function (can_export) {
                            if (can_export == true) {
                                setTimeout(function () {
                                    $(".o_form_button_edit").addClass('hidden');
                                }, 1000)
                            }
                        });
                    }
                    else {
                        setTimeout(function () {
                            $(".o_form_button_edit").removeClass('hidden');
                        }, 1000)
                    }
                }
                setTimeout(function () {
                    $(".o_cp_sidebar li:contains('Xác Nhận Kho')").addClass('hidden');
                    $(".o_cp_sidebar li:contains('Set to draft picking')").addClass('hidden');
                }, 400)
                if (!session.is_superuser) {
                    setTimeout(function () {
                        $(".o_cp_sidebar li:contains('Delete')").addClass('hidden');
                        $(".o_cp_sidebar li:contains('Xóa')").addClass('hidden');
                    }, 400)
                }
            }

        }
    });




});