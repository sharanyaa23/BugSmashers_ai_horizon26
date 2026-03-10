window.APP_CONFIG = Object.assign(
    {
        API_BASE_URL: 'http://localhost:8000/api',
        OPENROUTESERVICE_API_KEY: 'eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjMzYzA5OGIzN2NkNzQ5OTI5NGRiZDBjZjNiNDI3YjhmIiwiaCI6Im11cm11cjY0In0='
    },
    window.APP_CONFIG || {}
);

try {
    const storedKey = localStorage.getItem('OPENROUTESERVICE_API_KEY');
    if (storedKey) {
        window.APP_CONFIG.OPENROUTESERVICE_API_KEY = storedKey;
    }
} catch (error) {
    console.warn('Could not read local OpenRouteService key override.', error);
}
