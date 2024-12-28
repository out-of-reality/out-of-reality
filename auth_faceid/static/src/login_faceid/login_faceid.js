/** @odoo-module **/

import {Component, useRef} from "@odoo/owl";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";

export class FaceIDLogin extends Component {
    static template = "auth_faceid.FaceIDLogin";
    videoRef = useRef("videoElement");
    stream = null;

    setup() {
        this.rpc = useService("rpc");
        this.notification = useService("notification");
    }

    async openModal() {
        const modal = document.getElementById("faceidModal");
        modal.style.display = "block";

        try {
            this.stream = await navigator.mediaDevices.getUserMedia({video: true});
            this.videoRef.el.srcObject = this.stream;
            this.videoRef.el.play();
        } catch (error) {
            this.notification.add(_t("Failed to access the camera."), {type: "danger"});
        }
    }

    closeModal() {
        const modal = document.getElementById("faceidModal");
        modal.style.display = "none";

        if (this.stream) {
            const tracks = this.stream.getTracks();
            tracks.forEach((track) => track.stop());
            this.stream = null;
        }
    }

    async captureImage() {
        const canvas = document.createElement("canvas");
        canvas.width = this.videoRef.el.videoWidth;
        canvas.height = this.videoRef.el.videoHeight;
        const context = canvas.getContext("2d");
        context.drawImage(this.videoRef.el, 0, 0, canvas.width, canvas.height);

        const image = canvas.toDataURL("image/png");
        this.closeModal();

        const spinner = document.getElementById("loadingSpinner");
        spinner.classList.remove("d-none");
        spinner.classList.add("d-flex");

        await this.verifyFace(image);

        spinner.classList.remove("d-flex");
        spinner.classList.add("d-none");
    }

    async verifyFace(image) {
        try {
            const result = await this.rpc("/web/login/verify_face", {image: image});
            if (result.success) {
                this.notification.add(result.message, {type: "success"});
                window.location.href = "/web";
            } else {
                this.notification.add(result.message, {type: "danger"});
            }
        } catch (error) {
            this.notification.add(_t("An error occurred while verifying the face."), {
                type: "danger",
            });
        }
    }
}

registry.category("public_components").add("auth_faceid.FaceIDLogin", FaceIDLogin);
