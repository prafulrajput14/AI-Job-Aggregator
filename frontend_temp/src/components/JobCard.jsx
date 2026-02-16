// src/components/JobCard.jsx
import React from 'react';

const JobCard = ({ job }) => {
  return (
    <div className="job-card">
      <h3>{job.title}</h3>
      <p className="company">{job.company}</p>
      <div className="tags">
        <span className={`tag ${job.is_internship ? 'internship' : 'fulltime'}`}>
          {job.is_internship ? 'Internship' : 'Full-time'}
        </span>
        {job.skills && job.skills.split(',').map(skill => (
          <span key={skill} className="tag skill">{skill.trim()}</span>
        ))}
      </div>
      <a href={job.url} target="_blank" rel="noopener noreferrer">Apply Now</a>
    </div>
  );
};

export default JobCard;
