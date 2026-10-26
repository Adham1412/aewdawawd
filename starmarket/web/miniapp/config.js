// For deployment, set API_URL to the public HTTPS backend origin + /api/v1.
// Example: window.STARMARKET_API_URL = 'https://api.your-domain.example/api/v1';
window.STARMARKET_API_URL = window.STARMARKET_API_URL || `${location.origin}/api/v1`;
