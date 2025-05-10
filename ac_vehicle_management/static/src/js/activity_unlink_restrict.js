odoo.define('ac_vehicle_management.activity_unlink_restrict', function (require) {
    "use strict";

    var Activity = require('mail.Activity');
    var core = require('web.core');
    var _t = core._t;

    Activity.include({

        /**
         * Override unlink to prevent activity deletion in crm.lead
         */
        _onUnlinkActivity: function (event, options) {
            event.preventDefault();
            var self = this;
            var activity_id = $(event.currentTarget).data('activity-id');
            options = _.defaults(options || {}, {
                model: 'mail.activity',
                args: [[activity_id]],
            });

            // Only restrict for crm.lead model
            if (this.model === 'crm.lead') {
                return this._rpc({
                    model: 'res.users',
                    method: 'has_group',
                    args: ['base.group_system'],  // Replace with your custom group if needed
                }).then(function (hasAccess) {
                    if (!hasAccess) {
                        self.do_warn(
                            _t("Operation Not Allowed"),
                            _t("Unauthorised access to delete activities from a lead.")
                        );
                        return;
                    }
                    return self._rpc({
                        model: options.model,
                        method: 'unlink',
                        args: options.args,
                    }).then(self._reload.bind(self, { activity: true }));
                });
            }

            // Default behavior for other models
            return this._rpc({
                model: options.model,
                method: 'unlink',
                args: options.args,
            }).then(this._reload.bind(this, { activity: true }));
        },
    });
});