import React, { useState, useEffect, useMemo, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { AuthContext } from './AuthContext';
import { INDIAN_CITIES } from './data/indian_cities';

function JobSearch({ theme }) {
    const [jobs, setJobs] = useState([]);
    const [isFetching, setIsFetching] = useState(false);
    const [statusMessage, setStatusMessage] = useState('');
    const [systemStatus, setSystemStatus] = useState(null);

    // Search State
    const [fetchKeyword, setFetchKeyword] = useState('');
    const [fetchLocation, setFetchLocation] = useState('');

    // Autocomplete State
    const [filteredCities, setFilteredCities] = useState([]);
    const [showCitySuggestions, setShowCitySuggestions] = useState(false);

    // Filter & Display State
    const [searchTerm, setSearchTerm] = useState('');
    const [filterType, setFilterType] = useState('All');
    const [selectedJob, setSelectedJob] = useState(null);
    const [hasSearched, setHasSearched] = useState(false);

    // Pagination State
    const [currentPage, setCurrentPage] = useState(1);
    const jobsPerPage = 12;

    const { token } = useContext(AuthContext);
    const navigate = useNavigate();

    useEffect(() => {
        // Fetch system status on load to show cache freshness
        fetch(`${import.meta.env.VITE_API_URL || ''}/api/system/status`)
            .then(res => res.json())
            .then(data => setSystemStatus(data))
            .catch(err => console.error("Could not fetch system status", err));
    }, []);

    const handleLocationChange = (e) => {
        const input = e.target.value;
        setFetchLocation(input);
        if (input.length > 0) {
            const filtered = INDIAN_CITIES.filter(city => city.toLowerCase().startsWith(input.toLowerCase()));
            setFilteredCities(filtered);
            setShowCitySuggestions(true);
        } else {
            setShowCitySuggestions(false);
        }
    };

    const selectCity = (city) => {
        setFetchLocation(city);
        setShowCitySuggestions(false);
    };

    const generateMockJobs = (termInput, locInput) => {
        const term = termInput || fetchKeyword || 'Software Engineer';
        const loc = locInput || fetchLocation || 'Remote';
        const titles = [`Senior ${term} Developer`, `${term} Engineer`, `Junior ${term}`, `Lead ${term}`, `${term} Intern`, `Principal ${term} Architect`];
        const companies = ["Tech Giants Inc.", "Startup Hub", "Creative Solutions", "Global Systems", "Future Tech"];
        const sites = ["LinkedIn", "Glassdoor", "Indeed", "Naukri"];

        return Array.from({ length: 8 }).map((_, i) => {
            const title = titles[i % titles.length];
            const jobLoc = loc;
            const siteName = sites[i % sites.length];
            return {
                id: `mock-${i}`, // Needs a unique ID for saving logic demoing
                title: title,
                company: companies[i % companies.length],
                location: jobLoc,
                url: "#",
                site: siteName,
                date_posted: datePosted === 'past_24h' || datePosted === 'past_week' ? "1 day ago" : "Just now",
                job_type: "Full-time",
                salary: sortBy === 'salary' ? "₹20,00,000 - ₹35,00,000" : "₹12,00,000 - ₹25,00,000",
                description: `Exciting opportunity...`
            };
        });
    };

    const handleFetchJobs = () => {
        if (!fetchKeyword || !fetchLocation) {
            setStatusMessage("Please enter both keyword and location");
            return;
        }
        setHasSearched(true);
        setIsFetching(true);
        setSearchTerm('');
        setCurrentPage(1);
        setStatusMessage('Checking database for existing jobs...');

        const pollParams = new URLSearchParams();
        if (fetchKeyword) pollParams.append('q', fetchKeyword);
        if (fetchLocation) pollParams.append('location', fetchLocation);
        if (filterType !== 'All') pollParams.append('filter_type', filterType);
        pollParams.append('sort_by', 'newest');
        pollParams.append('date_posted_filter', 'any');

        let attempts = 0;
        const maxAttempts = 3;

        const pollBackend = () => {
            fetch(`https://ai-job-aggregator-1.onrender.com/api/jobs?${pollParams.toString()}`)
                .then(res => res.json())
                .then(currentJobs => {
                    attempts++;

                    if (currentJobs.length > 0) {
                        setJobs(currentJobs);
                        setStatusMessage(`Found ${currentJobs.length} active jobs!`);
                        setIsFetching(false);
                    } else if (attempts < maxAttempts) {
                        // Backend kicked off a background scrape. Wait 1s and check if it found anything yet.
                        setStatusMessage(`Searching for best matches... (${attempts}/${maxAttempts})`);
                        setTimeout(pollBackend, 1000);
                    } else {
                        // Max attempts reached, genuinely no jobs found within the 3 second threshold
                        setStatusMessage("No jobs found in that location right now.");
                        setJobs([]);
                        setIsFetching(false);
                    }
                })
                .catch(error => {
                    setJobs([]);
                    setIsFetching(false);
                    setStatusMessage('Search complete (Database Offline).');
                });
        };

        pollBackend();
    };

    const handleRefresh = () => {
        if (!fetchKeyword || !fetchLocation) return;
        setIsFetching(true);
        setCurrentPage(1);
        setStatusMessage('Refreshing list from database...');

        const refreshParams = new URLSearchParams();
        refreshParams.append('q', fetchKeyword);
        refreshParams.append('location', fetchLocation);
        if (filterType !== 'All') refreshParams.append('filter_type', filterType);
        refreshParams.append('sort_by', 'newest');
        refreshParams.append('date_posted_filter', 'any');

        fetch(`https://ai-job-aggregator-1.onrender.com/api/jobs?${refreshParams.toString()}`)
            .then(res => res.json())
            .then(data => {
                if (data.length > 0) {
                    setJobs(data);
                    setStatusMessage('List refreshed!');
                } else {
                    setStatusMessage('No new jobs in the cache yet. Check back later.');
                    if (jobs.length === 0) setJobs(generateMockJobs(fetchKeyword, fetchLocation));
                }
                setIsFetching(false);
                setTimeout(() => setStatusMessage(''), 3000);
            });
    };



    const filteredJobs = useMemo(() => {
        return jobs.filter(job => {
            const term = searchTerm.toLowerCase().trim();
            const synonyms = { 'sde': ['sde', 'software', 'engineer'], 'mern': ['mern', 'react'] };
            const searchTerms = synonyms[term] || [term];
            const matchesSearch = searchTerms.some(t => job.title.toLowerCase().includes(t) || job.company.toLowerCase().includes(t));
            return matchesSearch;
        });
    }, [jobs, searchTerm, filterType]);

    const indexOfLastJob = currentPage * jobsPerPage;
    const indexOfFirstJob = indexOfLastJob - jobsPerPage;
    const currentDisplayedJobs = filteredJobs.slice(indexOfFirstJob, indexOfLastJob);
    const totalPages = Math.ceil(filteredJobs.length / jobsPerPage);

    const paginate = (pageNumber) => {
        setCurrentPage(pageNumber);
        window.scrollTo({ top: document.querySelector('.results-section').offsetTop - 100, behavior: 'smooth' });
    };

    useEffect(() => {
        if (currentPage > totalPages && totalPages > 0) setCurrentPage(totalPages);
    }, [totalPages, currentPage]);

    return (
        <div onClick={() => { setSelectedJob(null); setShowCitySuggestions(false); }}>
            <div className="fetch-section" onClick={e => e.stopPropagation()}>
                <h1>Find Your Next Great Opportunity</h1>
                <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>Search thousands of tech jobs aggregated globally.</p>

                <div className="search-container" style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', position: 'relative' }}>
                    <input type="text" className="fetch-input" placeholder="Job Role (e.g. Manager)" value={fetchKeyword} onChange={e => setFetchKeyword(e.target.value)} style={{ flex: '1 1 200px' }} />
                    <div className="location-wrapper" style={{ position: 'relative', flex: '1 1 200px' }}>
                        <input type="text" className="fetch-input" placeholder="City (e.g. Delhi)" value={fetchLocation} onChange={handleLocationChange} onFocus={() => { if (fetchLocation) setShowCitySuggestions(true); }} style={{ width: '100%' }} />
                        {showCitySuggestions && (
                            <ul className="city-suggestions" style={{ position: 'absolute', top: '100%', left: 0, right: 0, background: '#1a1a1a', border: '1px solid #333', borderRadius: '8px', maxHeight: '200px', overflowY: 'auto', zIndex: 1000, listStyle: 'none', padding: 0, margin: '4px 0' }}>
                                {filteredCities.map(city => <li key={city} onClick={() => selectCity(city)} style={{ padding: '8px 12px', cursor: 'pointer', borderBottom: '1px solid #222', color: '#eee' }} onMouseEnter={e => e.target.style.background = '#333'} onMouseLeave={e => e.target.style.background = 'transparent'}>{city}</li>)}
                            </ul>
                        )}
                    </div>
                    <button className="fetch-btn" onClick={handleFetchJobs} disabled={isFetching}>{isFetching ? 'Searching...' : 'Search'}</button>
                </div>
                {statusMessage && <div className="status-msg">{statusMessage}</div>}
            </div>

            <div className="results-section">
                {!hasSearched ? (
                    <div className="welcome-placeholder" style={{ textAlign: 'center', padding: '4rem', color: '#888' }}>
                        <h2>Discover Your Next Opportunity</h2>
                        <p style={{ marginTop: '1rem', fontSize: '1.2rem' }}>AI-powered job search tailored for you.</p>
                    </div>
                ) : (isFetching && jobs.length === 0) ? (
                    <div className="loading-placeholder" style={{ textAlign: 'center', padding: '4rem', color: '#888' }}>
                        <h2>Searching for opportunities...</h2>
                    </div>
                ) : (
                    <>
                        <h2>Found Opportunities ({filteredJobs.length})</h2>
                        <div className="controls" onClick={e => e.stopPropagation()} style={{ flexWrap: 'wrap', gap: '10px' }}>
                            <input type="text" className="search-bar" placeholder="Filter results locally..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} style={{ flex: '1 1 200px' }} />
                            <button className="refresh-btn" onClick={handleRefresh} disabled={isFetching}>{isFetching ? 'Refreshing...' : 'Refresh List'}</button>
                        </div>

                        <div className="job-list">
                            {isFetching && jobs.length === 0 ? (
                                Array.from({ length: 6 }).map((_, idx) => (
                                    <div key={`skeleton-${idx}`} className="skeleton-card"><div className="skeleton-title"></div><div className="skeleton-company"></div><div className="skeleton-tags"><div className="skeleton-tag"></div><div className="skeleton-tag" style={{ width: '60px' }}></div></div><div className="skeleton-company" style={{ width: '50%', marginTop: 'auto' }}></div><div className="skeleton-btn"></div></div>
                                ))
                            ) : filteredJobs.length === 0 ? (
                                <div className="no-jobs">No new jobs found for this search. Try broader terms.</div>
                            ) : (
                                currentDisplayedJobs.map((job, index) => (
                                    <div key={job.id || index} className="job-card" onClick={(e) => { e.stopPropagation(); navigate(`/job/${job.id}`); }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                            <h3 style={{ margin: 0, paddingRight: '2rem' }}>{job.title}</h3>
                                        </div>

                                        <div className="company" style={{ marginTop: '0.5rem' }}>{job.company}</div>

                                        <div className="tags">
                                            <span className={`tag ${job.job_type?.toLowerCase().includes('intern') ? 'internship' : 'fulltime'}`}>{job.job_type || 'Full-time'}</span>
                                            {job.is_remote && <span className="tag">Remote</span>}
                                            <span className="tag site-tag" style={{ background: '#f0f0f0', color: '#333', border: '1px solid #ddd' }}>{job.site || 'Source'}</span>
                                        </div>

                                        <div className="details">
                                            <div className="location">📍 {job.location}</div>
                                            {job.salary_max && <div className="salary">💰 {job.salary_min ? `${job.salary_min} - ` : ''}{job.salary_max}</div>}
                                            <div className="date-posted">📅 {job.date_posted || 'Recently'}</div>
                                        </div>

                                        <a href={job.job_url || job.url} target="_blank" rel="noopener noreferrer" className="apply-btn" onClick={e => e.stopPropagation()}>{job.job_url || job.url ? 'Apply Now' : 'No Link Available'}</a>
                                    </div>
                                ))
                            )}
                        </div>

                        {totalPages > 1 && !isFetching && (
                            <div className="pagination-controls">
                                <button className="page-btn" onClick={() => paginate(currentPage - 1)} disabled={currentPage === 1}>Previous</button>
                                <span className="page-info">Page {currentPage} of {totalPages}</span>
                                <button className="page-btn" onClick={() => paginate(currentPage + 1)} disabled={currentPage === totalPages}>Next</button>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}

export default JobSearch;
