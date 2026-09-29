import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

export default function ActivityRecharts({ mode, data }) {
  const isMonthly = mode === 'monthly';
  const accessibleLabel = isMonthly
    ? 'Monthly checks stacked by risk: not scam, suspicious, and high risk'
    : 'Scam checks by day of the week';
  const summary = isMonthly
    ? data.map((month) => `${month.label}: ${month.not_scam} not scam, ${month.suspicious} suspicious, ${month.high_risk} high risk`)
    : data.map((day) => `${day.weekday}: ${day.scam_count} ${day.scam_count === 1 ? 'scam check' : 'scam checks'}`);

  return (
    <div className="journey__activity-recharts" role="img" aria-label={accessibleLabel}>
      <ResponsiveContainer width="100%" height={isMonthly ? 280 : 260}>
        <BarChart data={data} margin={{ top: 8, right: 12, bottom: 10, left: 0 }} barCategoryGap={isMonthly ? '32%' : undefined}>
          <CartesianGrid stroke="rgba(148, 163, 184, .14)" vertical={false} />
          <XAxis
            dataKey={isMonthly ? 'label' : 'weekday'}
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            axisLine={{ stroke: 'rgba(148, 163, 184, .24)' }}
            tickLine={false}
            label={{ value: isMonthly ? 'Month' : 'Day of week', position: 'insideBottom', offset: -4, fill: '#94a3b8', fontSize: 11 }}
          />
          <YAxis
            allowDecimals={false}
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            label={{ value: isMonthly ? 'Checks' : 'Scam checks', angle: -90, position: 'insideLeft', fill: '#94a3b8', fontSize: 11 }}
          />
          <Tooltip
            contentStyle={{ border: '1px solid rgba(103, 232, 249, .3)', borderRadius: 8, background: '#101b2b', color: '#e6edf5' }}
            formatter={(value, name) => [value, name === 'not_scam' ? 'Not scam' : name === 'suspicious' ? 'Suspicious' : isMonthly ? 'High risk' : 'Scam checks']}
          />
          {isMonthly ? (
            <>
              <Bar dataKey="not_scam" name="Not scam" stackId="risk" fill="#34d399" />
              <Bar dataKey="suspicious" name="Suspicious" stackId="risk" fill="#fbbf24" />
              <Bar dataKey="high_risk" name="High risk" stackId="risk" fill="#fb7185" radius={[4, 4, 0, 0]} />
            </>
          ) : <Bar dataKey="scam_count" name="Scam checks" fill="#fbbf24" radius={[4, 4, 0, 0]} />}
        </BarChart>
      </ResponsiveContainer>
      <span className="journey__sr-only">{summary.join('. ')}</span>
    </div>
  );
}

export function CommunityLineChart({ data, category }) {
  const summary = data.map((point) => `${point.label}: you ${point.user_share == null ? 'not enough data' : `${point.user_share.toFixed(1)} percent`}; community ${point.community_share == null ? 'not enough data' : `${point.community_share.toFixed(1)} percent`}`).join('. ');

  return (
    <div className="journey__community-trend-chart" role="img" aria-label={`Monthly share comparison for ${category}: you and community`}>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={data} margin={{ top: 8, right: 12, bottom: 10, left: 0 }}>
          <CartesianGrid stroke="rgba(148, 163, 184, .14)" vertical={false} />
          <XAxis dataKey="label" tick={{ fill: '#94a3b8', fontSize: 10 }} axisLine={{ stroke: 'rgba(148, 163, 184, .24)' }} tickLine={false} label={{ value: 'Month', position: 'insideBottom', offset: -4, fill: '#94a3b8', fontSize: 10 }} />
          <YAxis domain={[0, 100]} tickFormatter={(value) => `${value}%`} tick={{ fill: '#94a3b8', fontSize: 10 }} axisLine={false} tickLine={false} label={{ value: 'Share of scam checks', angle: -90, position: 'insideLeft', fill: '#94a3b8', fontSize: 10 }} />
          <Tooltip
            contentStyle={{ border: '1px solid rgba(103, 232, 249, .3)', borderRadius: 8, background: '#101b2b', color: '#e6edf5' }}
            formatter={(value, name) => [value == null ? 'Not enough data' : `${value.toFixed(1)}%`, name]}
          />
          <Line type="monotone" dataKey="user_share" name="You" stroke="#67e8f9" strokeWidth={2.5} dot={{ r: 3 }} activeDot={{ r: 5 }} connectNulls={false} />
          <Line type="monotone" dataKey="community_share" name="Community" stroke="#fbbf24" strokeWidth={2.5} strokeDasharray="5 4" dot={{ r: 3 }} activeDot={{ r: 5 }} connectNulls={false} />
        </LineChart>
      </ResponsiveContainer>
      <span className="journey__sr-only">{summary}</span>
    </div>
  );
}