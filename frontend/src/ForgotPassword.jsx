import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';

function ForgotPassword() {
    const [email, setEmail] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isSent, setIsSent] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);

        try {
            const response = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/forgot-password`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email })
            });

            if (response.ok) {
                setIsSent(true);
                toast.success('Reset link sent!');
            } else {
                toast.error('Failed to send reset link');
            }
        } catch (err) {
            console.error(err);
            toast.error('Network error occurred');
        } finally {
            setIsLoading(false);
        }
    };

    if (isSent) {
        return (
            <div className="container" style={{ maxWidth: '500px', marginTop: '4rem' }}>
                <div className="fetch-section" style={{ padding: '3rem 2rem', textAlign: 'center' }}>
                    <h2 style={{ marginBottom: '1rem', color: '#10b981' }}>Check Your Email</h2>
                    <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>
                        We've sent a password reset link to <strong>{email}</strong>. It will expire in 1 hour.
                    </p>
                    <Link to="/login" className="apply-btn" style={{ textDecoration: 'none' }}>Return to Login</Link>
                </div>
            </div>
        );
    }

    return (
        <div className="container" style={{ maxWidth: '500px', marginTop: '4rem' }}>
            <div className="fetch-section" style={{ padding: '3rem 2rem' }}>
                <h2 style={{ textAlign: 'center', marginBottom: '1rem' }}>Forgot Password</h2>
                <p style={{ textAlign: 'center', color: 'var(--text-secondary)', marginBottom: '2rem' }}>
                    Enter your email address to receive a secure password reset link.
                </p>

                <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                    <div>
                        <input
                            type="email"
                            className="fetch-input"
                            placeholder="Email Address"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                            style={{ width: '100%' }}
                        />
                    </div>

                    <button type="submit" className="fetch-btn" disabled={isLoading} style={{ width: '100%', marginTop: '1rem' }}>
                        {isLoading ? 'Sending Link...' : 'Send Reset Link'}
                    </button>
                </form>

                <p style={{ textAlign: 'center', marginTop: '2rem', color: 'var(--text-secondary)' }}>
                    Remember your password? <Link to="/login" style={{ color: 'var(--accent-color)', fontWeight: '600', textDecoration: 'none' }}>Sign In</Link>
                </p>
            </div>
        </div>
    );
}

export default ForgotPassword;
