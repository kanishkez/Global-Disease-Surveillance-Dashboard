'use client';

interface StatsCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: string;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  variant?: 'default' | 'danger' | 'success' | 'warning';
}

const variantStyles = {
  default: {
    gradient: 'from-primary-500/20 to-primary-600/10',
    iconBg: 'bg-primary-500/20',
    border: 'border-primary-500/20',
  },
  danger: {
    gradient: 'from-red-500/20 to-red-600/10',
    iconBg: 'bg-red-500/20',
    border: 'border-red-500/20',
  },
  success: {
    gradient: 'from-emerald-500/20 to-emerald-600/10',
    iconBg: 'bg-emerald-500/20',
    border: 'border-emerald-500/20',
  },
  warning: {
    gradient: 'from-amber-500/20 to-amber-600/10',
    iconBg: 'bg-amber-500/20',
    border: 'border-amber-500/20',
  },
};

export default function StatsCard({ title, value, subtitle, icon, trend, trendValue, variant = 'default' }: StatsCardProps) {
  const style = variantStyles[variant];

  return (
    <div className={`stat-card group bg-gradient-to-br ${style.gradient}`}>
      <div className="flex items-start justify-between mb-3">
        <div className={`w-10 h-10 rounded-lg ${style.iconBg} flex items-center justify-center text-lg
                        group-hover:scale-110 transition-transform duration-300`}>
          {icon}
        </div>
        {trend && trendValue && (
          <div className={`flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-full
                          ${trend === 'up' ? 'text-red-400 bg-red-500/10' :
                            trend === 'down' ? 'text-emerald-400 bg-emerald-500/10' :
                            'text-dark-400 bg-white/5'}`}>
            {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'}
            {trendValue}
          </div>
        )}
      </div>
      <p className="text-dark-400 text-xs font-medium uppercase tracking-wider mb-1">{title}</p>
      <p className="text-2xl font-bold text-white tracking-tight">
        {typeof value === 'number' ? value.toLocaleString() : value}
      </p>
      {subtitle && (
        <p className="text-dark-400 text-xs mt-1">{subtitle}</p>
      )}
    </div>
  );
}
