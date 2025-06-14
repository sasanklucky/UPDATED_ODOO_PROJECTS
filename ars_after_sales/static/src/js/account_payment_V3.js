odoo.define('ars_after_sales.account_payment_V3', function (require) {
    "use strict";

    var session = require('web.session');
    var ShowPaymentLineWidget = require('account.payment').ShowPaymentLineWidget;

    var ShowPaymentLineWidgetPatch = ShowPaymentLineWidget.include({
        /**
         * Only override this method — session.uid is available here.
         */
        _onRemoveMoveReconcile: function (event) {
            var self = this;
                var paymentId = parseInt($(event.target).attr('payment-id'));
            if (paymentId !== undefined && !isNaN(paymentId)) {
                this._rpc({
                    model: 'account.move.line',
                    method: 'remove_move_reconcile',
                    args: [paymentId, {
                        invoice_id: this.res_id,
                        uid: session.uid,
                    }],
                }).then(function () {
                    self.trigger_up('reload');
                });
            }
        },
    });
});
