const defaultConfig = {
    form_title: "Registration Form",
    client_label: "Client",
    interpreter_label: "Interpreter",
    google_button_text: "Continue with Google",
    background_color: "#667eea",
    surface_color: "#ffffff",
    text_color: "#1f2937",
    primary_action_color: "#667eea",
    secondary_action_color: "#e5e7eb",
    font_family: "Inter",
    font_size: 16
};

let config = {...defaultConfig};
let currentUserType = 'client';

const clientToggle = document.getElementById('client-toggle');
const interpreterToggle = document.getElementById('interpreter-toggle');
const interpreterFields = document.getElementById('interpreter-fields');
const form = document.getElementById('registration-form');
const successMessage = document.getElementById('success-message');
const googleRegisterBtn = document.getElementById('google-register');

function switchUserType(type) {
    currentUserType = type;

    // Динамически меняем action формы
    if (type === 'client') {
        form.action = "/auth/client-signup/"; // Замените на ваш URL

        clientToggle.classList.add('active');
        interpreterToggle.classList.remove('active');
        interpreterFields.classList.add('hidden');

        clientToggle.style.background = config.primary_action_color || defaultConfig.primary_action_color;
        clientToggle.style.borderColor = config.primary_action_color || defaultConfig.primary_action_color;
        clientToggle.style.color = 'white';

        interpreterToggle.style.background = 'white';
        interpreterToggle.style.borderColor = config.secondary_action_color || defaultConfig.secondary_action_color;
        interpreterToggle.style.color = '#6b7280';

        const interpreterInputs = interpreterFields.querySelectorAll('input, select');
        interpreterInputs.forEach(input => {
            input.removeAttribute('required');
        });
    } else {
        form.action = "/auth/interpreter-signup/"; // Замените на ваш URL

        interpreterToggle.classList.add('active');
        clientToggle.classList.remove('active');
        interpreterFields.classList.remove('hidden');

        interpreterToggle.style.background = config.primary_action_color || defaultConfig.primary_action_color;
        interpreterToggle.style.borderColor = config.primary_action_color || defaultConfig.primary_action_color;
        interpreterToggle.style.color = 'white';

        clientToggle.style.background = 'white';
        clientToggle.style.borderColor = config.secondary_action_color || defaultConfig.secondary_action_color;
        clientToggle.style.color = '#6b7280';

        const genderSelect = document.getElementById('gender');
        const citySelect = document.getElementById('city');
        if (genderSelect) genderSelect.setAttribute('required', 'required');
        if (citySelect) citySelect.setAttribute('required', 'required');
    }

    console.log('🔄 User type switched to:', type);
    console.log('📍 Form will submit to:', form.action);
}

// Инициализация событий
if (clientToggle && interpreterToggle) {
    clientToggle.addEventListener('click', () => switchUserType('client'));
    interpreterToggle.addEventListener('click', () => switchUserType('interpreter'));
    
    // Устанавливаем начальное состояние
    switchUserType('client');
}

// Multiselect опции
const multiselectOptions = document.querySelectorAll('.multiselect-option');
multiselectOptions.forEach(option => {
    option.addEventListener('click', (e) => {
        if (e.target.tagName !== 'INPUT') {
            const checkbox = option.querySelector('input[type="checkbox"]');
            checkbox.checked = !checkbox.checked;
        }
        option.classList.toggle('selected', option.querySelector('input[type="checkbox"]').checked);
    });
});

// Валидация формы
if (form) {
    form.addEventListener('submit', (e) => {
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirm-password').value;

        // Проверка совпадения паролей
        if (password !== confirmPassword) {
            e.preventDefault();
            showError('Passwords do not match!');
            return;
        }

        // Проверка для переводчиков
        if (currentUserType === 'interpreter') {
            const languages = Array.from(document.querySelectorAll('#languages-list input:checked')).map(cb => cb.value);
            const translationTypes = Array.from(document.querySelectorAll('#translation-type-list input:checked')).map(cb => cb.value);

            if (languages.length === 0 || translationTypes.length === 0) {
                e.preventDefault();
                showError('Please select at least one language and translation type!');
                return;
            }
        }

        console.log('✅ Form is valid, submitting to:', form.action);
    });
}

// Функция для показа ошибок
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;

    const existingError = form.querySelector('.error-message');
    if (existingError) existingError.remove();

    form.appendChild(errorDiv);
    setTimeout(() => errorDiv.remove(), 3000);
}

// Google OAuth
if (googleRegisterBtn) {
    googleRegisterBtn.addEventListener('click', () => {
        showGoogleUserTypeModal();
    });
}

