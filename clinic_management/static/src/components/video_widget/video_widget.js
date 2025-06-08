/** @odoo-module **/

import {BinaryField} from "@web/views/fields/binary/binary_field";
import {_lt} from "@web/core/l10n/translation";
import {isBinarySize} from "@web/core/utils/binary";
import {registry} from "@web/core/registry";
// eslint-disable-next-line sort-imports
import {url as makeURL} from "@web/core/utils/urls";

function base64ToBlob(base64String, contentType) {
    try {
        const byteCharacters = atob(base64String);
        const byteArrays = [];
        for (let offset = 0; offset < byteCharacters.length; offset += 1024) {
            const slice = byteCharacters.slice(offset, offset + 1024);
            const byteNumbers = Array.from(slice, (char) => char.charCodeAt(0));
            byteArrays.push(new Uint8Array(byteNumbers));
        }
        return new Blob(byteArrays, {type: contentType || "video/mp4"});
    } catch (error) {
        console.error("Error in base64ToBlob:", error);
        return null;
    }
}

function isValidBase64(value) {
    if (typeof value !== "string") return false;
    try {
        return btoa(atob(value)) === value;
    } catch (error) {
        return false;
    }
}

export class VideoField extends BinaryField {
    static template = "video_widget.VideoField";
    static defaultProps = {
        ...super.defaultProps,
        acceptedFileExtensions: "video/mp4,video/webm,video/ogg",
    };

    get value() {
        return this.props.record.data[this.props.name];
    }

    get url() {
        const fieldValue = this.value;

        if (!fieldValue) {
            return "";
        }

        try {
            if (isBinarySize(fieldValue)) {
                const params = {
                    model: this.props.record.resModel,
                    id: this.props.record.resId,
                    field: this.props.name,
                    filename: this.fileName,
                };
                return makeURL("/web/content", params) + `&_cb=${Date.now()}`;
            } else if (typeof fieldValue === "string" && isValidBase64(fieldValue)) {
                const blob = base64ToBlob(fieldValue, "video/mp4");
                if (blob) {
                    return URL.createObjectURL(blob);
                }
                console.error("Failed to convert base64 to Blob.");
                return "";
            }
            console.warn(
                "VideoField: Value is not a binary size or valid base64. Cannot determine URL.",
                fieldValue
            );
            return "";
        } catch (error) {
            console.error("Error generating video URL:", error);
            return "";
        }
    }

    get fileName() {
        if (
            this.props.fileNameField &&
            this.props.record.data[this.props.fileNameField]
        ) {
            return this.props.record.data[this.props.fileNameField];
        }
        if (typeof this.props.name === "string") {
            return `${this.props.name.replace(/_/g, "_")}_video.mp4`;
        }
        return "video_file.mp4";
    }
}

registry.category("fields").add("video_widget", {
    component: VideoField,
    extractProps: ({attrs, field}) => {
        return {
            fileNameField:
                attrs.filename_field ||
                (field.options && field.options.filename_field) ||
                attrs.filename,
        };
    },
    supportedOptions: [
        {
            label: _lt("Filename Field"),
            name: "filename_field",
            type: "string",
            help: _lt(
                "The name of the field on the same record that holds the filename for this video."
            ),
        },
    ],
    supportedTypes: ["binary"],
});
