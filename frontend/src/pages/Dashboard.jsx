import { useQuery } from 'react-query'
import api from '../services/api'
import './Dashboard.css'

function Dashboard() {
  const { data: stats, isLoading } = useQuery('dashboard-stats', async () => {
    const response = await api.get('/metrics/dashboard')
    return response.data
  })

  if (isLoading) {
    return <div className="loading">Loading...</div>
  }

  return (
    <div className="dashboard">
      <h1>Dashboard</h1>
      <div className="stats-grid">
        <div className="stat-card">
          <h3>Total Profiles</h3>
          <p className="stat-value">{stats?.total_profiles || 0}</p>
        </div>
        <div className="stat-card">
          <h3>Active Profiles</h3>
          <p className="stat-value">{stats?.active_profiles || 0}</p>
        </div>
        <div className="stat-card">
          <h3>Total P&L</h3>
          <p className={`stat-value ${stats?.total_pnl >= 0 ? 'positive' : 'negative'}`}>
            ${stats?.total_pnl?.toFixed(2) || '0.00'}
          </p>
        </div>
        <div className="stat-card">
          <h3>Total Trades</h3>
          <p className="stat-value">{stats?.total_trades || 0}</p>
        </div>
        <div className="stat-card">
          <h3>Win Rate</h3>
          <p className="stat-value">{stats?.win_rate?.toFixed(2) || '0.00'}%</p>
        </div>
      </div>
    </div>
  )
}

export default Dashboard

