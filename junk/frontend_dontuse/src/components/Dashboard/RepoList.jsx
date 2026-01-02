import React, { useEffect, useState } from 'react';
import { reposService } from '../../services/repos';
import { Folder, RefreshCw } from 'lucide-react';

const RepoList = () => {
    const [repos, setRepos] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [scanData, setScanData] = useState(null);

    const fetchRepos = async () => {
        setLoading(true);
        try {
            const response = await reposService.getRepos();
            if (response.status === 'success') {
                setRepos(response.data || []);
                setScanData(null);
            } else if (response.status === 'no_data') {
                setRepos([]);
                setScanData(response);
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchRepos();
    }, []);

    const handleScan = async () => {
        try {
            await reposService.runScan();
            // In a real app we might poll for progress, but here just UI feedback
            setLoading(true); // temporary simple feedback
            setTimeout(fetchRepos, 2000); // refresh after a short delay
        } catch (err) {
            console.error("Scan failed", err);
        }
    };

    if (error) return <div style={{ color: 'red' }}>Error loading repos: {error}</div>;

    return (
        <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
                <h2 style={{ fontSize: '18px', margin: 0 }}>Repositories</h2>
                <button
                    onClick={handleScan}
                    style={{
                        background: 'transparent',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: '4px',
                        padding: '6px 10px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        cursor: 'pointer',
                        color: 'var(--text-primary)'
                    }}
                >
                    <RefreshCw size={14} /> Scan
                </button>
            </div>

            {loading && <div>Loading...</div>}

            {!loading && repos.length === 0 && (
                <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-muted)' }}>
                    {scanData ? scanData.message : 'No repositories found.'}
                </div>
            )}

            <div style={{ display: 'grid', gap: '10px' }}>
                {repos.map((repo, i) => (
                    <div key={i} style={{
                        background: 'var(--bg-card)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: 'var(--radius-sm)',
                        padding: '12px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between'
                    }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <Folder size={18} color="var(--accent-secondary)" />
                            <div>
                                <h4 style={{ margin: '0 0 2px 0', fontSize: '14px' }}>{repo.name}</h4>
                                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{repo.path}</span>
                            </div>
                        </div>
                        <div style={{ fontSize: '12px' }}>
                            {repo.status === 'SOTA' ? '✅ SOTA' : '⚠️ Improvable'}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default RepoList;
