import React, { useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthContext } from './AuthContext';

function Navbar({ toggleTheme, theme }) {
    const { user, logout } = useContext(AuthContext);
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/');
    };

    return (
        <header style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '1rem 2rem',
            marginBottom: '3rem',
            borderBottom: '1px solid var(--glass-border)',
            background: 'var(--card-bg)',
            backdropFilter: 'blur(12px)',
            borderRadius: '0 0 20px 20px'
        }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <Link to="/" style={{ textDecoration: 'none' }}>
                    <h1 style={{ fontSize: '2rem', margin: 0, padding: 0 }}>Ai Job Aggregator</h1>
                </Link>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                <button className="theme-toggle" onClick={toggleTheme} aria-label="Toggle Theme" style={{ position: 'relative', top: 0, right: 0 }}>
                    {theme === 'light' ? '🌙' : '☀️'}
                </button>

                {user ? (
                    <>
                        <Link to="/dashboard" style={{ textDecoration: 'none', color: 'var(--text-primary)', fontWeight: '600' }}>
                            Dashboard
                        </Link>
                        <button
                            onClick={handleLogout}
                            style={{
                                background: 'transparent',
                                border: '1px solid var(--text-secondary)',
                                color: 'var(--text-secondary)',
                                padding: '0.5rem 1rem',
                                borderRadius: '8px',
                                cursor: 'pointer',
                                fontWeight: '600'
                            }}
                        >
                            Logout
                        </button>
                    </>
                ) : (
                    <>
                        <Link to="/login" style={{ textDecoration: 'none', color: 'var(--text-primary)', fontWeight: '600' }}>
                            Sign In
                        </Link>
                        <Link to="/register">
                            <button className="fetch-btn" style={{ padding: '0.6rem 1.2rem', fontSize: '0.9rem' }}>
                                Sign Up
                            </button>
                        </Link>
                    </>
                )}
            </div>
        </header>
    );
}

export default Navbar;
