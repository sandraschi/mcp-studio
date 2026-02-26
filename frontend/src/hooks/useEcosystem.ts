import { useState, useEffect } from 'react';
import { api } from '../services/api';

export interface EcosystemApp {
    id: string;
    label: string;
    description: string;
    url: string;
    port: number;
    tags: string[];
}

export const useEcosystem = () => {
    const [apps, setApps] = useState<EcosystemApp[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchApps = async () => {
        setLoading(true);
        const response = await api.getEcosystemApps();
        if (response.data) {
            setApps(response.data);
            setError(null);
        } else {
            setError(response.error || 'Failed to fetch ecosystem apps');
        }
        setLoading(false);
    };

    const checkUrlUp = async (url: string, timeoutMs = 2500): Promise<boolean> => {
        try {
            const c = new AbortController();
            const t = setTimeout(() => c.abort(), timeoutMs);
            const r = await fetch(url, { method: 'GET', signal: c.signal, cache: 'no-store' });
            clearTimeout(t);
            return r.ok;
        } catch {
            return false;
        }
    };

    const launchApp = async (app: EcosystemApp) => {
        const up = await checkUrlUp(app.url);
        if (up) {
            window.open(app.url, '_blank', 'noopener,noreferrer');
            return true;
        }

        // Potential logic for auto-launching via proxy /api/webapp-launch could go here
        // For now, we just open it and hope for the best if we can't detect it's up
        window.open(app.url, '_blank', 'noopener,noreferrer');
        return false;
    };

    useEffect(() => {
        fetchApps();
    }, []);

    return { apps, loading, error, refreshApps: fetchApps, launchApp };
};
