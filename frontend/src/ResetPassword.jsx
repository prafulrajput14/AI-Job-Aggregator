import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import toast from 'react-hot-toast';

function ResetPassword() {
    const { token } = useParams();
    const navigate = useNavigate();
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isSuccess, setIsSuccess] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (password.length < 6) {
            toast.error('Password must be at least 6 characters');
            return;
        }

        if (password !== confirmPassword) {
            toast.error('Passwords do not match');
            return;
        }

        setIsLoading(true);

        try {
            const response = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/reset-password`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token, new_password: password })
            });

            if (response.ok) {
                setIsSuccess(true);
                toast.success('Password reset successfully!');
                setTimeout(() => {
                    navigate('/login');
                }, 3000);
            } else {
                const data = await response.json();
                toast.error(data.detail || 'Invalid or expired token.');
            }
        } catch (err) {
            console.error(err);
            toast.error('Network error occurred');
        } finally {
            setIsLoading(false);
        }
    };

    if (isSuccess) {
        return (
            <div className="container" style={{ maxWidth: '500px', marginTop: '4rem' }}>
                <div className="fetch-section" style={{ padding: '3rem 2rem', textAlign: 'center' }}>
                    <h2 style={{ marginBottom: '1rem', color: '#10b981' }}>Password Changed!</h2>
                    <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>
                        Your password has been successfully updated. Redirecting to login...
                    </p>
                    <Link to="/login" className="apply-btn" style={{ textDecoration: 'none' }}>Go to Login manually</Link>
                </div>
            </div>
        );
    }

    return (
        <div className="container" style={{ maxWidth: '500px', marginTop: '4rem' }}>
            <div className="fetch-section" style={{ padding: '3rem 2rem' }}>
                <h2 style={{ textAlign: 'center', marginBottom: '1rem' }}>Create New Password</h2>
                <p style={{ textAlign: 'center', color: 'var(--text-secondary)', marginBottom: '2rem' }}>
                    Please enter your new password below.
                </p>

                <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                    <div>
                        <input
                            type="password"
                            className="fetch-input"
                            placeholder="New Password (min 6 chars)"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            minLength="6"
                            style={{ width: '100%' }}
                        />
                    </div>
                    <div>
                        <input
                            type="password"
                            className="fetch-input"
                            placeholder="Confirm New Password"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            required
                            style={{ width: '100%' }}
                        />
                    </div>

                    <button type="submit" className="fetch-btn" disabled={isLoading} style={{ width: '100%', marginTop: '1rem' }}>
                        {isLoading ? 'Updating...' : 'Update Password'}
                    </button>
                </form>
            </div>
        </div>
    );
}

export default ResetPassword;
