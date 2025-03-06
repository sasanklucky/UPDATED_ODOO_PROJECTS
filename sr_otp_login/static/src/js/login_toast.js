odoo.define("sr_otp_login.login_toast", function (require) {
    "use strict";

    var ajax = require("web.ajax");

    $(document).ready(function () {
        console.log("Toastify Loaded:", window.Toastify);

        setTimeout(() => {
            ajax.jsonRpc("/get_toast_messages", "call", {}).then(function (message) {
                console.log("Received Messages:", message);

                let notifications = [];
                let logoutMessage = localStorage.getItem("logout_message");
                console.log("logoutMessage", logoutMessage);

                function showNotification(text, background, persistent = false, onCloseCallback = null) {
                    let toast = Toastify({
                        text: text,
                        duration: persistent ? -1 : 6000, // Keep it open if persistent
                        close: true,
                        gravity: "top",
                        position: "center",
                        className: "custom-toast",
                        style: { background: background,
                                width: "400px", // Fixed width
                                height: "auto", // Auto height for wrapping
                                textAlign: "center", // Center align text
                                whiteSpace: "normal", // Allow text wrapping
                                wordWrap: "break-word", // Ensure words break properly
                                overflow: "hidden", // Hide overflow
                         },
                        callback: function () {
                            if (onCloseCallback) {
                                onCloseCallback();
                            }
                        }
                    });

                    toast.showToast();
                }

                if (message.error) {
                    notifications.push(
                        showNotification(
                            message.error, "linear-gradient(to right, #ff5f6d, #ffc371)",
                            false,
                            function(){
                                ajax.jsonRpc("/clear_toast_messages", "call", {'msg_typ': 'error'}).then(() => {
                                console.log("Toast messages cleared.");
                                });
                            }
                        )
                    );
                }
                if (message.success) {
                    notifications.push(
                        showNotification(
                            message.success, "linear-gradient(to right, #00b09b, #96c93d)",
                            false,
                            function(){
                                ajax.jsonRpc("/clear_toast_messages", "call", {'msg_typ': 'success'}).then(() => {
                                console.log("Toast messages cleared.");
                                });
                            }

                        )

                    );
                }
                if (logoutMessage) {
                    notifications.push(
                        showNotification(
                            logoutMessage,
                            "linear-gradient(to right, #ff5f6d, #ffc371)",
                            true,
                            function () {
                                // Remove logout message from localStorage when closed
                                console.log("Clearing logout_message from localStorage...");
                                localStorage.removeItem("logout_message");
                            }
                        )
                    );
                }

                Promise.all(notifications).then(() => {
                    console.log("All toast notifications completed. Clearing session.");
                    ajax.jsonRpc("/clear_toast_messages", "call", {}).then(() => {
                        console.log("Toast messages cleared.");
                    });
                });

            }).fail((error) => console.error("Error fetching toast messages:", error));
        }, 1000);
    });
});
