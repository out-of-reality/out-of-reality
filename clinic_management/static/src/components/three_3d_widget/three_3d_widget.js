/** @odoo-module **/

/* eslint-disable */
import {Component, onMounted, useRef} from "@odoo/owl";
import {registry} from "@web/core/registry";

export class Three3DWidget extends Component {
    setup() {
        this.containerRef = useRef("container");
        onMounted(() => {
            this.render3D();
        });
    }

    render3D() {
        if (window.THREE) {
            this.initThree();
        } else {
            const script = document.createElement("script");
            script.src =
                "https://cdn.jsdelivr.net/npm/three@0.152.2/build/three.min.js";
            script.onload = () => this.initThree();
            document.head.appendChild(script);
        }
    }

    async initThree() {
        function styleButton(btn) {
            btn.style.background = "linear-gradient(135deg, #1976d2 60%, #42a5f5 100%)";
            btn.style.color = "#fff";
            btn.style.border = "none";
            btn.style.borderRadius = "50%";
            btn.style.width = "38px";
            btn.style.height = "38px";
            btn.style.fontSize = "1.5em";
            btn.style.cursor = "pointer";
            btn.style.boxShadow = "0 2px 8px rgba(25, 118, 210, 0.12)";
            btn.style.transition = "background 0.2s, box-shadow 0.2s";
            btn.onmouseenter = () =>
                (btn.style.background =
                    "linear-gradient(135deg, #1565c0 60%, #1976d2 100%)");
            btn.onmouseleave = () =>
                (btn.style.background =
                    "linear-gradient(135deg, #1976d2 60%, #42a5f5 100%)");
        }
        const container = this.containerRef.el;
        const controlsPanel = document.createElement("div");
        controlsPanel.style.display = "flex";
        controlsPanel.style.alignItems = "center";
        controlsPanel.style.gap = "8px";
        controlsPanel.style.margin = "8px 0";
        controlsPanel.style.background = "#f7fafd";
        controlsPanel.style.borderRadius = "16px";
        controlsPanel.style.boxShadow = "0 2px 12px rgba(25, 118, 210, 0.08)";
        controlsPanel.style.padding = "12px 18px";
        controlsPanel.style.margin = "18px 0 12px 0";
        controlsPanel.style.width = "max-content";
        const playBtn = document.createElement("button");
        playBtn.textContent = "⏵";
        playBtn.title = "Play/Pause";
        playBtn.style.background = "linear-gradient(135deg, #1976d2 60%, #42a5f5 100%)";
        playBtn.style.color = "#fff";
        playBtn.style.border = "none";
        playBtn.style.borderRadius = "50%";
        playBtn.style.width = "48px";
        playBtn.style.height = "48px";
        playBtn.style.fontSize = "2em";
        playBtn.style.cursor = "pointer";
        playBtn.style.boxShadow = "0 2px 8px rgba(25, 118, 210, 0.15)";
        playBtn.style.transition = "background 0.2s, box-shadow 0.2s";
        playBtn.onmouseenter = () => {
            playBtn.style.background =
                "linear-gradient(135deg, #1565c0 60%, #1976d2 100%)";
            playBtn.style.boxShadow = "0 4px 16px rgba(25, 118, 210, 0.22)";
        };
        playBtn.onmouseleave = () => {
            playBtn.style.background =
                "linear-gradient(135deg, #1976d2 60%, #42a5f5 100%)";
            playBtn.style.boxShadow = "0 2px 8px rgba(25, 118, 210, 0.15)";
        };
        const progress = document.createElement("input");
        progress.type = "range";
        progress.min = 0;
        progress.value = 0;
        progress.step = 0.01;
        progress.style.width = "340px";
        progress.style.height = "10px";
        progress.style.margin = "0 12px";
        progress.style.background = "transparent";
        progress.style.border = "none";
        progress.style.outline = "none";
        progress.style.cursor = "pointer";
        progress.style.flex = "1 1 auto";
        progress.style.webkitAppearance = "none";
        progress.style.appearance = "none";
        progress.style.borderRadius = "6px";
        progress.style.boxShadow = "0 1px 2px rgba(25, 118, 210, 0.08)";
        progress.addEventListener("input", function () {
            this.style.background = `linear-gradient(90deg, #1976d2 ${
                (this.value / this.max) * 100
            }%, #e3eafc ${(this.value / this.max) * 100}%)`;
        });
        progress.style.background = "linear-gradient(90deg, #1976d2 0%, #e3eafc 0%)";
        const style = document.createElement("style");
        style.textContent = `
        input[type=range]::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 22px;
            height: 22px;
            border-radius: 50%;
            background: linear-gradient(135deg, #1976d2 60%, #42a5f5 100%);
            box-shadow: 0 2px 8px rgba(25, 118, 210, 0.18);
            border: 2px solid #fff;
            cursor: pointer;
            transition: background 0.2s;
        }
        input[type=range]:hover::-webkit-slider-thumb {
            background: linear-gradient(135deg, #1565c0 60%, #1976d2 100%);
        }
        input[type=range]::-webkit-slider-runnable-track {
            height: 10px;
            border-radius: 6px;
            background: #e3eafc;
        }
        input[type=range]::-moz-range-thumb {
            width: 22px;
            height: 22px;
            border-radius: 50%;
            background: linear-gradient(135deg, #1976d2 60%, #42a5f5 100%);
            border: 2px solid #fff;
            cursor: pointer;
        }
        input[type=range]:hover::-moz-range-thumb {
            background: linear-gradient(135deg, #1565c0 60%, #1976d2 100%);
        }
        input[type=range]::-ms-thumb {
            width: 22px;
            height: 22px;
            border-radius: 50%;
            background: linear-gradient(135deg, #1976d2 60%, #42a5f5 100%);
            border: 2px solid #fff;
            cursor: pointer;
        }
        input[type=range]:hover::-ms-thumb {
            background: linear-gradient(135deg, #1565c0 60%, #1976d2 100%);
        }
        input[type=range]::-ms-fill-lower {
            background: #1976d2;
            border-radius: 6px;
        }
        input[type=range]::-ms-fill-upper {
            background: #e3eafc;
            border-radius: 6px;
        }
        input[type=range]:focus {
            outline: none;
        }
        `;
        document.head.appendChild(style);
        const timeLabel = document.createElement("span");
        timeLabel.textContent = "0.00s";
        timeLabel.style.fontFamily = "monospace";
        timeLabel.style.fontSize = "1.15em";
        timeLabel.style.minWidth = "64px";
        timeLabel.style.textAlign = "right";
        timeLabel.style.color = "#1976d2";
        timeLabel.style.fontWeight = "600";
        const slashLabel = document.createElement("span");
        slashLabel.textContent = "/";
        slashLabel.style.fontFamily = "monospace";
        slashLabel.style.fontSize = "1.15em";
        slashLabel.style.color = "#888";
        slashLabel.style.margin = "0 4px";
        slashLabel.style.fontWeight = "600";
        const totalLabel = document.createElement("span");
        totalLabel.textContent = "0.00s";
        totalLabel.style.fontFamily = "monospace";
        totalLabel.style.fontSize = "1.15em";
        totalLabel.style.color = "#888";
        totalLabel.style.fontWeight = "600";
        const timeGroup = document.createElement("span");
        timeGroup.style.display = "flex";
        timeGroup.style.alignItems = "center";
        timeGroup.style.gap = "0px";
        timeGroup.appendChild(timeLabel);
        timeGroup.appendChild(slashLabel);
        timeGroup.appendChild(totalLabel);
        controlsPanel.appendChild(playBtn);
        controlsPanel.appendChild(progress);
        controlsPanel.appendChild(timeGroup);
        const fullscreenBtn = document.createElement("button");
        fullscreenBtn.title = "Full screen";
        fullscreenBtn.innerHTML =
            '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#1976d2" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/></svg>';
        fullscreenBtn.style.background = "white";
        fullscreenBtn.style.border = "none";
        fullscreenBtn.style.borderRadius = "50%";
        fullscreenBtn.style.width = "44px";
        fullscreenBtn.style.height = "44px";
        fullscreenBtn.style.display = "flex";
        fullscreenBtn.style.alignItems = "center";
        fullscreenBtn.style.justifyContent = "center";
        fullscreenBtn.style.boxShadow = "0 2px 8px rgba(25, 118, 210, 0.10)";
        fullscreenBtn.style.marginLeft = "8px";
        fullscreenBtn.style.cursor = "pointer";
        fullscreenBtn.onmouseenter = () => (fullscreenBtn.style.background = "#e3eafc");
        fullscreenBtn.onmouseleave = () => (fullscreenBtn.style.background = "white");
        if (!this.props.isModal) {
            controlsPanel.appendChild(fullscreenBtn);
        }
        fullscreenBtn.onclick = () => {
            const modalOverlay = document.createElement("div");
            modalOverlay.style.position = "fixed";
            modalOverlay.style.top = "0";
            modalOverlay.style.left = "0";
            modalOverlay.style.width = "100vw";
            modalOverlay.style.height = "100vh";
            modalOverlay.style.background = "rgba(30,40,60,0.75)";
            modalOverlay.style.zIndex = "9999";
            modalOverlay.style.display = "flex";
            modalOverlay.style.alignItems = "center";
            modalOverlay.style.justifyContent = "center";
            modalOverlay.style.backdropFilter = "blur(2px)";
            modalOverlay.addEventListener("mousedown", function (e) {
                if (e.target === modalOverlay) {
                    document.body.removeChild(modalOverlay);
                    window.removeEventListener("keydown", escListener);
                }
            });
            const modalContent = document.createElement("div");
            modalContent.style.background = "white";
            modalContent.style.borderRadius = "24px";
            modalContent.style.boxShadow = "0 8px 32px 0 rgba(25, 118, 210, 0.18)";
            modalContent.style.padding = "12px 12px 8px 12px";
            modalContent.style.position = "relative";
            modalContent.style.maxWidth = "96vw";
            modalContent.style.maxHeight = "96vh";
            modalContent.style.display = "flex";
            modalContent.style.alignItems = "center";
            modalContent.style.justifyContent = "center";
            const closeBtn = document.createElement("button");
            closeBtn.innerHTML = "✕";
            closeBtn.title = "Close";
            closeBtn.style.position = "absolute";
            closeBtn.style.top = "18px";
            closeBtn.style.right = "18px";
            closeBtn.style.background = "transparent";
            closeBtn.style.border = "none";
            closeBtn.style.fontSize = "2.2em";
            closeBtn.style.color = "#1976d2";
            closeBtn.style.cursor = "pointer";
            closeBtn.style.zIndex = "10001";
            closeBtn.onmouseenter = () => (closeBtn.style.color = "#1565c0");
            closeBtn.onmouseleave = () => (closeBtn.style.color = "#1976d2");
            closeBtn.onclick = () => document.body.removeChild(modalOverlay);
            const modalWidget = document.createElement("div");
            modalWidget.style.width = "1600px";
            modalWidget.style.height = "1000px";
            modalWidget.style.maxWidth = "96vw";
            modalWidget.style.maxHeight = "96vh";
            modalWidget.style.background = "#f7fafd";
            modalWidget.style.borderRadius = "18px";
            modalWidget.style.overflow = "hidden";
            modalWidget.style.display = "flex";
            modalWidget.style.alignItems = "center";
            modalWidget.style.justifyContent = "center";
            setTimeout(() => {
                const modalWidgetInstance = new this.constructor();
                modalWidgetInstance.props = {...this.props, isModal: true};
                modalWidgetInstance.containerRef = {el: modalWidget};
                modalWidgetInstance.initThree();
            }, 0);
            modalContent.appendChild(closeBtn);
            modalContent.appendChild(modalWidget);
            modalOverlay.appendChild(modalContent);
            document.body.appendChild(modalOverlay);
            const escListener = (e) => {
                if (e.key === "Escape") {
                    document.body.removeChild(modalOverlay);
                    window.removeEventListener("keydown", escListener);
                }
            };
            window.addEventListener("keydown", escListener);
        };
        Array.from(container.querySelectorAll("canvas")).forEach((c) => c.remove());
        Array.from(container.querySelectorAll("div.threejs-overlay")).forEach((c) =>
            c.remove()
        );
        container.style.width = "100%";
        container.style.height = "100%";
        container.style.position = "relative";
        const rawValue = this.props.record?.data?.[this.props.name];
        let data = [];
        try {
            data = JSON.parse(rawValue || "[]");
        } catch (e) {
            container.innerHTML = "<div style='color:red'>Invalid landmark data</div>";
            return;
        }
        if (!Array.isArray(data) || !data.length) {
            container.innerHTML = "<div style='color:gray'>No landmark data</div>";
            return;
        }
        let rawFrames = [];
        if (Array.isArray(data[0]) && data[0].length === 33) {
            rawFrames = data;
        } else if (
            Array.isArray(data) &&
            data.length === 33 &&
            Array.isArray(data[0]) &&
            data[0].length >= 3
        ) {
            rawFrames = [data];
        } else {
            container.innerHTML = "<div style='color:red'>No valid 3D frames</div>";
            return;
        }
        let rawTimes = null;
        const fps = this.props.record?.data?.video_fps
            ? parseFloat(this.props.record.data.video_fps)
            : 30;
        let videoDuration = null;
        let videoEl = null;
        videoEl =
            container.closest(".o_form_view, .o_form_sheet")?.querySelector("video") ||
            document.querySelector("video");
        if (videoEl) {
            if (!isNaN(videoEl.duration) && videoEl.duration > 0) {
                videoDuration = videoEl.duration;
            } else {
                videoEl.addEventListener(
                    "loadedmetadata",
                    () => {
                        if (videoEl.duration && !isNaN(videoEl.duration)) {
                            this.initThree();
                        }
                    },
                    {once: true}
                );
            }
        } else if (this.props.record?.data?.video) {
            videoDuration = frames.length / fps;
        }
        if (!rawTimes || rawTimes.length !== rawFrames.length) {
            rawTimes = Array.from({length: rawFrames.length}, (_, i) => i / fps);
        }
        let frames = rawFrames;
        let times = null;
        if (videoDuration && rawFrames.length > 1) {
            const n = rawFrames.length;
            times = Array.from({length: n}, (_, i) => i * (videoDuration / (n - 1)));
            frames = rawFrames;
        } else {
            times = rawTimes;
            frames = rawFrames;
        }
        let scale = 1;
        const maxAbs = Math.max(...frames[0].flat().map(Math.abs));
        if (maxAbs < 0.1) scale = 100;
        if (maxAbs > 1000) scale = 0.01;
        const scene = new window.THREE.Scene();
        function getCentroid(frame) {
            let cx = 0,
                cy = 0,
                cz = 0;
            frame.forEach((point) => {
                cx += point[0] * scale;
                cy += -point[1] * scale;
                cz += point[2] * scale;
            });
            cx /= frame.length;
            cy /= frame.length;
            cz /= frame.length;
            return {cx, cy, cz};
        }
        const {cx, cy, cz} = getCentroid(frames[0]);
        const fov = 75;
        const aspect = 900 / 600;
        const camera = new window.THREE.PerspectiveCamera(fov, aspect, 0.1, 1000);
        camera.position.set(cx, cy + 1, cz - 2);
        camera.lookAt(cx, cy, cz);
        const renderer = new window.THREE.WebGLRenderer();
        renderer.setClearColor(0x222222);
        renderer.setSize(container.offsetWidth || 900, container.offsetHeight || 600);
        renderer.domElement.style.display = "block";
        renderer.domElement.style.width = "100%";
        renderer.domElement.style.height = "100%";
        renderer.domElement.style.position = "relative";
        container.appendChild(renderer.domElement);
        controlsPanel.style.position = "absolute";
        controlsPanel.style.left = "50%";
        controlsPanel.style.bottom = "24px";
        controlsPanel.style.transform = "translateX(-50%)";
        controlsPanel.style.zIndex = "20";
        controlsPanel.style.background = "rgba(255,255,255,0.92)";
        controlsPanel.style.boxShadow = "0 2px 12px rgba(25, 118, 210, 0.10)";
        controlsPanel.style.borderRadius = "18px";
        controlsPanel.style.padding = "10px 18px";
        controlsPanel.style.margin = "0";
        controlsPanel.style.width = "auto";
        controlsPanel.style.pointerEvents = "auto";
        container.appendChild(controlsPanel);
        const ambientLight = new window.THREE.AmbientLight(0xffffff, 1);
        scene.add(ambientLight);
        const sphereColor = 0x1976d2;
        const lineColor = 0x43a047;
        const spheres = [];
        for (let i = 0; i < 33; ++i) {
            const geometry = new window.THREE.SphereGeometry(0.022, 20, 20);
            const material = new window.THREE.MeshStandardMaterial({
                color: sphereColor,
            });
            const sphere = new window.THREE.Mesh(geometry, material);
            scene.add(sphere);
            spheres.push(sphere);
        }
        const POSE_CONNECTIONS = [
            [0, 1],
            [1, 2],
            [2, 3],
            [3, 7],
            [0, 4],
            [4, 5],
            [5, 6],
            [6, 8],
            [9, 10],
            [11, 12],
            [11, 13],
            [13, 15],
            [15, 17],
            [15, 19],
            [15, 21],
            [17, 19],
            [12, 14],
            [14, 16],
            [16, 18],
            [16, 20],
            [16, 22],
            [18, 20],
            [11, 23],
            [12, 24],
            [23, 24],
            [23, 25],
            [24, 26],
            [25, 27],
            [26, 28],
            [27, 29],
            [28, 30],
            [29, 31],
            [30, 32],
            [27, 31],
            [28, 32],
        ];
        const lines = [];
        for (const [s, e] of POSE_CONNECTIONS) {
            for (let k = 0; k < 3; ++k) {
                const geometry = new window.THREE.BufferGeometry().setFromPoints([
                    new window.THREE.Vector3(0, 0, 0),
                    new window.THREE.Vector3(0, 0, 0),
                ]);
                const material = new window.THREE.LineBasicMaterial({color: lineColor});
                const line = new window.THREE.Line(geometry, material);
                scene.add(line);
                lines.push({line, s, e, k});
            }
        }
        scene.background = new window.THREE.Color(0xffffff);
        const gridColor = 0xcccccc,
            gridSize = 2,
            gridDivisions = 10,
            opacity = 0.5;
        const grids = [
            {rot: [0, 0, 0], pos: [0, -1, 0]},
            {rot: [0, 0, Math.PI / 2], pos: [1, 0, 0]},
            {rot: [Math.PI / 2, 0, 0], pos: [0, 0, 1]},
        ];
        grids.forEach(({rot, pos}) => {
            const grid = new window.THREE.GridHelper(gridSize, gridDivisions);
            grid.material = new window.THREE.LineBasicMaterial({
                color: gridColor,
                transparent: true,
                opacity,
            });
            grid.rotation.set(...rot);
            grid.position.set(...pos);
            scene.add(grid);
        });
        const overlayPanel = document.createElement("div");
        overlayPanel.className = "threejs-overlay";
        overlayPanel.style.position = "absolute";
        overlayPanel.style.right = "40px";
        overlayPanel.style.bottom = "120px";
        overlayPanel.style.zIndex = "10";
        overlayPanel.style.display = "flex";
        overlayPanel.style.flexDirection = "column";
        overlayPanel.style.alignItems = "center";
        overlayPanel.style.gap = "18px";
        overlayPanel.style.background = "#fff";
        overlayPanel.style.borderRadius = "28px";
        overlayPanel.style.boxShadow =
            "0 8px 32px 0 rgba(25, 118, 210, 0.13), 0 1.5px 8px 0 rgba(25, 118, 210, 0.10)";
        overlayPanel.style.padding = "28px 22px 22px 22px";
        overlayPanel.style.backdropFilter = "blur(8px)";
        overlayPanel.style.border = "2.5px solid rgba(255,255,255,0.7)";
        overlayPanel.style.outline = "1.5px solid #b3c6e6";
        overlayPanel.style.userSelect = "none";
        overlayPanel.style.pointerEvents = "auto";
        overlayPanel.style.background =
            "linear-gradient(120deg, #fff 80%, #e3f0ff 100%)";
        const btnUp = document.createElement("button");
        btnUp.innerHTML = "⬆️";
        btnUp.title = "Turn up";
        styleButton(btnUp);
        const btnDown = document.createElement("button");
        btnDown.innerHTML = "⬇️";
        btnDown.title = "Turn down";
        styleButton(btnDown);
        const btnLeft = document.createElement("button");
        btnLeft.innerHTML = "⬅️";
        btnLeft.title = "Turn left";
        styleButton(btnLeft);
        const btnRight = document.createElement("button");
        btnRight.innerHTML = "➡️";
        btnRight.title = "Turn right";
        styleButton(btnRight);
        const arrowPanel = document.createElement("div");
        arrowPanel.style.display = "grid";
        arrowPanel.style.gridTemplateColumns = "40px 40px 40px";
        arrowPanel.style.gridTemplateRows = "40px 40px 40px";
        arrowPanel.style.gap = "0px";
        arrowPanel.style.justifyItems = "center";
        arrowPanel.style.alignItems = "center";
        [btnUp, btnDown, btnLeft, btnRight].forEach((btn) => {
            btn.style.background = "linear-gradient(135deg, #1976d2 60%, #42a5f5 100%)";
            btn.style.color = "#fff";
            btn.style.border = "none";
            btn.style.borderRadius = "50%";
            btn.style.width = "38px";
            btn.style.height = "38px";
            btn.style.fontSize = "1.5em";
            btn.style.cursor = "pointer";
            btn.style.boxShadow = "0 2px 8px rgba(25, 118, 210, 0.12)";
            btn.style.transition = "background 0.2s, box-shadow 0.2s";
            btn.onmouseenter = () =>
                (btn.style.background =
                    "linear-gradient(135deg, #1565c0 60%, #1976d2 100%)");
            btn.onmouseleave = () =>
                (btn.style.background =
                    "linear-gradient(135deg, #1976d2 60%, #42a5f5 100%)");
        });
        arrowPanel.appendChild(document.createElement("div"));
        arrowPanel.appendChild(btnUp);
        arrowPanel.appendChild(document.createElement("div"));
        arrowPanel.appendChild(btnLeft);
        arrowPanel.appendChild(document.createElement("div"));
        arrowPanel.appendChild(btnRight);
        arrowPanel.appendChild(document.createElement("div"));
        arrowPanel.appendChild(btnDown);
        arrowPanel.appendChild(document.createElement("div"));
        const ROT_STEP = Math.PI / 18;
        btnLeft.onclick = () => {
            camera.position.applyAxisAngle(
                new window.THREE.Vector3(0, 1, 0),
                -ROT_STEP
            );
            camera.lookAt(cx, cy, cz);
            renderer.render(scene, camera);
        };
        btnRight.onclick = () => {
            camera.position.applyAxisAngle(new window.THREE.Vector3(0, 1, 0), ROT_STEP);
            camera.lookAt(cx, cy, cz);
            renderer.render(scene, camera);
        };
        btnUp.onclick = () => {
            const right = new window.THREE.Vector3()
                .subVectors(camera.position, new window.THREE.Vector3(cx, cy, cz))
                .cross(new window.THREE.Vector3(0, 1, 0))
                .normalize();
            camera.position.applyAxisAngle(right, ROT_STEP);
            camera.lookAt(cx, cy, cz);
            renderer.render(scene, camera);
        };
        btnDown.onclick = () => {
            const right = new window.THREE.Vector3()
                .subVectors(camera.position, new window.THREE.Vector3(cx, cy, cz))
                .cross(new window.THREE.Vector3(0, 1, 0))
                .normalize();
            camera.position.applyAxisAngle(right, -ROT_STEP);
            camera.lookAt(cx, cy, cz);
            renderer.render(scene, camera);
        };
        const zoomPanel = document.createElement("div");
        zoomPanel.style.display = "flex";
        zoomPanel.style.alignItems = "center";
        zoomPanel.style.gap = "8px";
        const zoomInBtn = document.createElement("button");
        zoomInBtn.textContent = "+";
        zoomInBtn.title = "Zoom in";
        styleButton(zoomInBtn);
        const zoomOutBtn = document.createElement("button");
        zoomOutBtn.textContent = "−";
        zoomOutBtn.title = "Zoom out";
        styleButton(zoomOutBtn);
        zoomPanel.appendChild(zoomInBtn);
        zoomPanel.appendChild(zoomOutBtn);
        overlayPanel.appendChild(arrowPanel);
        overlayPanel.appendChild(zoomPanel);
        renderer.domElement.style.position = "relative";
        renderer.domElement.parentElement.style.position = "relative";
        renderer.domElement.parentElement.appendChild(overlayPanel);
        zoomInBtn.onclick = () => {
            camera.position.add(
                camera.getWorldDirection(new window.THREE.Vector3()).multiplyScalar(0.2)
            );
            renderer.render(scene, camera);
        };
        zoomOutBtn.onclick = () => {
            camera.position.sub(
                camera.getWorldDirection(new window.THREE.Vector3()).multiplyScalar(0.2)
            );
            renderer.render(scene, camera);
        };
        const totalFrames = frames.length;
        let playing = false;
        let lastTimestamp = null;
        let elapsed = 0;
        function updateUI() {
            const duration =
                videoDuration || times[times.length - 1] || (totalFrames - 1) / 30;
            progress.max = duration.toFixed(2);
            progress.value = Math.min(elapsed, duration).toFixed(2);
            timeLabel.textContent = `${Math.min(elapsed, duration).toFixed(2)}s`;
            totalLabel.textContent = `${duration.toFixed(2)}s`;
            playBtn.textContent = playing ? "⏸" : "⏵";
        }
        playBtn.onclick = () => {
            playing = !playing;
            if (playing) {
                lastTimestamp = null;
                window.requestAnimationFrame(animate);
            }
            updateUI();
        };
        let dragging = false;
        let dragHandler = null;
        let dragEndHandler = null;
        progress.addEventListener("mousedown", () => {
            dragging = true;
            playing = false;
            document.body.style.userSelect = "none";
            dragHandler = (ev) => {
                const rect = progress.getBoundingClientRect();
                let x = ev.clientX;
                if (x < rect.left) x = rect.left;
                if (x > rect.right) x = rect.right;
                const percent = (x - rect.left) / rect.width;
                elapsed = percent * parseFloat(progress.max);
                updateFrameInterp(elapsed);
                updateUI();
            };
            dragEndHandler = () => {
                dragging = false;
                document.body.style.userSelect = "";
                window.removeEventListener("mousemove", dragHandler);
                window.removeEventListener("mouseup", dragEndHandler);
            };
            window.addEventListener("mousemove", dragHandler);
            window.addEventListener("mouseup", dragEndHandler);
        });
        progress.addEventListener("touchstart", () => {
            dragging = true;
            playing = false;
            document.body.style.userSelect = "none";
            dragHandler = (ev) => {
                if (!ev.touches || !ev.touches.length) return;
                const rect = progress.getBoundingClientRect();
                let x = ev.touches[0].clientX;
                if (x < rect.left) x = rect.left;
                if (x > rect.right) x = rect.right;
                const percent = (x - rect.left) / rect.width;
                elapsed = percent * parseFloat(progress.max);
                updateFrameInterp(elapsed);
                updateUI();
            };
            dragEndHandler = () => {
                dragging = false;
                document.body.style.userSelect = "";
                window.removeEventListener("touchmove", dragHandler);
                window.removeEventListener("touchend", dragEndHandler);
            };
            window.addEventListener("touchmove", dragHandler);
            window.addEventListener("touchend", dragEndHandler);
        });
        progress.addEventListener("input", () => {
            if (!dragging) {
                playing = false;
                elapsed = parseFloat(progress.value);
                updateFrameInterp(elapsed);
                updateUI();
            }
        });
        function updateFrameInterp(time) {
            const duration = videoDuration || times[times.length - 1];
            if (time >= duration) {
                setFrame(frames[frames.length - 1]);
                return;
            }
            let idx = times.findIndex((t) => t > time);
            if (idx === -1) idx = times.length - 1;
            if (idx === 0 || times.length === 1) {
                setFrame(frames[0]);
            } else {
                const t0 = times[idx - 1],
                    t1 = times[idx];
                const f0 = frames[idx - 1],
                    f1 = frames[idx];
                const alpha = t1 === t0 ? 0 : (time - t0) / (t1 - t0);
                const interp = f0.map((p0, j) => {
                    const p1 = f1[j];
                    return [
                        p0[0] + (p1[0] - p0[0]) * alpha,
                        p0[1] + (p1[1] - p0[1]) * alpha,
                        p0[2] + (p1[2] - p0[2]) * alpha,
                    ];
                });
                setFrame(interp);
            }
        }
        function setFrame(frame) {
            for (let i = 0; i < 33; ++i) {
                const point = frame[i];
                spheres[i].position.set(
                    -point[0] * scale,
                    -point[1] * scale,
                    point[2] * scale
                );
            }
            for (let i = 0; i < lines.length; i += 3) {
                const {line, s, e} = lines[i];
                const {line: line2} = lines[i + 1];
                const {line: line3} = lines[i + 2];
                const offset = 0.012;
                const p1 = [
                    -frame[s][0] * scale,
                    -frame[s][1] * scale,
                    frame[s][2] * scale,
                ];
                const p2 = [
                    -frame[e][0] * scale,
                    -frame[e][1] * scale,
                    frame[e][2] * scale,
                ];
                line.geometry.setFromPoints([
                    new window.THREE.Vector3(...p1),
                    new window.THREE.Vector3(...p2),
                ]);
                line2.geometry.setFromPoints([
                    new window.THREE.Vector3(p1[0] + offset, p1[1] + offset, p1[2]),
                    new window.THREE.Vector3(p2[0] + offset, p2[1] + offset, p2[2]),
                ]);
                line3.geometry.setFromPoints([
                    new window.THREE.Vector3(p1[0] - offset, p1[1] - offset, p1[2]),
                    new window.THREE.Vector3(p2[0] - offset, p2[1] - offset, p2[2]),
                ]);
            }
            renderer.render(scene, camera);
        }
        function animate(timestamp) {
            if (!playing) return;
            if (lastTimestamp === null) lastTimestamp = timestamp;
            const delta = (timestamp - lastTimestamp) / 1000;
            lastTimestamp = timestamp;
            if (!dragging) {
                elapsed += delta;
            }
            const duration = videoDuration || times[times.length - 1];
            if (elapsed > duration) elapsed = duration;
            updateFrameInterp(elapsed);
            updateUI();
            if (elapsed >= duration) {
                playing = false;
                updateUI();
                return;
            }
            window.requestAnimationFrame(animate);
        }
        updateUI();
        window.requestAnimationFrame(animate);
        function addThickAxes(origin, length = 0.2, radius = 0.01) {
            const axis = [
                {dir: [1, 0, 0], color: 0xff0000},
                {dir: [0, 1, 0], color: 0x00ff00},
                {dir: [0, 0, 1], color: 0x0000ff},
            ];
            axis.forEach(({dir, color}) => {
                const geom = new window.THREE.CylinderGeometry(
                    radius,
                    radius,
                    length,
                    16
                );
                const mat = new window.THREE.MeshBasicMaterial({color});
                const mesh = new window.THREE.Mesh(geom, mat);
                if (dir[0]) mesh.rotation.z = Math.PI / 2;
                if (dir[2]) mesh.rotation.x = Math.PI / 2;
                mesh.position.set(
                    origin.x + length * 0.5 * -dir[0],
                    origin.y + length * 0.5 * dir[1],
                    origin.z + length * 0.5 * -dir[2]
                );
                scene.add(mesh);
            });
        }
        addThickAxes(new window.THREE.Vector3(cx, cy, cz), 0.2, 0.01);
        renderer.domElement.addEventListener(
            "wheel",
            (e) => {
                e.preventDefault();
            },
            {passive: false}
        );
        const blockEvt = (e) => {
            e.preventDefault();
            e.stopPropagation();
        };
        [
            "mousedown",
            "mousemove",
            "mouseup",
            "touchstart",
            "touchmove",
            "touchend",
        ].forEach((evt) => {
            renderer.domElement.addEventListener(evt, blockEvt, {passive: false});
        });
    }

    static template = "clinic_management.Three3DWidget";
    static props = {
        readonly: {type: Boolean, optional: true},
        id: {type: [String, Number], optional: true},
        name: {type: String, optional: true},
        record: {type: Object, optional: true},
        value: {type: [String, null], optional: true},
    };
}

registry.category("fields").add("three_3d_widget", {
    component: Three3DWidget,
    extractProps: () => ({}),
    supportedTypes: ["text", "char"],
});
registry.category("public_components").add("three_3d_widget_public", Three3DWidget);
