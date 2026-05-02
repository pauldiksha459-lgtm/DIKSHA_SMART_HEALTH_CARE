document.addEventListener("DOMContentLoaded", () => {
    const payload = window.dashboardData || { labels: [], temperatures: [], heart_rates: [] };

    const temperatureCanvas = document.getElementById("temperatureChart");
    if (temperatureCanvas) {
        new Chart(temperatureCanvas, {
            type: "line",
            data: {
                labels: payload.labels,
                datasets: [
                    {
                        label: "Temperature (°F)",
                        data: payload.temperatures,
                        borderColor: "#cb2f40",
                        backgroundColor: "rgba(203, 47, 64, 0.12)",
                    },
                ],
            },
        });
    }

    const heartRateCanvas = document.getElementById("heartRateChart");
    if (heartRateCanvas) {
        new Chart(heartRateCanvas, {
            type: "line",
            data: {
                labels: payload.labels,
                datasets: [
                    {
                        label: "Heart Rate (bpm)",
                        data: payload.heart_rates,
                        borderColor: "#1d6fd8",
                        backgroundColor: "rgba(29, 111, 216, 0.12)",
                    },
                ],
            },
        });
    }
});
