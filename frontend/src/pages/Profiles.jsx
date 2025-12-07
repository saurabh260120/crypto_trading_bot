import { useQuery, useMutation, useQueryClient } from 'react-query'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import './Profiles.css'

function Profiles() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: profiles, isLoading } = useQuery('profiles', async () => {
    const response = await api.get('/profiles')
    return response.data
  })

  const startMutation = useMutation(
    (id) => api.post(`/profiles/${id}/start`),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('profiles')
      },
    }
  )

  const stopMutation = useMutation(
    (id) => api.post(`/profiles/${id}/stop`),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('profiles')
      },
    }
  )

  if (isLoading) {
    return <div className="loading">Loading profiles...</div>
  }

  return (
    <div className="profiles">
      <div className="profiles-header">
        <h1>Profiles</h1>
        <button
          className="btn-primary"
          onClick={() => navigate('/profiles/new')}
        >
          Create Profile
        </button>
      </div>

      {profiles?.length === 0 ? (
        <div className="empty-state">
          <p>No profiles yet. Create your first profile to start trading.</p>
        </div>
      ) : (
        <div className="profiles-grid">
          {profiles?.map((profile) => (
            <div key={profile.id} className="profile-card">
              <div className="profile-header">
                <h3>{profile.name}</h3>
                <span className={`status-badge ${profile.enabled ? 'active' : 'inactive'}`}>
                  {profile.enabled ? 'Active' : 'Inactive'}
                </span>
              </div>
              <div className="profile-info">
                <p><strong>Environment:</strong> {profile.environment}</p>
                <p><strong>API Keys:</strong> {profile.has_api_keys ? '✓ Configured' : '✗ Not configured'}</p>
                <p><strong>Algorithm:</strong> {profile.algorithm_version_id ? '✓ Configured' : '✗ Not configured'}</p>
              </div>
              <div className="profile-actions">
                <button
                  className="btn-secondary"
                  onClick={() => navigate(`/profiles/${profile.id}`)}
                >
                  View Details
                </button>
                {profile.enabled ? (
                  <button
                    className="btn-danger"
                    onClick={() => stopMutation.mutate(profile.id)}
                    disabled={stopMutation.isLoading}
                  >
                    Stop
                  </button>
                ) : (
                  <button
                    className="btn-success"
                    onClick={() => startMutation.mutate(profile.id)}
                    disabled={startMutation.isLoading}
                  >
                    Start
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default Profiles

