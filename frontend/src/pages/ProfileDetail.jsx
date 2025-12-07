import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import Editor from '@monaco-editor/react'
import api from '../services/api'
import './ProfileDetail.css'

function ProfileDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState('overview')
  const [algorithmCode, setAlgorithmCode] = useState('')
  const [parameters, setParameters] = useState({})

  const { data: profile, isLoading } = useQuery(
    ['profile', id],
    async () => {
      const response = await api.get(`/profiles/${id}`)
      return response.data
    }
  )

  const { data: algorithms } = useQuery(
    ['algorithms', id],
    async () => {
      const response = await api.get(`/algorithms/profile/${id}`)
      return response.data
    },
    { enabled: !!id }
  )

  const { data: orders } = useQuery(
    ['orders', id],
    async () => {
      const response = await api.get(`/orders/profile/${id}`)
      return response.data
    },
    { enabled: !!id }
  )

  const { data: metrics } = useQuery(
    ['metrics', id],
    async () => {
      const response = await api.get(`/metrics/profile/${id}/latest`)
      return response.data
    },
    { enabled: !!id, refetchInterval: 5000 }
  )

  const updateProfileMutation = useMutation(
    (data) => api.put(`/profiles/${id}`, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['profile', id])
      },
    }
  )

  const createAlgorithmMutation = useMutation(
    (data) => api.post('/algorithms', data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['algorithms', id])
        queryClient.invalidateQueries(['profile', id])
      },
    }
  )

  if (isLoading) {
    return <div className="loading">Loading profile...</div>
  }

  if (!profile) {
    return <div>Profile not found</div>
  }

  const handleSaveAlgorithm = () => {
    createAlgorithmMutation.mutate({
      profile_id: parseInt(id),
      code: algorithmCode,
      note: 'Updated via UI',
    })
  }

  return (
    <div className="profile-detail">
      <div className="profile-detail-header">
        <button className="btn-back" onClick={() => navigate('/profiles')}>
          ← Back
        </button>
        <h1>{profile.name}</h1>
      </div>

      <div className="tabs">
        <button
          className={activeTab === 'overview' ? 'active' : ''}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={activeTab === 'algorithm' ? 'active' : ''}
          onClick={() => setActiveTab('algorithm')}
        >
          Algorithm
        </button>
        <button
          className={activeTab === 'parameters' ? 'active' : ''}
          onClick={() => setActiveTab('parameters')}
        >
          Parameters
        </button>
        <button
          className={activeTab === 'orders' ? 'active' : ''}
          onClick={() => setActiveTab('orders')}
        >
          Orders
        </button>
        <button
          className={activeTab === 'logs' ? 'active' : ''}
          onClick={() => setActiveTab('logs')}
        >
          Logs
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'overview' && (
          <div className="overview">
            <div className="metrics-grid">
              <div className="metric-card">
                <h3>Total P&L</h3>
                <p className={metrics?.total_pnl >= 0 ? 'positive' : 'negative'}>
                  ${metrics?.total_pnl?.toFixed(2) || '0.00'}
                </p>
              </div>
              <div className="metric-card">
                <h3>Win Rate</h3>
                <p>{metrics?.win_rate?.toFixed(2) || '0.00'}%</p>
              </div>
              <div className="metric-card">
                <h3>Total Trades</h3>
                <p>{metrics?.total_trades || 0}</p>
              </div>
              <div className="metric-card">
                <h3>Open Positions</h3>
                <p>{metrics?.open_positions || 0}</p>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'algorithm' && (
          <div className="algorithm-editor">
            <div className="editor-header">
              <h3>Algorithm Code</h3>
              <button className="btn-primary" onClick={handleSaveAlgorithm}>
                Save Algorithm
              </button>
            </div>
            <Editor
              height="500px"
              defaultLanguage="python"
              value={algorithmCode || algorithms?.[0]?.code || ''}
              onChange={(value) => setAlgorithmCode(value)}
              theme="vs-dark"
            />
          </div>
        )}

        {activeTab === 'parameters' && (
          <div className="parameters">
            <h3>Runtime Parameters</h3>
            <div className="parameters-form">
              {Object.entries(profile.parameters || {}).map(([key, value]) => (
                <div key={key} className="form-group">
                  <label>{key}</label>
                  <input
                    type="text"
                    value={value}
                    onChange={(e) => {
                      const newParams = { ...parameters, [key]: e.target.value }
                      setParameters(newParams)
                    }}
                  />
                </div>
              ))}
              <button
                className="btn-primary"
                onClick={() => {
                  updateProfileMutation.mutate({ parameters })
                }}
              >
                Save Parameters
              </button>
            </div>
          </div>
        )}

        {activeTab === 'orders' && (
          <div className="orders">
            <h3>Order History</h3>
            <table className="orders-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Side</th>
                  <th>Type</th>
                  <th>Size</th>
                  <th>Price</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {orders?.map((order) => (
                  <tr key={order.id}>
                    <td>{new Date(order.created_at).toLocaleString()}</td>
                    <td>{order.side}</td>
                    <td>{order.order_type}</td>
                    <td>{order.size}</td>
                    <td>{order.price || 'Market'}</td>
                    <td>{order.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'logs' && (
          <div className="logs">
            <h3>Logs</h3>
            <LogsViewer profileId={id} />
          </div>
        )}
      </div>
    </div>
  )
}

function LogsViewer({ profileId }) {
  const { data: logs } = useQuery(
    ['logs', profileId],
    async () => {
      const response = await api.get(`/logs/profile/${profileId}`)
      return response.data
    },
    { enabled: !!profileId, refetchInterval: 2000 }
  )

  return (
    <div className="logs-viewer">
      {logs?.map((log) => (
        <div key={log.id} className={`log-entry log-${log.level.toLowerCase()}`}>
          <span className="log-time">{new Date(log.timestamp).toLocaleTimeString()}</span>
          <span className="log-level">{log.level}</span>
          <span className="log-message">{log.message}</span>
        </div>
      ))}
    </div>
  )
}

export default ProfileDetail

