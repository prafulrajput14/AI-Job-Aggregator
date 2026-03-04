import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { AuthContext } from './AuthContext';

function Dashboard() {
    const [savedJobs, setSavedJobs] = useState([]);
    const [alerts, setAlerts] = useState([]);
    const [newKeyword, setNewKeyword] = useState('');
    const [newLocation, setNewLocation] = useState('');
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState('');

    const { user, token, loading } = useContext(AuthContext);
    const navigate = useNavigate();

    useEffect(() => {
        // Redirect if not logged in after auth has finished checking
        if (!loading && !user) {
            navigate('/login');
            return;
        }

        if (token) {
            const fetchSavedJobs = async () => {
                try {
                    const response = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/user/saved_jobs`, {
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                    if (response.ok) {
                        const jobs = await response.json();
                        setSavedJobs(jobs);
                    }
                } catch (err) {
                    console.error(err);
                }
            };

            const fetchAlerts = async () => {
                try {
                    const response = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/alerts`, {
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                    if (response.ok) {
                        const data = await response.json();
                        setAlerts(data);
                    }
                } catch (err) {
                    console.error(err);
                }
            };

            setIsLoading(true);
            Promise.all([fetchSavedJobs(), fetchAlerts()]).then(() => setIsLoading(false));
        }
    }, [user, token, loading, navigate]);

    const handleUnsaveJob = async (e, jobId) => {
        e.stopPropagation();
        try {
            const response = await fetch(`/api/unsave_job/${jobId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                setSavedJobs(prev => prev.filter(job => job.id !== jobId));
                toast.success('Job removed');
            } else {
                toast.error("Failed to remove job");
            }
        } catch (err) {
            console.error(err);
            toast.error("Network error removing job");
        }
    };

    const handleAddAlert = async (e) => {
        e.preventDefault();
        if (!newKeyword.trim()) return;

        try {
            const response = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/alerts`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ keyword: newKeyword, location: newLocation })
            });

            if (response.ok) {
                setNewKeyword('');
                setNewLocation('');
                // Refresh alerts
                const fetchRes = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/alerts`, { headers: { 'Authorization': `Bearer ${token}` } });
                const data = await fetchRes.json();
                setAlerts(data);
                toast.success("Alert created!");
            } else {
                toast.error("Failed to create alert.");
            }
        } catch (err) {
            console.error(err);
            toast.error("Error creating alert");
        }
    };

    const handleDeleteAlert = async (alertId) => {
        try {
            const response = await fetch(`/api/alerts/${alertId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                setAlerts(prev => prev.filter(a => a.id !== alertId));
            }
        } catch (err) { console.error(err); }
    };

    if (loading || isLoading) {
        return (
            <div className="container">
                <div className="fetch-section" style={{ textAlign: 'center', padding: '4rem' }}>
                    <h2>Loading your dashboard...</h2>
                </div>
            </div>
        );
    }

    return (
        <div className="container">
            <div className="fetch-section" style={{ marginBottom: '2rem' }}>
                <h2>Dashboard</h2>
                <p style={{ color: 'var(--text-secondary)' }}>Welcome back, {user?.full_name || user?.email}!</p>
            </div>

            <div className="fetch-section" style={{ marginBottom: '2rem' }}>
                <h2>Job Alerts</h2>
                <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>Get daily email digests when new jobs match your criteria.</p>

                <form onSubmit={handleAddAlert} style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginBottom: '1.5rem' }}>
                    <input type="text" className="fetch-input" placeholder="Keyword (e.g. React)" value={newKeyword} onChange={e => setNewKeyword(e.target.value)} required style={{ flex: 1, minWidth: '150px' }} />
                    <input type="text" className="fetch-input" placeholder="Location (Optional)" value={newLocation} onChange={e => setNewLocation(e.target.value)} style={{ flex: 1, minWidth: '150px' }} />
                    <button type="submit" className="fetch-btn">Create Alert</button>
                </form>

                <div className="alerts-list">
                    {alerts.length === 0 ? (
                        <p style={{ color: '#888', fontStyle: 'italic' }}>No active alerts.</p>
                    ) : (
                        <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '10px' }}>
                            {alerts.map(alert => (
                                <li key={alert.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#222', padding: '10px 15px', borderRadius: '8px', border: '1px solid #333' }}>
                                    <div>
                                        <strong style={{ color: '#fff' }}>{alert.keyword}</strong>
                                        {alert.location && <span style={{ color: '#aaa', marginLeft: '8px' }}> in {alert.location}</span>}
                                    </div>
                                    <button onClick={() => handleDeleteAlert(alert.id)} style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '1.2rem' }} title="Remove Alert">✖</button>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            </div>

            <div className="results-section">
                <h2>Your Saved Jobs ({savedJobs.length})</h2>

                {error && <div style={{ color: '#ef4444', marginBottom: '1rem', fontWeight: '500' }}>{error}</div>}

                <div className="job-list">
                    {savedJobs.length === 0 ? (
                        <div className="no-jobs" style={{ padding: '3rem', textAlign: 'center' }}>
                            You haven't saved any jobs yet. Go to the search page to find some!
                        </div>
                    ) : (
                        savedJobs.map((job) => (
                            <div key={job.id} className="job-card">
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                    <h3 style={{ margin: 0, paddingRight: '2rem' }}>{job.title}</h3>
                                    <button
                                        onClick={(e) => handleUnsaveJob(e, job.id)}
                                        style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.2rem', color: '#ef4444', opacity: 0.8 }}
                                        title="Remove Saved Job"
                                    >✖</button>
                                </div>

                                <div className="company" style={{ marginTop: '0.5rem' }}>{job.company}</div>

                                <div className="tags">
                                    <span className={`tag ${job.job_type?.toLowerCase().includes('intern') ? 'internship' : 'fulltime'}`}>
                                        {job.job_type || 'Full-time'}
                                    </span>
                                    {job.is_remote && <span className="tag">Remote</span>}
                                    <span className="tag site-tag" style={{ background: '#f0f0f0', color: '#333', border: '1px solid #ddd' }}>
                                        {job.site || 'Source'}
                                    </span>
                                </div>

                                <div className="details">
                                    <div className="location">📍 {job.location}</div>
                                    {job.salary_max && <div className="salary">💰 {job.salary_min ? `${job.salary_min} - ` : ''}{job.salary_max}</div>}
                                    <div className="date-posted">📅 {job.date_posted || 'Recently'}</div>
                                </div>

                                <a
                                    href={job.job_url || job.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="apply-btn"
                                >
                                    Apply Now
                                </a>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
}

export default Dashboard;
