"use client";

import { LucideIcon, TrendingUp, TrendingDown, Minus } from "lucide-react";

interface StatsCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: "up" | "down" | "neutral";
  trendValue?: string;
  variant?: "default" | "danger" | "success" | "warning";
}

const variantStyles = {
  default: {
    iconBg: "bg-blue-500/10",
    iconColor: "text-blue-500",
  },
  danger: {
    iconBg: "bg-red-500/10",
    iconColor: "text-red-500",
  },
  success: {
    iconBg: "bg-emerald-500/10",
    iconColor: "text-emerald-500",
  },
  warning: {
    iconBg: "bg-amber-500/10",
    iconColor: "text-amber-500",
  },
};

export default function StatsCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  trendValue,
  variant = "default",
}: StatsCardProps) {
  const style = variantStyles[variant];

  return (
    <div className="stat-card transition-colors">
      <div className="flex items-start justify-between mb-3">
        <div
          className={`w-10 h-10 rounded-lg ${style.iconBg} flex items-center justify-center transition-transform duration-200`}
        >
          <Icon className={`w-5 h-5 ${style.iconColor}`} />
        </div>
        {trend && trendValue && (
          <div
            className={`flex items-center gap-1 text-xs font-medium px-2 py-1 rounded ${
              trend === "up"
                ? "text-red-400 bg-red-500/10"
                : trend === "down"
                  ? "text-emerald-400 bg-emerald-500/10"
                  : "text-[color:var(--text-muted)] bg-black/5 dark:bg-white/5"
            }`}
          >
            {trend === "up" ? (
              <TrendingUp className="w-3 h-3" />
            ) : trend === "down" ? (
              <TrendingDown className="w-3 h-3" />
            ) : (
              <Minus className="w-3 h-3" />
            )}
            {trendValue}
          </div>
        )}
      </div>
      <p className="text-xs font-medium uppercase tracking-wider mb-1 text-[color:var(--text-muted)]">
        {title}
      </p>
      <p className="text-2xl font-bold tracking-tight text-[color:var(--text-primary)]">
        {typeof value === "number" ? value.toLocaleString() : value}
      </p>
      {subtitle && (
        <p className="text-xs mt-1 text-[color:var(--text-muted)]">{subtitle}</p>
      )}
    </div>
  );
}
