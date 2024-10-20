/** @odoo-module **/

import {registry} from '@web/core/registry';
import {url} from '@web/core/utils/urls';
import {BinaryField} from '@web/views/fields/binary/binary_field';
import {isBinarySize} from '@web/core/utils/binary';

function base64ToBlob(base64String, contentType) {
    const byteCharacters = atob(base64String);
    const byteArrays = [];
    for (let offset = 0; offset < byteCharacters.length; offset += 1024) {
        const slice = byteCharacters.slice(offset, offset + 1024);
        const byteNumbers = Array.from(slice, char => char.charCodeAt(0));
        byteArrays.push(new Uint8Array(byteNumbers));
    }
    return new Blob(byteArrays, { type: contentType });
}

function isValidBase64(value) {
    try {
        return btoa(atob(value)) === value;
    } catch (error) {
        return false;
    }
}

export class VideoField extends BinaryField {
    static template = 'video_widget.VideoField';
    static defaultProps = { acceptedFileExtensions: 'video/mp4' };

    get value() {
        return this.props.record.data[this.props.name];
    }

    get url() {
        try {
            if (isBinarySize(this.value)) {
                return url('/web/content', {
                    model: this.props.record.resModel,
                    id: this.props.record.resId,
                    field: this.props.name,
                });
            } else if (isValidBase64(this.value)) {
                return URL.createObjectURL(base64ToBlob(this.value, 'video/mp4'));
            } else {
                console.error('The base64 value is invalid or corrupted');
                return '';
            }
        } catch (error) {
            console.error('Error converting base64 to Blob:', error);
            return '';
        }
    }
}

registry.category('fields').add('video_widget', {
    component: VideoField,
    extractProps: ({ attrs }) => ({
        fileNameField: attrs.filename,
    }),
});
