odoo.define("auto_logout_idle_user_odoo.auto_log_out_notify", function (require) {
    "use strict";

    $(document).ready(function () {
        console.log("Toastify Loaded:", window.Toastify);

        setTimeout(() => {
            let logoutMessage = localStorage.getItem("logout_message");
            console.log("Logout Message:", logoutMessage);

            function showNotification(text, background, persistent = false, onCloseCallback = null) {
                let toast = Toastify({
                    text: text,
                    duration: persistent ? -1 : 6000, // Keep open if persistent
                    close: true,
                    gravity: "top",
                    position: "center",
                    className: "custom-toast-auto-logout",
                    style: {
                        background: background,
                        width: "400px",
                        textAlign: "center",
                        whiteSpace: "normal",
                        wordWrap: "break-word",
                        borderRadius: "10px",
                        padding: "12px"
                    },
                    callback: function () {
                        if (onCloseCallback) {
                            onCloseCallback();
                        }
                    }
                });

                toast.showToast();
            }

            if (logoutMessage) {
                showNotification(
                    logoutMessage,
                    "linear-gradient(to right, #ff5f6d, #ffc371)",
                    true,
                    function () {
                        console.log("Clearing logout_message from localStorage...");
                        localStorage.removeItem("logout_message");
                    }
                );
            }

        }, 1000); // Delay to ensure DOM is ready
    });
});
