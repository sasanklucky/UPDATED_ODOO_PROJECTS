odoo.define('kanban_draggable.schedule_chatter_extension', function (require) {
    "use strict";

    const Chatter = require('mail.Chatter');
    const rpc = require('web.rpc');
    const core = require('web.core');
    const _t = core._t;

    function isCrmInactive(context) {
        if (context && context.default_res_id) {
            return rpc.query({
                model: 'crm.lead',
                method: 'read',
                args: [[context.default_res_id], ['active']],
            }).then(result => {
                if (result && result.length) {
                    return result[0].active === false;
                }
                return false;
            });
        }
        return Promise.resolve(false);
    }

    Chatter.include({
        _onScheduleActivity: function () {
            const self = this;
            var activeField = this.context;
            if (this.record && this.record.model === 'crm.lead') {
                isCrmInactive(activeField).then(function (inactive) {
                    if (inactive) {
                        self.do_warn(_t("Blocked"), _t("You cannot schedule activities on an inactive CRM Lead."));
                        return; // block
                    }
                    // Not inactive → allow scheduling
                    if (self.fields.activity) {
                        self.fields.activity.scheduleActivity(false);
                    }
                });
            } else {
                // Other models → allow default behavior
                if (this.fields.activity) {
                    this.fields.activity.scheduleActivity(false);
                }
            }
        },
    });
});
