odoo.define('sr_otp_login.otp_timer', function (require) {
    "use strict";

    var ajax = require('web.ajax');

    $(document).ready(function () {
        let timer = 60;
        const resendButton = $('#resend_otp_button');
        const timerElement = $('#timer');

        resendButton.hide();
        $('#resend_timer').show();

        const countdown = setInterval(function () {
            timer--;
            timerElement.text(timer);

            if (timer <= 0) {
                clearInterval(countdown);
                $('#resend_timer').hide();
                resendButton.show();
            }
        }, 1000);

        resendButton.click(function () {
            const email = $('#user_email').val();

            // Disable button and add loading animation
            resendButton.prop("disabled", true);
            resendButton.html('<i class="fa fa-spinner fa-spin"></i> Resending...');

            // Show persistent loading notification
            let loadingToast = Toastify({
                text: "Resending OTP...",
                duration: -1, // Persistent until manually closed
                close: false,
                gravity: "top",
                position: "center",
                className: "custom-toast",
                style: {
                    background: "linear-gradient(to right, #007bff, #0056b3)",
                    width: "300px",
                    textAlign: "center"
                }
            });

            loadingToast.showToast();

            ajax.jsonRpc('/web/resend_otp', 'call', { email: email })
                .then(function (data) {
                    // Remove loading toast
                    loadingToast.hideToast();

                    if (data.success) {
                        Toastify({
                            text: "OTP resent successfully!",
                            duration: 6000,
                            close: true,
                            gravity: "top",
                            position: "center",
                            className: "custom-toast",
                            style: {
                                background: "linear-gradient(to right, #00b09b, #96c93d)",
                                width: "300px",
                                textAlign: "center"
                            }
                        }).showToast();

                        timer = 60;
                        timerElement.text(timer);
                        $('#resend_timer').show();
                        resendButton.hide();

                        const restartCountdown = setInterval(function () {
                            timer--;
                            timerElement.text(timer);

                            if (timer <= 0) {
                                clearInterval(restartCountdown);
                                $('#resend_timer').hide();
                                resendButton.show();
                            }
                        }, 1000);
                    } else {
                        Toastify({
                            text: "Failed to resend OTP. Please try again.",
                            duration: 6000,
                            close: true,
                            gravity: "top",
                            position: "center",
                            className: "custom-toast",
                            style: {
                                background: "linear-gradient(to right, #ff5f6d, #ffc371)",
                                width: "300px",
                                textAlign: "center"
                            }
                        }).showToast();
                    }
                })
                .fail(function (error) {
                    console.error("Error:", error);

                    // Remove loading toast
                    loadingToast.hideToast();

                    Toastify({
                        text: "An unexpected error occurred. Please try again later.",
                        duration: 6000,
                        close: true,
                        gravity: "top",
                        position: "center",
                        className: "custom-toast",
                        style: {
                            background: "linear-gradient(to right, #ff5f6d, #ffc371)",
                            width: "300px",
                            textAlign: "center"
                        }
                    }).showToast();
                })
                .always(function () {
                    // Reset button after AJAX call completes
                    resendButton.prop("disabled", false);
                    resendButton.html("Resend OTP");
                });
        });
    });
});
