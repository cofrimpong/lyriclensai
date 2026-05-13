document.addEventListener("DOMContentLoaded", () => {
    const canvases = document.querySelectorAll(".chart-canvas");
    if (!canvases.length || typeof Chart === "undefined") {
        return;
    }

    const palette = ["#8B5CF6", "#EC4899", "#22D3EE", "#1DB954", "#F59E0B", "#F8FAFC"];

    canvases.forEach((canvas) => {
        const chartKind = canvas.dataset.chartKind;
        const chartAxis = canvas.dataset.chartAxis || "x";
        const labels = JSON.parse(canvas.dataset.chartLabels || "[]");
        const values = JSON.parse(canvas.dataset.chartValues || "[]");
        const chartLabel = canvas.dataset.chartLabel || "Dataset";

        new Chart(canvas, {
            type: chartKind,
            data: {
                labels,
                datasets: [
                    {
                        label: chartLabel,
                        data: values,
                        backgroundColor: values.map((_, index) => palette[index % palette.length] + "CC"),
                        borderColor: values.map((_, index) => palette[index % palette.length]),
                        borderWidth: 2,
                        tension: 0.35,
                        fill: chartKind === "line",
                    },
                ],
            },
            options: {
                maintainAspectRatio: false,
                indexAxis: chartKind === "bar" ? chartAxis : "x",
                plugins: {
                    legend: {
                        display: chartKind === "doughnut",
                        labels: {
                            color: "#CBD5E1",
                        },
                    },
                },
                scales: chartKind === "doughnut" ? {} : {
                    x: {
                        ticks: { color: "#CBD5E1" },
                        grid: { color: "rgba(255,255,255,0.06)" },
                    },
                    y: {
                        ticks: { color: "#CBD5E1", precision: 0 },
                        grid: { color: "rgba(255,255,255,0.06)" },
                        beginAtZero: true,
                    },
                },
            },
        });
    });
});
