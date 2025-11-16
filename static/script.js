document.addEventListener("DOMContentLoaded", function () {
    class PasswordManager {
        constructor() {
            this.init();
        }

        init() {
            this.initializePasswordToggles();
            this.initializeFormValidation();
            this.initializeRealTimeValidation();
        }

        // Password visibility toggle
        initializePasswordToggles() {
            document.querySelectorAll('.password-container').forEach(container => {
                const input = container.querySelector('input[type="password"], input[type="text"]');
                const toggle = container.querySelector('.toggle-password');
                if (!input || !toggle) return;

                toggle.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.togglePasswordVisibility(input, toggle);
                });
            });
        }

        togglePasswordVisibility(input, toggle) {
            const type = input.type === 'password' ? 'text' : 'password';
            input.type = type;
            toggle.innerHTML = type === 'password' 
                ? '<i class="fas fa-eye"></i>' 
                : '<i class="fas fa-eye-slash"></i>';
            input.focus();
        }

        // Form validation: password required ONLY (no more rules)
        initializeFormValidation() {
            document.querySelectorAll('form').forEach(form => {
                form.addEventListener('submit', (e) => {
                    if (!this.validateForm(form)) {
                        e.preventDefault();
                    }
                });
            });
        }

        validateForm(form) {
            let isValid = true;
            const errorMessages = [];

            // Required fields
            form.querySelectorAll('input[required], select[required], textarea[required]').forEach(input => {
                if (!input.value.trim()) {
                    isValid = false;
                    this.showFieldError(input, 'This field is required');
                    errorMessages.push(`${input.previousElementSibling?.textContent || 'Field'} is required`);
                } else {
                    this.clearFieldError(input);
                }
            });

            // Email validation
            const emailInput = form.querySelector('input[type="email"]');
            if (emailInput && emailInput.value.trim() && !this.isValidEmail(emailInput.value)) {
                isValid = false;
                this.showFieldError(emailInput, 'Please enter a valid email');
                errorMessages.push('Invalid email');
            }

            // Password NO RULES — only required
            const pwdInput = form.querySelector('input[name="password"]');
            if (pwdInput && !pwdInput.value.trim()) {
                isValid = false;
                this.showFieldError(pwdInput, 'Password is required');
                errorMessages.push('Password required');
            }

            // Confirm password
            const confirmPwdInput = form.querySelector('input[name="confirm_password"]');
            if (confirmPwdInput && pwdInput && confirmPwdInput.value !== pwdInput.value) {
                isValid = false;
                this.showFieldError(confirmPwdInput, 'Passwords do not match');
                this.showFieldError(pwdInput, 'Passwords do not match');
                errorMessages.push('Passwords do not match');
            }

            if (!isValid && errorMessages.length > 0) {
                this.showAlert(errorMessages.join('\n'), 'error');
            }

            return isValid;
        }

        // Real-time validation
        initializeRealTimeValidation() {

            document.querySelectorAll('input[name="confirm_password"]').forEach(input => {
                input.addEventListener('input', () => {
                    const pwdInput = input.form?.querySelector('input[name="password"]');

                    if (pwdInput && input.value !== pwdInput.value) {
                        this.showFieldError(input, 'Passwords do not match');
                        this.showFieldError(pwdInput, 'Passwords do not match');
                    } else {
                        this.clearFieldError(input);
                        if (pwdInput) this.clearFieldError(pwdInput);
                    }
                });
            });

            document.querySelectorAll('input[type="email"]').forEach(input => {
                input.addEventListener('blur', () => {
                    if (input.value.trim() && !this.isValidEmail(input.value)) {
                        this.showFieldError(input, 'Please enter a valid email address');
                    }
                });
            });

            document.querySelectorAll('input, select, textarea').forEach(field => {
                field.addEventListener('input', () => this.clearFieldError(field));
            });
        }

        // Utils
        isValidEmail(email) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return emailRegex.test(email);
        }

        showFieldError(field, message) {
            this.clearFieldError(field);
            field.style.borderColor = '#ef4444';
            const error = document.createElement('div');
            error.className = 'field-error';
            error.style.color = '#ef4444';
            error.style.fontSize = '0.8rem';
            error.style.marginTop = '5px';
            error.textContent = message;
            field.parentNode.appendChild(error);
        }

        clearFieldError(field) {
            field.style.borderColor = '';
            const existing = field.parentNode.querySelector('.field-error');
            if (existing) existing.remove();
        }

        showAlert(message, type = 'error') {
            this.removeExistingAlerts();
            const alert = document.createElement('div');
            alert.className = `alert alert-${type}`;
            alert.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 16px 20px;
                border-radius: 8px;
                color: ${type === 'error' ? '#ef4444' : '#10b981'};
                background-color: ${type === 'error' ? 'rgba(239,68,68,0.1)' : 'rgba(16,185,129,0.1)'};
                border: 1px solid ${type === 'error' ? 'rgba(239,68,68,0.2)' : 'rgba(16,185,129,0.2)'};
                z-index: 1000;
                max-width: 400px;
                box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
            `;
            const icon = type === 'error' ? 'fa-exclamation-triangle' : 'fa-check-circle';
            alert.innerHTML = `<div style="display:flex;align-items:center;gap:10px;">
                <i class="fas ${icon}"></i>
                <div style="flex:1;">${message}</div>
                <button type="button" class="close-alert" style="background:none;border:none;cursor:pointer;"><i class="fas fa-times"></i></button>
            </div>`;
            document.body.appendChild(alert);
            alert.querySelector('.close-alert').addEventListener('click', () => alert.remove());
            setTimeout(() => {
                if (alert.parentNode) alert.remove();
            }, 5000);
        }

        removeExistingAlerts() {
            document.querySelectorAll('.alert').forEach(a => a.remove());
        }
    }

    new PasswordManager();
});
