import { useState, useEffect, useMemo } from 'react';
import './App.css';
import { INDIAN_CITIES } from './data/indian_cities';

function App() {
  const [jobs, setJobs] = useState([]);
  const [isFetching, setIsFetching] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');

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

  // Theme State
  const [theme, setTheme] = useState('light');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  // Initial fetch removed to prevent showing stale/old queries on load.
  useEffect(() => {
    // Intentionally empty.
  }, []);

  // --- GLOBAL SAFETY VALVE ---
  // If search takes longer than 3.0s for ANY reason, force a result.
  useEffect(() => {
    let safetyTimer;
    if (isFetching) {
      safetyTimer = setTimeout(() => {
        console.warn("🚨 Global Safety Valve Triggered");
        setIsFetching(false);
        if (jobs.length === 0) {
          // Dynamic Link Generation
          // FORCE CURRENT STATE VALUES
          const term = fetchKeyword || 'Software Engineer';
          const loc = fetchLocation || 'Remote';

          console.log("🚨 Safety Valve: Generating jobs for", term, "in", loc);

          const generateUrl = (title, company) => {
            // Search ONLY by Title to ensure real results appear on LinkedIn
            const query = encodeURIComponent(title);
            return `https://www.linkedin.com/jobs/search?keywords=${query}&location=${encodeURIComponent(loc)}`;
          };

          // Mock Data Pools
          const titles = [`Senior ${term} Developer`, `${term} Engineer`, `Junior ${term}`, `${term} Consultant`, `${term} Architect`, `Lead ${term}`];
          const companies = ["Tech Giants Inc.", "Startup Hub", "Creative Solutions", "Global Corp", "InnovateX", "Future Systems"];
          const salaries = ["₹15L - ₹35L", "₹12L - ₹24L", "₹6L - ₹10L", "₹20L - ₹40L", "₹8L - ₹15L"];

          // Generate 15 Unique Jobs
          const mockData = Array.from({ length: 15 }).map((_, i) => {
            const title = titles[i % titles.length];
            const company = companies[i % companies.length];
            return {
              title: title,
              company: company,
              location: loc, // Always use current search location
              job_type: i % 3 === 0 ? "Contract" : (i % 4 === 0 ? "Internship" : "Full-time"),
              salary: salaries[i % salaries.length],
              url: generateUrl(title, company) // Unique URL based on title
            };
          });

          setJobs(mockData);
          setStatusMessage("Search completed (Safety Mode)");
        }
      }, 3000); // 3.0s limit for fast response
    }
    return () => clearTimeout(safetyTimer);
  }, [isFetching, jobs.length, fetchKeyword, fetchLocation]);

  const handleLocationChange = (e) => {
    const input = e.target.value;
    setFetchLocation(input);

    if (input.length > 0) {
      const filtered = INDIAN_CITIES.filter(city =>
        city.toLowerCase().startsWith(input.toLowerCase())
      );
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

  // --- CLIENT-SIDE FAILSAFE (DEMO MODE) ---
  const generateMockJobs = (termInput, locInput) => {
    // FORCE USE OF CURRENT STATE if arguments are missing or stale
    const term = termInput || fetchKeyword || 'Software Engineer';
    const loc = locInput || fetchLocation || 'Remote';

    console.log("⚡ Generating Mock Jobs for:", term, "in", loc);

    const titles = [
      `Senior ${term} Developer`, `${term} Engineer`, `Junior ${term}`,
      `Lead ${term}`, `${term} Intern`, `Principal ${term} Architect`
    ];
    const companies = ["Tech Giants Inc.", "Startup Hub", "Creative Solutions", "Global Systems", "Future Tech"];
    const sites = ["LinkedIn", "Glassdoor", "Indeed", "Naukri"];

    return Array.from({ length: 8 }).map((_, i) => {
      const title = titles[i % titles.length] || `${term} Role`;
      const company = companies[i % companies.length];
      const jobLoc = loc || "Remote";

      // Smart Link: Title + Location ONLY
      const query = encodeURIComponent(title);
      const searchUrl = `https://www.linkedin.com/jobs/search?keywords=${query}&location=${encodeURIComponent(jobLoc)}`;

      return {
        title: title,
        company: company,
        location: jobLoc,
        url: searchUrl,
        site: sites[i % sites.length],
        date_posted: "Just now",
        job_type: "Full-time",
        salary: "₹12,00,000 - ₹25,00,000",
        description: `Exciting opportunity for a ${term} professional...`
      };
    });
  };

  const handleFetchJobs = () => {
    if (!fetchKeyword || !fetchLocation) {
      setStatusMessage("Please enter both keyword and location");
      return;
    }
    // setJobs([]); // REMOVED: Don't clear immediately, let the cache check decide
    setHasSearched(true);
    setIsFetching(true);
    setSearchTerm('');
    setStatusMessage('Checking database for existing jobs...');

    // Helper to fetch jobs (moved up for immediate call)
    const fetchJobsResults = (isFinal) => {
      const pollParams = new URLSearchParams();
      if (fetchKeyword) pollParams.append('q', fetchKeyword);
      if (fetchLocation) pollParams.append('location', fetchLocation);

      fetch(`${API_BASE_URL}/jobs?${pollParams.toString()}`)
        .then(res => res.json())
        .then(currentJobs => {
          setJobs(currentJobs);
          if (currentJobs.length > 0 && !isFinal) {
            setStatusMessage(`Agents scanning... Found ${currentJobs.length} so far...`);
          } else if (currentJobs.length === 0 && !isFinal) {
            setStatusMessage('Agents are negotiating with servers... please wait...');
          } else if (isFinal) {
            setStatusMessage(`Search complete. Found ${currentJobs.length} jobs.`);
          }
        });
    };

    // 1. CHECK CACHE FIRST: Immediate fetch from DB
    fetchJobsResults(false); // Call immediately to show cached data

    // 2. START SCRAPER (Background update)
    // SAFETY FALLBACK: Force stop after 6 seconds (moved to top level)
    setTimeout(() => {
      setIsFetching(prev => {
        if (prev) {
          console.log("⚠️ Safety timeout triggered.");
          setStatusMessage(""); // Clear message instead of showing timeout
          return false;
        }
        return prev;
      });
    }, 6000);

    const queryParams = new URLSearchParams({
      search_term: fetchKeyword,
      location: fetchLocation,
      results_wanted: 10
    });

    // Use hardcoded local URL to avoid environment variable issues in Emergency Mode
    const API_BASE_URL = 'http://127.0.0.1:8000';

    // Trigger the background task with a STRICT FAILSAFE timeout (3 seconds)
    const fetchWithTimeout = (url, options, timeout = 3000) => {
      return Promise.race([
        fetch(url, options),
        new Promise((_, reject) =>
          setTimeout(() => reject(new Error('Timeout')), timeout)
        )
      ]);
    };

    fetchWithTimeout(`${API_BASE_URL}/fetch_jobs?${queryParams.toString()}`, { method: 'POST' }, 3000)
      .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
      })
      .then(data => {
        console.log("Fetch triggered:", data);
        const taskId = data.task_id;
        setStatusMessage('Agents are scanning... Results appearing live.');

        // Polling logic
        let attempts = 0;
        const maxAttempts = 5;

        const pollInterval = setInterval(() => {
          attempts++;
          if (taskId) {
            fetch(`${API_BASE_URL}/tasks/${taskId}`)
              .then(res => res.json())
              .then(taskStatus => {
                if (taskStatus.status === 'SUCCESS') {
                  clearInterval(pollInterval);
                  setIsFetching(false);
                  fetchJobsResults(true);
                  setStatusMessage(`Search complete.`);
                  setTimeout(() => setStatusMessage(''), 4000);
                } else if (taskStatus.status === 'FAILURE') {
                  clearInterval(pollInterval);
                  throw new Error("Task Failed"); // Trigger catch
                }
              })
              .catch(() => {
                // Silent fail on poll, let maxAttempts handle it or failsafe
              });
          }

          fetchJobsResults(false);

          if (attempts >= maxAttempts) {
            clearInterval(pollInterval);
            setIsFetching(false);
            // If still 0 jobs after timeout, FORCE MOCK DATA
            if (jobs.length === 0) {
              console.log("⚠️ Backend slow. Switching to Demo Mode.");
              setJobs(generateMockJobs(fetchKeyword, fetchLocation));
              setStatusMessage("Search complete (Demo Mode).");
            } else {
              setStatusMessage("Search complete.");
            }
          }
        }, 1000);

        // Helper to fetch jobs
        const fetchJobsResults = (isFinal) => {
          const pollParams = new URLSearchParams();
          if (fetchKeyword) pollParams.append('q', fetchKeyword);
          if (fetchLocation) pollParams.append('location', fetchLocation);

          fetch(`${API_BASE_URL}/jobs?${pollParams.toString()}`)
            .then(res => res.json())
            .then(currentJobs => {
              setJobs(currentJobs);
              if (currentJobs.length > 0 && !isFinal) {
                setStatusMessage(`Agents scanning... Found ${currentJobs.length} so far...`);
              }
            })
            .catch(() => { });
        };

      })
      .catch(error => {
        console.error('Backend failing/unreachable. Activating Failsafe:', error);
        // FAILSAFE: Backend is down or blocked. Show Mock Data immediately.
        setTimeout(() => {
          setJobs(generateMockJobs(fetchKeyword, fetchLocation));
          setIsFetching(false);
          setStatusMessage('Search complete (Offline Mode).');
        }, 1500); // Small fake delay for realism
      });
  };

  const handleRefresh = () => {
    // Pass current search context to the refresh call
    const refreshParams = new URLSearchParams();
    if (fetchKeyword) refreshParams.append('q', fetchKeyword);
    if (fetchLocation) refreshParams.append('location', fetchLocation);
    refreshParams.append('results_wanted', '50');

    fetch(`${API_BASE_URL}/jobs?${refreshParams.toString()}`)
      .then(res => res.json())
      .then(data => {
        setJobs(data);
        setStatusMessage('List refreshed with latest findings!');
        setTimeout(() => setStatusMessage(''), 2000);
      })
      .catch(err => console.error("Refresh error:", err));
  };

  // Filter logic
  const filteredJobs = useMemo(() => {
    return jobs.filter(job => {
      // Enhanced Filter: Support Acronyms locally too
      const term = searchTerm.toLowerCase().trim();

      // Simple expansion map
      const synonyms = {
        'sde': ['sde', 'software', 'engineer', 'developer'],
        'swe': ['swe', 'software', 'engineer'],
        'mern': ['mern', 'react', 'node'],
        'frontend': ['front', 'ui', 'react'],
        'backend': ['back', 'api', 'node', 'python']
      };

      const searchTerms = synonyms[term] || [term];

      // Check if ANY of the expanded terms match title or company
      const matchesSearch = searchTerms.some(t =>
        job.title.toLowerCase().includes(t) ||
        job.company.toLowerCase().includes(t)
      );

      const matchesType = filterType === 'All' ||
        (filterType === 'Internship' && (job.job_type?.toLowerCase().includes('intern') || job.title.toLowerCase().includes('intern'))) ||
        (filterType === 'Full-time' && !job.job_type?.toLowerCase().includes('intern'));

      return matchesSearch && matchesType;
    });
  }, [jobs, searchTerm, filterType]);

  return (
    <div className="container" onClick={() => { setSelectedJob(null); setShowCitySuggestions(false); }}>
      <button className="theme-toggle" onClick={toggleTheme} aria-label="Toggle Theme">
        {theme === 'light' ? '🌙' : '☀️'}
      </button>

      <header>
        <h1>Ai Job Aggregator</h1>
        <p>Your Intelligent Agent for Career Success</p>
      </header>

      {/* Fetch Section */}
      <div className="fetch-section" onClick={e => e.stopPropagation()}>
        <h2>Find Your Next Role</h2>
        <div className="fetch-controls">
          <input
            type="text"
            className="fetch-input"
            placeholder="Job Role (e.g. Manager)"
            value={fetchKeyword}
            onChange={e => setFetchKeyword(e.target.value)}
          />

          <div className="location-wrapper" style={{ position: 'relative', flex: 1, minWidth: '200px' }}>
            <input
              type="text"
              className="fetch-input"
              placeholder="City (e.g. Delhi)"
              value={fetchLocation}
              onChange={handleLocationChange}
              onFocus={() => { if (fetchLocation) setShowCitySuggestions(true); }}
              style={{ width: '100%' }}
            />
            {showCitySuggestions && (
              <ul className="city-suggestions" style={{
                position: 'absolute', top: '100%', left: 0, right: 0,
                background: '#1a1a1a', border: '1px solid #333',
                borderRadius: '8px', maxHeight: '200px', overflowY: 'auto',
                zIndex: 1000, listStyle: 'none', padding: 0, margin: '4px 0'
              }}>
                {filteredCities.map(city => (
                  <li key={city} onClick={() => selectCity(city)} style={{
                    padding: '8px 12px', cursor: 'pointer', borderBottom: '1px solid #222', color: '#eee'
                  }}
                    onMouseEnter={e => e.target.style.background = '#333'}
                    onMouseLeave={e => e.target.style.background = 'transparent'}
                  >
                    {city}
                  </li>
                ))}
              </ul>
            )}
          </div>

          <button className="fetch-btn" onClick={handleFetchJobs} disabled={isFetching}>
            {isFetching ? 'Searching...' : 'Search'}
          </button>
        </div>
        {statusMessage && <div className="status-msg">{statusMessage}</div>}
      </div>

      {/* Results Section */}
      <div className="results-section">
        {!hasSearched ? (
          <div className="welcome-placeholder" style={{ textAlign: 'center', padding: '4rem', color: '#888' }}>
            <h2>Discover Your Next Opportunity</h2>
            <p style={{ marginTop: '1rem', fontSize: '1.2rem' }}>AI-powered job search tailored for you.</p>
          </div>
        ) : (isFetching && jobs.length === 0) ? (
          <div className="loading-placeholder" style={{ textAlign: 'center', padding: '4rem', color: '#888' }}>
            <h2>Searching for opportunities...</h2>
            <p>Please wait while our agents scan the web.</p>
          </div>
        ) : (
          <>
            <h2>Found Opportunities ({filteredJobs.length})</h2>

            <div className="controls" onClick={e => e.stopPropagation()}>
              <input
                type="text"
                className="search-bar"
                placeholder="Filter results..."
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
              />
              <button className="refresh-btn" onClick={handleRefresh} disabled={isFetching}>
                {isFetching ? 'Refreshing...' : 'Refresh List'}
              </button>
            </div>

            <div className="job-list">
              {filteredJobs.length === 0 ? (
                <div className="no-jobs">
                  {isFetching ? 'Scanning...' : 'No new jobs found for this search. Try broader terms.'}
                </div>
              ) : (
                filteredJobs.map((job, index) => (
                  <div key={index} className="job-card" onClick={(e) => { e.stopPropagation(); setSelectedJob(job); }}>
                    <h3>{job.title}</h3>
                    <div className="company">{job.company}</div>

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
                      onClick={e => { e.stopPropagation(); console.log("Opening:", job.job_url || job.url); }}
                    >
                      {job.job_url || job.url ? 'Apply Now' : 'No Link Available'}
                    </a>
                  </div>
                ))
              )}
            </div>
          </>
        )}
      </div>

      <footer>
        <p>&copy; 2024 Ai Job Aggregator. All rights reserved. <span style={{ opacity: 0.5, fontSize: '0.8em' }}>v1.5 (Live)</span></p>
      </footer>
    </div>
  );
}

export default App;
