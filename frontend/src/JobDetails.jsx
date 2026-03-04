import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

function JobDetails() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [job, setJob] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchJob = async () => {
            // Mock jobs don't exist in DB, handle gracefully if coming from Demo jobs
            if (id.toString().startsWith('mock')) {
                setError('This is a demo job and cannot be viewed. Wait for the database to sync.');
                setIsLoading(false);
                return;
            }

            try {
                const res = await fetch(`/api/jobs/${id}`);
                if (res.ok) {
                    const data = await res.json();
                    setJob(data);
                } else if (res.status === 404) {
                    setError('Job not found in database.');
                } else {
                    setError('Failed to fetch job details.');
                }
            } catch (err) {
                console.error(err);
                setError('Network error loading job.');
            } finally {
                setIsLoading(false);
            }
        };

        fetchJob();
    }, [id]);

    if (isLoading) {
        return (
            <div className="container" style={{ padding: '4rem', textAlign: 'center' }}>
                <h2>Loading Job Details...</h2>
            </div>
        );
    }

    if (error || !job) {
        return (
            <div className="container" style={{ padding: '4rem', textAlign: 'center' }}>
                <h2 style={{ color: '#ef4444' }}>{error || 'Job not found'}</h2>
                <button onClick={() => navigate('/')} className="apply-btn" style={{ marginTop: '2rem' }}>Return to Search</button>
            </div>
        );
    }

    return (
        <div className="container" style={{ maxWidth: '800px', margin: '0 auto', paddingTop: '2rem' }}>
            <button
                onClick={() => navigate(-1)}
                style={{ background: 'none', border: 'none', color: 'var(--primary-color)', cursor: 'pointer', marginBottom: '1rem', fontSize: '1rem', fontWeight: 'bold' }}>
                ← Back
            </button>

            <div className="job-card" style={{ padding: '2rem' }}>
                <h1 style={{ marginBottom: '0.5rem', fontSize: '2rem' }}>{job.title}</h1>
                <h2 style={{ color: 'var(--text-secondary)', fontWeight: '500', marginBottom: '1.5rem' }}>{job.company}</h2>

                <div className="tags" style={{ marginBottom: '1.5rem', gap: '10px' }}>
                    <span className={`tag ${job.job_type?.toLowerCase().includes('intern') ? 'internship' : 'fulltime'}`}>
                        {job.job_type || 'Full-time'}
                    </span>
                    {job.is_remote && <span className="tag">Remote</span>}
                    <span className="tag site-tag" style={{ background: '#f0f0f0', color: '#333', border: '1px solid #ddd' }}>
                        {job.site || 'Source'}
                    </span>
                </div>

                <div className="details" style={{ fontSize: '1.1rem', marginBottom: '2rem', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <div className="location">📍 <strong>Location:</strong> {job.location || 'Not Specified'}</div>
                    {job.salary && <div className="salary">💰 <strong>Salary:</strong> {job.salary}</div>}
                    <div className="date-posted">📅 <strong>Posted:</strong> {job.date_posted || 'Recently'}</div>
                </div>

                <a
                    href={job.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="apply-btn"
                    style={{ display: 'inline-block', width: '100%', textAlign: 'center', padding: '1rem', fontSize: '1.1rem' }}
                >
                    Apply on {job.site || 'Company Site'}
                </a>

                {job.description && (
                    <div style={{ marginTop: '3rem', borderTop: '1px solid #333', paddingTop: '2rem' }}>
                        <h3>Job Description</h3>
                        <div
                            style={{ marginTop: '1rem', lineHeight: '1.8', color: '#ccc', whiteSpace: 'pre-wrap' }}
                            dangerouslySetInnerHTML={{ __html: job.description }}
                        />
                    </div>
                )}
            </div>
        </div>
    );
}

export default JobDetails;
