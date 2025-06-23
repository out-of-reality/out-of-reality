/** @odoo-module **/

import {_t} from "@web/core/l10n/translation";
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.FaceIDLogin = publicWidget.Widget.extend({
    selector: "#faceidBtn",
    events: {
        click: "_onOpenModal",
    },

    init() {
        this._super(...arguments);
        this.notification = this.bindService("notification");
    },

    _onOpenModal() {
        const modal = document.getElementById("faceidModal");
        const video = document.getElementById("faceVideo");
        const closeModalBtns = [
            document.getElementById("closeFaceModal"),
            document.getElementById("closeFaceModal2"),
        ];
        const captureBtn = document.getElementById("captureFace");
        const spinner = document.getElementById("loadingSpinner");

        let stream = null;
        modal.style.display = "block";

        navigator.mediaDevices
            .getUserMedia({video: true})
            .then((mediaStream) => {
                stream = mediaStream;
                video.srcObject = stream;
                video.play();
            })
            .catch(() => this._notifyError(_t("Unable to access the camera.")));

        const closeModal = () => {
            modal.style.display = "none";
            if (stream) {
                stream.getTracks().forEach((track) => track.stop());
                stream = null;
            }
        };

        closeModalBtns.forEach((btn) => btn?.addEventListener("click", closeModal));

        captureBtn.addEventListener(
            "click",
            async () => {
                const canvas = document.createElement("canvas");
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                const ctx = canvas.getContext("2d");
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                const image = canvas.toDataURL("image/png");
                closeModal();

                spinner.classList.remove("d-none");
                spinner.classList.add("d-flex");

                const response = await fetch("/web/login/verify_face", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        jsonrpc: "2.0",
                        method: "call",
                        params: {image},
                    }),
                });

                spinner.classList.remove("d-flex");
                spinner.classList.add("d-none");

                const json = await response.json();
                const result = json.result;

                if (result.success) {
                    window.location.href = "/web";
                } else {
                    this._notifyError(
                        result.message || _t("Face verification failed.")
                    );
                }
            },
            {once: true}
        );
    },

    _notifyError(message) {
        this.notification.add(message, {type: "danger"});
    },
});
