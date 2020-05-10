odoo.define('tts_attandance_checkin_out.my_attendances', function (require) {
"use strict";

var core = require('web.core');
var Model = require('web.Model');
var Widget = require('web.Widget');

var QWeb = core.qweb;
var _t = core._t;


var MyAttendances = Widget.extend({
    events: {
        "click .o_hr_attendance_sign_in_out_icon": function() {
            this.$('.o_hr_attendance_sign_in_out_icon').attr("disabled", "disabled");
            this.update_attendance();
        },
    },

    start: function () {
        var self = this;

        var hr_employee = new Model('hr.employee');
        hr_employee.query(['attendance_state', 'name'])
            .filter([['user_id', '=', self.session.uid]])
            .all()
            .then(function (res) {
                if (_.isEmpty(res) ) {
                    self.$('.o_hr_attendance_employee').append(_t("Error : Could not find employee linked to user"));
                    return;
                }
                self.employee = res[0];
                self.$el.html(QWeb.render("HrAttendanceMyMainMenu", {widget: self}));
            });

        return this._super.apply(this, arguments);
    },

    update_attendance: function () {
        var url = 'http://192.168.1.12:8069';
        console.log('run modifier')
        var Session = require('web.Session');
        var self = this;
        this.connection = new Session(undefined,url, { use_cors: true});
        this.connection.rpc('/hw_proxy/tts_attendance',{},{timeout: 5000})
                    .then(function(results){
                        console.log(results)
                        var hr_employee = new Model('hr.employee');
                        hr_employee.call('attendance_manual', [[self.employee.id], 'hr_attendance.hr_attendance_action_my_attendances', false, results])
                            .then(function(result) {
                                if (result.action) {
                                    self.do_action(result.action);
                                } else if (result.warning) {
                                    self.do_warn(result.warning);
                                }
                            });
                    },function(error, event){
                        console.log('There was an error while trying to print the order:');
                        console.log(error);
                    });
    },
});

core.action_registry.add('hr_attendance_my_attendances', MyAttendances);

return MyAttendances;

});
