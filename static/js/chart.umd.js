/*
 * Lightweight offline chart renderer with a Chart.js-style API.
 * This file is intentionally small and beginner-friendly so the project can
 * run without internet access while keeping the familiar `new Chart(...)` pattern.
 */
(function () {
    class Chart {
        constructor(contextOrCanvas, config) {
            this.canvas = contextOrCanvas.canvas ? contextOrCanvas.canvas : contextOrCanvas;
            this.context = this.canvas.getContext("2d");
            this.config = config || {};
            this.draw();
            window.addEventListener("resize", () => this.draw());
        }

        draw() {
            const ctx = this.context;
            const canvas = this.canvas;
            const parentWidth = canvas.parentElement ? canvas.parentElement.clientWidth : 640;
            canvas.width = Math.max(parentWidth - 10, 280);
            canvas.height = canvas.height || 220;

            const data = this.config.data || {};
            const labels = data.labels || [];
            const dataset = (data.datasets || [])[0] || { data: [] };
            const values = dataset.data || [];
            const lineColor = dataset.borderColor || "#1d6fd8";
            const fillColor = dataset.backgroundColor || "rgba(29, 111, 216, 0.12)";

            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = "#ffffff";
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            if (!values.length) {
                ctx.fillStyle = "#5e7389";
                ctx.font = "16px Segoe UI";
                ctx.fillText("No data available yet.", 22, 40);
                return;
            }

            const padding = { top: 24, right: 18, bottom: 44, left: 44 };
            const plotWidth = canvas.width - padding.left - padding.right;
            const plotHeight = canvas.height - padding.top - padding.bottom;
            let min = Math.min(...values);
            let max = Math.max(...values);
            if (min === max) {
                min -= 1;
                max += 1;
            }

            ctx.strokeStyle = "#d8e3f0";
            ctx.lineWidth = 1;
            for (let step = 0; step < 5; step += 1) {
                const y = padding.top + (plotHeight / 4) * step;
                const chartValue = max - ((max - min) / 4) * step;
                ctx.beginPath();
                ctx.moveTo(padding.left, y);
                ctx.lineTo(canvas.width - padding.right, y);
                ctx.stroke();
                ctx.fillStyle = "#5e7389";
                ctx.font = "11px Segoe UI";
                ctx.fillText(chartValue.toFixed(1), 4, y + 4);
            }

            ctx.strokeStyle = "#94a3b8";
            ctx.beginPath();
            ctx.moveTo(padding.left, padding.top);
            ctx.lineTo(padding.left, canvas.height - padding.bottom);
            ctx.lineTo(canvas.width - padding.right, canvas.height - padding.bottom);
            ctx.stroke();

            ctx.beginPath();
            ctx.lineWidth = 3;
            ctx.strokeStyle = lineColor;
            ctx.fillStyle = fillColor;

            const points = values.map((value, index) => {
                const x = values.length === 1
                    ? padding.left + plotWidth / 2
                    : padding.left + (plotWidth / (values.length - 1)) * index;
                const y = padding.top + ((max - value) / (max - min)) * plotHeight;
                return { x, y, value };
            });

            points.forEach((point, index) => {
                if (index === 0) {
                    ctx.moveTo(point.x, point.y);
                } else {
                    ctx.lineTo(point.x, point.y);
                }
            });
            ctx.stroke();

            points.forEach((point, index) => {
                ctx.beginPath();
                ctx.fillStyle = lineColor;
                ctx.arc(point.x, point.y, 4, 0, Math.PI * 2);
                ctx.fill();
                ctx.fillStyle = "#5e7389";
                ctx.font = "10px Segoe UI";
                const label = labels[index] ? labels[index].split(" ")[0] : `P${index + 1}`;
                ctx.fillText(label, point.x - 14, canvas.height - 18);
            });

            ctx.fillStyle = "#15304b";
            ctx.font = "bold 13px Segoe UI";
            ctx.fillText(dataset.label || "Health Data", padding.left, 16);
        }
    }

    window.Chart = Chart;
})();
