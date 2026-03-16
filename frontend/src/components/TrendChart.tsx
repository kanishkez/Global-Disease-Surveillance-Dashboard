"use client";

import { useEffect, useRef } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  ArcElement,
} from "chart.js";
import { Line, Bar, Doughnut } from "react-chartjs-2";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  ArcElement,
);

// Default chart options for dark theme
const defaultOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      labels: {
        color: "#94a3b8",
        font: { family: "Inter", size: 11 },
        usePointStyle: true,
        pointStyle: "circle",
      },
    },
    tooltip: {
      backgroundColor: "#1a1f35",
      titleColor: "#f1f5f9",
      bodyColor: "#94a3b8",
      borderColor: "rgba(99, 102, 241, 0.3)",
      borderWidth: 1,
      cornerRadius: 8,
      padding: 12,
      titleFont: { family: "Inter", size: 13, weight: "600" as const },
      bodyFont: { family: "Inter", size: 12 },
    },
  },
  scales: {
    x: {
      ticks: { color: "#64748b", font: { family: "Inter", size: 10 } },
      grid: { color: "rgba(148, 163, 184, 0.06)" },
      border: { color: "rgba(148, 163, 184, 0.1)" },
    },
    y: {
      ticks: { color: "#64748b", font: { family: "Inter", size: 10 } },
      grid: { color: "rgba(148, 163, 184, 0.06)" },
      border: { color: "rgba(148, 163, 184, 0.1)" },
    },
  },
};

interface TrendChartProps {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    color?: string;
    fill?: boolean;
  }[];
  title?: string;
  type?: "line" | "bar" | "doughnut";
  height?: number;
}

const colorPalette = [
  { border: "#2563eb", bg: "rgba(37, 99, 235, 0.15)" },
  { border: "#10b981", bg: "rgba(16, 185, 129, 0.15)" },
  { border: "#f59e0b", bg: "rgba(245, 158, 11, 0.15)" },
  { border: "#ef4444", bg: "rgba(239, 68, 68, 0.15)" },
  { border: "#3b82f6", bg: "rgba(59, 130, 246, 0.15)" },
  { border: "#06b6d4", bg: "rgba(6, 182, 212, 0.15)" },
];

const doughnutColors = [
  "#2563eb",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#3b82f6",
  "#06b6d4",
  "#0ea5e9",
  "#14b8a6",
];

export default function TrendChart({
  labels,
  datasets,
  title,
  type = "line",
  height = 300,
}: TrendChartProps) {
  const chartData = {
    labels,
    datasets: datasets.map((ds, i) => {
      const palette = colorPalette[i % colorPalette.length];
      if (type === "doughnut") {
        return {
          label: ds.label,
          data: ds.data,
          backgroundColor: doughnutColors.slice(0, ds.data.length),
          borderColor: doughnutColors.slice(0, ds.data.length).map((c) => c),
          borderWidth: 2,
        };
      }
      return {
        label: ds.label,
        data: ds.data,
        borderColor: ds.color || palette.border,
        backgroundColor:
          ds.fill !== false
            ? ds.color
              ? `${ds.color}20`
              : palette.bg
            : "transparent",
        fill: ds.fill !== false,
        tension: 0.4,
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 5,
        pointHoverBackgroundColor: ds.color || palette.border,
      };
    }),
  };

  const options = {
    ...defaultOptions,
    plugins: {
      ...defaultOptions.plugins,
      title: title
        ? {
            display: true,
            text: title,
            color: "#f1f5f9",
            font: { family: "Inter", size: 14, weight: "600" as const },
            padding: { bottom: 16 },
          }
        : { display: false },
    },
  };

  if (type === "doughnut") {
    return (
      <div style={{ height }}>
        <Doughnut
          data={chartData}
          options={
            {
              ...options,
              cutout: "65%",
              scales: undefined,
            } as any
          }
        />
      </div>
    );
  }

  return (
    <div style={{ height }}>
      {type === "bar" ? (
        <Bar data={chartData} options={options as any} />
      ) : (
        <Line data={chartData} options={options as any} />
      )}
    </div>
  );
}
