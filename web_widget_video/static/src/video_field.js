/** @odoo-module **/

import {_t} from '@web/core/l10n/translation';
import {registry} from '@web/core/registry';
import {url} from '@web/core/utils/urls';
import {BinaryField} from '@web/views/fields/binary/binary_field';
import {isBinarySize} from '@web/core/utils/binary';

function base64ToBlob(base64String, contentType) {
    const byteCharacters = atob(base64String);
    const byteArrays = [];
    for (let offset = 0; offset < byteCharacters.length; offset += 1024) {
        const slice = byteCharacters.slice(offset, offset + 1024);
        const byteNumbers = new Array(slice.length);
        for (let i = 0; i < slice.length; i++) {
            byteNumbers[i] = slice.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        byteArrays.push(byteArray);
    }
    return new Blob(byteArrays, { type: contentType });
}

export class VideoField extends BinaryField {
    static template = 'web_widget_video.VideoField';
    static defaultProps = {
        acceptedFileExtensions: 'video/mp4',
    };

    get value() {
        return this.props.record.data[this.props.name];
    }

    get url() {
        if (isBinarySize(this.value)) {
            return url('/web/content', {
                model: this.props.record.resModel,
                id: this.props.record.resId,
                field: this.props.name,
            });
        }
        const base64String = this.value;
        const contentType = 'video/mp4';
        const videoBlob = base64ToBlob(base64String, contentType);
        return URL.createObjectURL(videoBlob);
    }
}

export const videoField = {
    component: VideoField,
    displayName: _t('Video'),
    supportedTypes: ['binary'],
}

registry.category('fields').add('video', videoField);
