////odoo.define('model_access_rights.kanban_controller', function (require) {
////    "use strict";
////
////    var KanbanRecord = require('web.KanbanRecord');
////    var rpc = require('web.rpc');
////
////    KanbanRecord.include({
////        willStart: function () {
////            var self = this;
////            self.removedActions = [];
////
////            return this._super.apply(this, arguments).then(function () {
////                return rpc.query({
////                    model: 'access.right',
////                    method: 'hide_buttons',
////                    args: [],
////                    kwargs: {
////                        model: self.modelName,
////                        user_id: self.getSession().uid,
////                    },
////                }).then(function (records) {
////                    console.log("Fetched records:", records);
////
////                    if (records.is_delete) self.removedActions.push("Delete");
////                    if (records.is_archive) self.removedActions.push("Archive");
////                    if (records.is_edit) self.removedActions.push("Edit");
////
////                    console.log("Removed Actions:", self.removedActions);
////                }).fail(function (error) {
////                    console.error("RPC Error:", error);
////                });
////            });
////        },
////
////        _render: function () {
////            this._super.apply(this, arguments);
////
////            var self = this;
////            setTimeout(function () {
////                var dropdown = self.$('.o_dropdown_kanban .dropdown-menu');
////                if (!dropdown.length) return;
////
////                dropdown.find('a').each(function () {
////                    var actionLabel = $(this).text().trim();
////                    if (self.removedActions.includes(actionLabel)) {
////                        $(this).remove();
////                    }
////                });
////
////            }, 100);
////        }
////
////    });
////
////});
////
//odoo.define('model_access_rights.kanban_controller', function (require) {
//    "use strict";
//
//    var KanbanRecord = require('web.KanbanRecord');
//    var rpc = require('web.rpc');
//
//    KanbanRecord.include({
//        willStart: function () {
//            var self = this;
//            self.removedActions = [];
//
//            return this._super.apply(this, arguments).then(function () {
//                return rpc.query({
//                    model: 'access.right',
//                    method: 'hide_buttons',
//                    args: [],
//                    kwargs: {
//                        model: self.modelName,
//                        user_id: self.getSession().uid,
//                    },
//                }).then(function (records) {
//                    console.log("Fetched records:", records);
//
//                    if (records.is_delete) self.removedActions.push("Delete");
//                    if (records.is_archive) self.removedActions.push("Archive");
//                    if (records.is_edit) self.removedActions.push("Edit");
//
//                    console.log("Removed Actions:", self.removedActions);
//                }).fail(function (error) {
//                    console.error("RPC Error:", error);
//                });
//            });
//        },
//
//        start: function () {
//            var self = this;
//            return this._super.apply(this, arguments).then(function () {
//                self._removeActionsFromDropdown();
//            });
//        },
//
//        _removeActionsFromDropdown: function () {
//            var self = this;
//            setTimeout(function () {
//                var dropdown = self.$('.o_dropdown_kanban .dropdown-menu');
//                if (!dropdown.length) return;
//
//                dropdown.find('a').each(function () {
//                    var actionLabel = $(this).text().trim();
//                    if (self.removedActions.includes(actionLabel)) {
//                        $(this).remove();
//                    }
//                });
//
//            }, 100);
//        }
//    });
//});
odoo.define('model_access_rights.kanban_controller', function (require) {
    "use strict";

    var KanbanRecord = require('web.KanbanRecord');
    var rpc = require('web.rpc');

    KanbanRecord.include({
        willStart: function () {
            var self = this;
            self.removedActions = [];

            // **Skip execution if the model is 'ir.module.module' (Apps menu)**
            if (self.modelName === 'ir.module.module') {
                console.log("Skipping Apps Kanban View (willStart)");
                return this._super.apply(this, arguments);
            }

            return this._super.apply(this, arguments).then(function () {
                return rpc.query({
                    model: 'access.right',
                    method: 'hide_buttons',
                    args: [],
                    kwargs: {
                        model: self.modelName,
                        user_id: self.getSession().uid,
                    },
                }).then(function (records) {
                    console.log("Fetched records:", records);

                    if (records.is_delete) self.removedActions.push("Delete");
                    if (records.is_archive) self.removedActions.push("Archive");
                    if (records.is_edit) self.removedActions.push("Edit");

                    console.log("Removed Actions:", self.removedActions);
                }).fail(function (error) {
                    console.error("RPC Error:", error);
                });
            });
        },

        _render: function () {
            var self = this;
            this._super.apply(this, arguments);

            // **Skip execution if the model is 'ir.module.module' (Apps menu)**
            if (self.modelName === 'ir.module.module') {
                console.log("Skipping Apps Kanban View (_render)");
                return;
            }

            setTimeout(function () {
                var dropdown = self.$('.o_dropdown_kanban .dropdown-menu');
                if (!dropdown.length) return;

                dropdown.find('a').each(function () {
                    var actionLabel = $(this).text().trim();
                    if (self.removedActions.includes(actionLabel)) {
                        $(this).remove(); // Hide instead of remove
                    }
                });

            }, 500);
        }
    });

});