function showGoogleUserTypeModal() {
    const modalOverlay = document.createElement('div');
    modalOverlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    `;

    const modalContent = document.createElement('div');
    modalContent.style.cssText = `
        background: white;
        border-radius: 1rem;
        padding: 2rem;
        max-width: 400px;
        width: 90%;
        text-align: center;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    `;

    modalContent.innerHTML = `
        <div style="margin-bottom: 1.5rem;">
            <h3 style="margin: 0 0 0.5rem 0; font-size: 1.5rem; font-weight: 700; color: #1f2937;">Continue with Google</h3>
            <p style="margin: 0; color: #6b7280; font-size: 0.875rem;">Select your account type</p>
        </div>

        <p style="margin-bottom: 1.5rem; color: #374151; font-weight: 600;">I want to register as:</p>

        <div style="display: flex; gap: 1rem; margin-bottom: 1.5rem;">
            <button id="modal-client-btn" style="flex: 1; padding: 1rem; border: 2px solid #667eea; background: #667eea; color: white; border-radius: 0.5rem; font-weight: 600; cursor: pointer;">
                Client
            </button>
            <button id="modal-interpreter-btn" style="flex: 1; padding: 1rem; border: 2px solid #e5e7eb; background: white; color: #6b7280; border-radius: 0.5rem; font-weight: 600; cursor: pointer;">
                Interpreter
            </button>
        </div>

        <button id="continue-with-google" style="width: 100%; padding: 0.875rem; background: #10b981; color: white; border: none; border-radius: 0.5rem; font-weight: 600; cursor: pointer; margin-bottom: 1rem;">
            Continue with Google
        </button>

        <button id="cancel-google-registration" style="width: 100%; padding: 0.875rem; background: transparent; color: #6b7280; border: none; cursor: pointer; font-weight: 500;">
            Cancel
        </button>
    `;

    modalOverlay.appendChild(modalContent);
    document.body.appendChild(modalOverlay);

    let selectedType = 'client';

    const modalClientBtn = modalContent.querySelector('#modal-client-btn');
    const modalInterpreterBtn = modalContent.querySelector('#modal-interpreter-btn');
    const continueBtn = modalContent.querySelector('#continue-with-google');
    const cancelBtn = modalContent.querySelector('#cancel-google-registration');

    function selectModalType(type) {
        selectedType = type;
        if (type === 'client') {
            modalClientBtn.style.background = '#667eea';
            modalClientBtn.style.borderColor = '#667eea';
            modalClientBtn.style.color = 'white';
            modalInterpreterBtn.style.background = 'white';
            modalInterpreterBtn.style.borderColor = '#e5e7eb';
            modalInterpreterBtn.style.color = '#6b7280';
        } else {
            modalInterpreterBtn.style.background = '#667eea';
            modalInterpreterBtn.style.borderColor = '#667eea';
            modalInterpreterBtn.style.color = 'white';
            modalClientBtn.style.background = 'white';
            modalClientBtn.style.borderColor = '#e5e7eb';
            modalClientBtn.style.color = '#6b7280';
        }
    }

    modalClientBtn.addEventListener('click', () => selectModalType('client'));
    modalInterpreterBtn.addEventListener('click', () => selectModalType('interpreter'));

    // Редирект на Google OAuth
    continueBtn.addEventListener('click', () => {
        continueBtn.textContent = 'Redirecting to Google...';
        continueBtn.disabled = true;
        continueBtn.style.opacity = '0.7';

        // Редирект с типом пользователя
        window.location.href = `/auth/google-login?user_type=${selectedType}`;
    });

    cancelBtn.addEventListener('click', () => {
        document.body.removeChild(modalOverlay);
    });

    modalOverlay.addEventListener('click', (e) => {
        if (e.target === modalOverlay) {
            document.body.removeChild(modalOverlay);
        }
    });
}

// Конфигурация (для SDK)
async function onConfigChange(newConfig) {
    const formTitle = document.getElementById('form-title');
    const clientLabel = document.getElementById('client-label');
    const interpreterLabel = document.getElementById('interpreter-label');
    const container = document.querySelector('.form-container');
    const formBox = container.querySelector('.form-box');
    const submitButton = form.querySelector('.submit-button');
    const labels = document.querySelectorAll('label');

    const customFont = newConfig.font_family || defaultConfig.font_family;
    const baseFontStack = '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    const baseSize = newConfig.font_size || defaultConfig.font_size;

    if (formTitle) formTitle.textContent = newConfig.form_title || defaultConfig.form_title;
    if (clientLabel) clientLabel.textContent = newConfig.client_label || defaultConfig.client_label;
    if (interpreterLabel) interpreterLabel.textContent = newConfig.interpreter_label || defaultConfig.interpreter_label;

    if (container) {
        container.style.background = `linear-gradient(135deg, ${newConfig.background_color || defaultConfig.background_color} 0%, ${newConfig.primary_action_color || defaultConfig.primary_action_color} 100%)`;
    }
    if (formBox) formBox.style.background = newConfig.surface_color || defaultConfig.surface_color;
    if (formTitle) formTitle.style.color = newConfig.text_color || defaultConfig.text_color;

    labels.forEach(label => {
        label.style.color = newConfig.text_color || defaultConfig.text_color;
    });

    if (submitButton) {
        submitButton.style.background = `linear-gradient(135deg, ${newConfig.primary_action_color || defaultConfig.primary_action_color} 0%, ${newConfig.background_color || defaultConfig.background_color} 100%)`;
    }

    if (googleRegisterBtn) {
        googleRegisterBtn.style.borderColor = newConfig.secondary_action_color || defaultConfig.secondary_action_color;
        googleRegisterBtn.style.color = newConfig.text_color || defaultConfig.text_color;
    }

    if (currentUserType === 'client' && clientToggle && interpreterToggle) {
        clientToggle.style.background = newConfig.primary_action_color || defaultConfig.primary_action_color;
        clientToggle.style.borderColor = newConfig.primary_action_color || defaultConfig.primary_action_color;
        interpreterToggle.style.borderColor = newConfig.secondary_action_color || defaultConfig.secondary_action_color;
    } else if (interpreterToggle && clientToggle) {
        interpreterToggle.style.background = newConfig.primary_action_color || defaultConfig.primary_action_color;
        interpreterToggle.style.borderColor = newConfig.primary_action_color || defaultConfig.primary_action_color;
        clientToggle.style.borderColor = newConfig.secondary_action_color || defaultConfig.secondary_action_color;
    }

    // Применение шрифтов
    if (formTitle) {
        formTitle.style.fontFamily = `${customFont}, ${baseFontStack}`;
        formTitle.style.fontSize = `${baseSize * 2}px`;
    }

    if (clientLabel) clientLabel.style.fontFamily = `${customFont}, ${baseFontStack}`;
    if (interpreterLabel) interpreterLabel.style.fontFamily = `${customFont}, ${baseFontStack}`;

    labels.forEach(label => {
        label.style.fontFamily = `${customFont}, ${baseFontStack}`;
        label.style.fontSize = `${baseSize}px`;
    });

    if (submitButton) {
        submitButton.style.fontFamily = `${customFont}, ${baseFontStack}`;
        submitButton.style.fontSize = `${baseSize * 1.125}px`;
    }

    if (googleRegisterBtn) {
        googleRegisterBtn.style.fontFamily = `${customFont}, ${baseFontStack}`;
        googleRegisterBtn.style.fontSize = `${baseSize}px`;
    }

    const googleButtonText = document.getElementById('google-button-text');
    if (googleButtonText) {
        googleButtonText.textContent = newConfig.google_button_text || defaultConfig.google_button_text;
    }
}

// Инициализация SDK
if (window.elementSdk) {
    window.elementSdk.init({
        defaultConfig,
        onConfigChange: async (newConfig) => {
            config = {...config, ...newConfig};
            await onConfigChange(config);
        },
        mapToCapabilities: (cfg) => ({
            recolorables: [
                {
                    get: () => cfg.background_color || defaultConfig.background_color,
                    set: (value) => {
                        cfg.background_color = value;
                        window.elementSdk.setConfig({background_color: value});
                    }
                },
                {
                    get: () => cfg.surface_color || defaultConfig.surface_color,
                    set: (value) => {
                        cfg.surface_color = value;
                        window.elementSdk.setConfig({surface_color: value});
                    }
                },
                {
                    get: () => cfg.text_color || defaultConfig.text_color,
                    set: (value) => {
                        cfg.text_color = value;
                        window.elementSdk.setConfig({text_color: value});
                    }
                },
                {
                    get: () => cfg.primary_action_color || defaultConfig.primary_action_color,
                    set: (value) => {
                        cfg.primary_action_color = value;
                        window.elementSdk.setConfig({primary_action_color: value});
                    }
                },
                {
                    get: () => cfg.secondary_action_color || defaultConfig.secondary_action_color,
                    set: (value) => {
                        cfg.secondary_action_color = value;
                        window.elementSdk.setConfig({secondary_action_color: value});
                    }
                }
            ],
            borderables: [],
            fontEditable: {
                get: () => cfg.font_family || defaultConfig.font_family,
                set: (value) => {
                    cfg.font_family = value;
                    window.elementSdk.setConfig({font_family: value});
                }
            },
            fontSizeable: {
                get: () => cfg.font_size || defaultConfig.font_size,
                set: (value) => {
                    cfg.font_size = value;
                    window.elementSdk.setConfig({font_size: value});
                }
            }
        }),
        mapToEditPanelValues: (cfg) => new Map([
            ["form_title", cfg.form_title || defaultConfig.form_title],
            ["client_label", cfg.client_label || defaultConfig.client_label],
            ["interpreter_label", cfg.interpreter_label || defaultConfig.interpreter_label],
            ["google_button_text", cfg.google_button_text || defaultConfig.google_button_text]
        ])
    });
}