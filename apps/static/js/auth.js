
class AuthManager {

constructor() {

this.currentRole = 'client';

this.currentMode = 'login';

this.init();

}



init() {

this.setupEventListeners();

this.updateFormVisibility();

}



setupEventListeners() {

// Переключение между Login и Register

document.querySelectorAll('.toggle-btn').forEach(btn => {

btn.addEventListener('click', (e) => {

this.switchMode(e.target.dataset.mode);

});

});



// Переключение Role (Client/Interpreter)

document.querySelectorAll('.role-btn').forEach(btn => {

btn.addEventListener('click', (e) => {

e.preventDefault();

this.switchRole(e.target.dataset.role);

});

});



// Отправка форм

document.getElementById('loginForm').addEventListener('submit', (e) => {

e.preventDefault();

this.handleLogin();

});



document.getElementById('registerForm').addEventListener('submit', (e) => {

e.preventDefault();

this.handleRegister();

});

}



switchMode(mode) {

this.currentMode = mode;



// Обновление активной кнопки

document.querySelectorAll('.toggle-btn').forEach(btn => {

btn.classList.toggle('active', btn.dataset.mode === mode);

});



// Показ/скрытие форм

document.querySelectorAll('.auth-form').forEach(form => {

form.classList.toggle('active', form.id === `${mode}Form`);

});

}



switchRole(role) {

this.currentRole = role;



// Обновление активной кнопки

document.querySelectorAll('.role-btn').forEach(btn => {

btn.classList.toggle('active', btn.dataset.role === role);

});



this.updateFormVisibility();

}



updateFormVisibility() {

const interpreterFields = document.querySelectorAll('.interpreter-only');



interpreterFields.forEach(field => {

if (this.currentRole === 'interpreter') {

field.classList.add('show');

// Делаем поля обязательными

const inputs = field.querySelectorAll('input, select');

inputs.forEach(input => {

input.required = true;

});

} else {

field.classList.remove('show');

// Убираем required для клиента

const inputs = field.querySelectorAll('input, select');

inputs.forEach(input => {

input.required = false;

});

}

});

}



validateEmail(email) {

const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

return regex.test(email);

}



validatePassword(password) {

return password.length >= 8;

}



validatePhone(phone) {

const regex = /^[+]?[(]?[0-9]{3}[)]?[-\s.]?[0-9]{3}[-\s.]?[0-9]{4,6}$/;

return regex.test(phone.replace(/\s/g, ''));

}



validateLogin() {

const email = document.getElementById('loginEmail').value.trim();

const password = document.getElementById('loginPassword').value;



if (!this.validateEmail(email)) {

this.showError('loginEmail', 'Invalid email address');

return false;

}



if (!password) {

this.showError('loginPassword', 'Password is required');

return false;

}



this.clearErrors();

return true;

}



validateRegister() {

const firstName = document.getElementById('firstName').value.trim();

const lastName = document.getElementById('lastName').value.trim();

const phone = document.getElementById('phone').value.trim();

const email = document.getElementById('email').value.trim();

const password = document.getElementById('password').value;

const confirmPassword = document.getElementById('confirmPassword').value;



this.clearErrors();



if (!firstName) {

this.showError('firstName', 'First name is required');

return false;

}



if (!lastName) {

this.showError('lastName', 'Last name is required');

return false;

}



if (!phone || !this.validatePhone(phone)) {

this.showError('phone', 'Invalid phone number');

return false;

}



if (!this.validateEmail(email)) {

this.showError('email', 'Invalid email address');

return false;

}



if (!this.validatePassword(password)) {

this.showError('password', 'Password must be at least 8 characters');

return false;

}



if (password !== confirmPassword) {

this.showError('confirmPassword', 'Passwords do not match');

return false;

}



// Валидация специфичных полей интерпретатора

if (this.currentRole === 'interpreter') {

const gender = document.getElementById('gender').value;

const languages = document.querySelectorAll('input[name="languages"]:checked');

const translationType = document.querySelectorAll('input[name="translation_type"]:checked');



if (!gender) {

this.showError('gender', 'Gender is required');

return false;

}



if (languages.length === 0) {

this.showError('languages', 'Select at least one language');

return false;

}



if (translationType.length === 0) {

this.showError('translationType', 'Select at least one translation type');

return false;

}

}



return true;

}



showError(fieldId, message) {

const field = document.getElementById(fieldId);

if (field) {

field.classList.add('error');

const errorMsg = field.parentElement.querySelector('.error-message');

if (errorMsg) {

errorMsg.textContent = message;

errorMsg.classList.add('show');

} else {

const error = document.createElement('div');

error.className = 'error-message show';

error.textContent = message;

field.parentElement.appendChild(error);

}

}

}



clearErrors() {

document.querySelectorAll('.error').forEach(field => {

field.classList.remove('error');

});

document.querySelectorAll('.error-message').forEach(msg => {

msg.classList.remove('show');

});

}



async handleLogin() {

if (!this.validateLogin()) return;



const formData = new FormData(document.getElementById('loginForm'));

const data = Object.fromEntries(formData);



try {

const response = await fetch('/api/login/', {

method: 'POST',

headers: {

'Content-Type': 'application/json',

'X-CSRFToken': this.getCSRFToken(),

},

body: JSON.stringify(data),

});



const result = await response.json();



if (response.ok) {

window.location.href = '/dashboard/';

} else {

alert(result.error || 'Login failed');

}

} catch (error) {

console.error('Login error:', error);

alert('An error occurred. Please try again.');

}

}



async handleRegister() {

if (!this.validateRegister()) return;



const formData = new FormData(document.getElementById('registerForm'));

const data = {

first_name: formData.get('first_name'),

last_name: formData.get('last_name'),

phone: formData.get('phone'),

email: formData.get('email'),

password: formData.get('password'),

user_type: this.currentRole,

};



// Добавляем специфичные поля интерпретатора

if (this.currentRole === 'interpreter') {

data.gender = formData.get('gender');

data.city = formData.get('city');

data.ready_for_trips = formData.get('ready_for_trips') === 'true';

data.languages = Array.from(document.querySelectorAll('input[name="languages"]:checked'))

.map(checkbox => checkbox.value);

data.translation_type = Array.from(document.querySelectorAll('input[name="translation_type"]:checked'))

.map(checkbox => checkbox.value);

}



try {

const response = await fetch('/api/register/', {

method: 'POST',

headers: {

'Content-Type': 'application/json',

'X-CSRFToken': this.getCSRFToken(),

},

body: JSON.stringify(data),

});



const result = await response.json();



if (response.ok) {

alert('Registration successful! Please log in.');

this.switchMode('login');

} else {

alert(result.error || 'Registration failed');

}

} catch (error) {

console.error('Registration error:', error);

alert('An error occurred. Please try again.');

}

}



handleGoogleLogin(response) {

this.handleGoogleAuth(response, 'login');

}



handleGoogleRegister(response) {

this.handleGoogleAuth(response, 'register');

}



async handleGoogleAuth(response, mode) {

try {

const result = await fetch('/api/google-auth/', {

method: 'POST',

headers: {

'Content-Type': 'application/json',

'X-CSRFToken': this.getCSRFToken(),

},

body: JSON.stringify({

token: response.credential,

mode: mode,

user_type: this.currentRole,

}),

});



const data = await result.json();



if (result.ok) {

if (mode === 'register' && this.currentRole === 'interpreter') {

// Перенаправляем на завершение профиля интерпретатора

window.location.href = '/profile/complete/';

} else {

window.location.href = '/dashboard/';

}

} else {

alert(data.error || 'Authentication failed');

}

} catch (error) {

console.error('Google auth error:', error);

alert('An error occurred. Please try again.');

}

}



getCSRFToken() {

return document.querySelector('[name=csrfmiddlewaretoken]')?.value ||

document.cookie.split('; ')

.find(row => row.startsWith('csrftoken='))

?.split('=')[1] ||

'';

}

}



// Инициализация

document.addEventListener('DOMContentLoaded', () => {

new AuthManager();

});



// Google callback функции

function handleGoogleLogin(response) {

window.authManager?.handleGoogleLogin(response);

}



function handleGoogleRegister(response) {

window.authManager?.handleGoogleRegister(response);

}



// Сохраняем экземпляр в window для доступа из HTML

window.authManager = new AuthManager();
