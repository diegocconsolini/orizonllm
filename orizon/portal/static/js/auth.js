/**
 * Orizon Auth JavaScript
 *
 * Handles signup and login form submissions.
 */

document.addEventListener('DOMContentLoaded', () => {
    // Signup form handler
    const signupForm = document.getElementById('signup-form');
    if (signupForm) {
        signupForm.addEventListener('submit', handleSignup);
    }

    // Login form handler
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
});

/**
 * Handle signup form submission
 */
async function handleSignup(event) {
    event.preventDefault();

    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const email = form.querySelector('#email').value.trim();
    const name = form.querySelector('#name').value.trim();
    const company = form.querySelector('#company')?.value.trim() || '';

    // Validate
    if (!email || !name) {
        showError(form, 'Please fill in all required fields');
        return;
    }

    if (!isValidEmail(email)) {
        showError(form, 'Please enter a valid email address');
        return;
    }

    // Show loading state
    submitBtn.classList.add('loading');
    submitBtn.disabled = true;

    try {
        const response = await fetch('/api/auth/signup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, name, company }),
        });

        const data = await response.json();

        if (response.ok) {
            // Show success message
            showSuccessMessage(email);
        } else {
            showError(form, data.detail || 'Signup failed. Please try again.');
        }
    } catch (error) {
        console.error('Signup error:', error);
        showError(form, 'Network error. Please try again.');
    } finally {
        submitBtn.classList.remove('loading');
        submitBtn.disabled = false;
    }
}

/**
 * Handle login form submission
 */
async function handleLogin(event) {
    event.preventDefault();

    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const email = form.querySelector('#email').value.trim();

    // Validate
    if (!email) {
        showError(form, 'Please enter your email address');
        return;
    }

    if (!isValidEmail(email)) {
        showError(form, 'Please enter a valid email address');
        return;
    }

    // Show loading state
    submitBtn.classList.add('loading');
    submitBtn.disabled = true;

    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email }),
        });

        const data = await response.json();

        if (response.ok) {
            // Show success message
            showSuccessMessage(email);
        } else {
            showError(form, data.detail || 'Login failed. Please try again.');
        }
    } catch (error) {
        console.error('Login error:', error);
        showError(form, 'Network error. Please try again.');
    } finally {
        submitBtn.classList.remove('loading');
        submitBtn.disabled = false;
    }
}

/**
 * Show error message
 */
function showError(form, message) {
    // Remove existing error
    const existingError = form.parentElement.querySelector('.alert-error');
    if (existingError) {
        existingError.remove();
    }

    // Create error alert
    const alert = document.createElement('div');
    alert.className = 'alert alert-error';
    alert.textContent = message;

    // Insert before form
    form.parentElement.insertBefore(alert, form);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        alert.remove();
    }, 5000);
}

/**
 * Show success message
 */
function showSuccessMessage(email) {
    const authCard = document.querySelector('.auth-card:not(.success-card)');
    const successCard = document.getElementById('success-message');
    const sentEmail = document.getElementById('sent-email');

    if (authCard && successCard && sentEmail) {
        authCard.style.display = 'none';
        sentEmail.textContent = email;
        successCard.style.display = 'block';
    }
}

/**
 * Validate email format
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}
