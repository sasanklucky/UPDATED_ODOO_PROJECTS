odoo.define('sr_otp_login.otp_timer', function (require) {
    "use strict";

    var ajax = require('web.ajax');  // Odoo Ajax helper

    // Ensure DOM is fully loaded
    $(document).ready(function () {
        let timer = 60;
        const resendButton = $('#resend_otp_button');  // Get Resend OTP button
        const timerElement = $('#timer');  // Get Timer element

        // Hide resend OTP button initially, show timer
        resendButton.hide();
        $('#resend_timer').show();

        // Countdown logic
        const countdown = setInterval(function () {
            timer--;
            timerElement.text(timer);  // Update timer UI

            // If timer reaches 0, stop countdown and show the resend button
            if (timer <= 0) {
                clearInterval(countdown);
                $('#resend_timer').hide();  // Hide the timer
                resendButton.show();  // Show the resend OTP button
            }
        }, 1000);

        // Handle resend OTP button click
        resendButton.click(function () {
            // Get the email value (can be dynamically set)
            const email = $('#user_email').val();  // Assuming you have an email input field with id "user_email"

            // Perform AJAX request to resend OTP
            ajax.jsonRpc('/web/resend_otp', 'call', { email: email })
                .then(function (data) {
                    if (data.success) {
                        // Success: alert user and restart timer
                        alert(data.message || "OTP resent successfully.");
                        timer = 60;  // Reset timer
                        timerElement.text(timer);  // Update timer UI
                        $('#resend_timer').show();
                        resendButton.hide();  // Hide the button while countdown is active

                        // Restart countdown
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
                        // Error: alert failure message
                        alert(data.message || "Failed to resend OTP. Please try again.");
                    }
                })
                .catch(function (error) {
                    // Handle any network or unexpected errors
                    console.error("Error:", error);
                    alert("An unexpected error occurred. Please try again later.");
                });
        });
    });
});
