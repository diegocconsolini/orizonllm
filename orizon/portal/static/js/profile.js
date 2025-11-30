/**
 * Orizon Profile Page JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    loadUserProfile();
    setupEventListeners();
});

/**
 * Load user profile data
 */
async function loadUserProfile() {
    try {
        const response = await fetch('/api/auth/me');

        if (!response.ok) {
            if (response.status === 401) {
                // Not authenticated, redirect to login
                window.location.href = '/login';
                return;
            }
            throw new Error('Failed to load profile');
        }

        const data = await response.json();

        // Update profile info
        document.getElementById('user-name').textContent = data.name || 'User';
        document.getElementById('user-email').textContent = data.email;

        // Update avatar with initials
        const avatar = document.getElementById('user-avatar');
        if (data.avatar_url) {
            avatar.innerHTML = `<img src="${data.avatar_url}" alt="Avatar">`;
        } else {
            avatar.textContent = getInitials(data.name || data.email);
        }

        // Update API key
        document.getElementById('api-key').textContent = data.virtual_key || 'No key available';

        // Load usage stats
        loadUsageStats();

    } catch (error) {
        console.error('Error loading profile:', error);
        showToast('Failed to load profile', 'error');
    }
}

/**
 * Load usage statistics
 */
async function loadUsageStats() {
    try {
        const response = await fetch('/api/auth/usage');

        if (!response.ok) {
            return; // Usage stats are optional
        }

        const data = await response.json();

        document.getElementById('requests-count').textContent =
            formatNumber(data.requests_today || 0);
        document.getElementById('tokens-count').textContent =
            formatNumber(data.tokens_used || 0);

    } catch (error) {
        console.error('Error loading usage stats:', error);
    }
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
    // Logout button
    document.getElementById('logout-btn').addEventListener('click', handleLogout);

    // Copy API key button
    document.getElementById('copy-key-btn').addEventListener('click', copyApiKey);
}

/**
 * Handle logout
 */
async function handleLogout() {
    try {
        const response = await fetch('/api/auth/logout', {
            method: 'POST',
        });

        if (response.ok) {
            window.location.href = '/login';
        } else {
            showToast('Logout failed', 'error');
        }
    } catch (error) {
        console.error('Logout error:', error);
        showToast('Logout failed', 'error');
    }
}

/**
 * Copy API key to clipboard
 */
async function copyApiKey() {
    const apiKey = document.getElementById('api-key').textContent;

    if (!apiKey || apiKey === 'Loading...' || apiKey === 'No key available') {
        showToast('No API key to copy', 'error');
        return;
    }

    try {
        await navigator.clipboard.writeText(apiKey);
        showToast('API key copied to clipboard', 'success');
    } catch (error) {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = apiKey;
        textArea.style.position = 'fixed';
        textArea.style.left = '-9999px';
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            showToast('API key copied to clipboard', 'success');
        } catch (err) {
            showToast('Failed to copy API key', 'error');
        }
        document.body.removeChild(textArea);
    }
}

/**
 * Get initials from name or email
 */
function getInitials(nameOrEmail) {
    if (!nameOrEmail) return '?';

    // If it's an email, get first letter
    if (nameOrEmail.includes('@')) {
        return nameOrEmail.charAt(0).toUpperCase();
    }

    // Get initials from name
    const parts = nameOrEmail.trim().split(/\s+/);
    if (parts.length >= 2) {
        return (parts[0].charAt(0) + parts[parts.length - 1].charAt(0)).toUpperCase();
    }
    return parts[0].charAt(0).toUpperCase();
}

/**
 * Format large numbers
 */
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = 'toast ' + type + ' show';

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}
