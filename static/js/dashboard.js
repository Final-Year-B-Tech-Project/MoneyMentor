/**
 * MoneyMentor Dashboard JavaScript
 * Enhanced functionality for financial planning dashboard
 */

class MoneyMentorDashboard {
    constructor() {
        this.charts = {};
        this.notifications = [];
        this.theme = localStorage.getItem('moneymentor-theme') || 'light';
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupNotifications();
        this.setupThemeToggle();
        this.setupKeyboardShortcuts();
        this.setupLocalStorage();
    }

    setupEventListeners() {
        // Auto-save form data
        document.addEventListener('input', (e) => {
            if (e.target.matches('input[type="number"], select')) {
                this.debounce(() => this.saveFormData(), 1000)();
            }
        });

        // Chart resize handler
        window.addEventListener('resize', () => {
            this.debounce(() => this.resizeCharts(), 250)();
        });

        // Print functionality
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'p') {
                e.preventDefault();
                this.printDashboard();
            }
        });
    }

    setupNotifications() {
        // Create notification container
        if (!document.getElementById('notifications')) {
            const notificationContainer = document.createElement('div');
            notificationContainer.id = 'notifications';
            notificationContainer.className = 'fixed top-4 right-4 z-50 space-y-2';
            document.body.appendChild(notificationContainer);
        }
    }

    showNotification(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        const id = 'notification-' + Date.now();
        
        const bgColors = {
            success: 'bg-green-500',
            error: 'bg-red-500',
            warning: 'bg-yellow-500',
            info: 'bg-blue-500'
        };

        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-triangle',
            warning: 'fas fa-exclamation-circle',
            info: 'fas fa-info-circle'
        };

        notification.id = id;
        notification.className = `${bgColors[type]} text-white px-6 py-3 rounded-lg shadow-lg flex items-center space-x-3 transform translate-x-full transition-transform duration-300`;
        
        notification.innerHTML = `
            <i class="${icons[type]}"></i>
            <span>${message}</span>
            <button onclick="this.parentElement.remove()" class="ml-2 text-white hover:text-gray-200">
                <i class="fas fa-times"></i>
            </button>
        `;

        document.getElementById('notifications').appendChild(notification);

        // Animate in
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 100);

        // Auto remove
        setTimeout(() => {
            this.removeNotification(id);
        }, duration);
    }

    removeNotification(id) {
        const notification = document.getElementById(id);
        if (notification) {
            notification.classList.add('translate-x-full');
            setTimeout(() => notification.remove(), 300);
        }
    }

    setupThemeToggle() {
        // Add theme toggle button to navigation
        const nav = document.querySelector('nav .flex.items-center.space-x-6');
        if (nav) {
            const themeToggle = document.createElement('button');
            themeToggle.className = 'text-white hover:text-gray-200 transition';
            themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
            themeToggle.onclick = () => this.toggleTheme();
            nav.insertBefore(themeToggle, nav.firstChild);
        }
    }

    toggleTheme() {
        this.theme = this.theme === 'light' ? 'dark' : 'light';
        localStorage.setItem('moneymentor-theme', this.theme);
        this.applyTheme();
    }

    applyTheme() {
        if (this.theme === 'dark') {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl + G: Focus on goals section
            if (e.ctrlKey && e.key === 'g') {
                e.preventDefault();
                document.querySelector('#goalSection')?.scrollIntoView({ behavior: 'smooth' });
            }

            // Ctrl + C: Focus on chat
            if (e.ctrlKey && e.key === 'c') {
                e.preventDefault();
                document.querySelector('#chatMessages')?.scrollIntoView({ behavior: 'smooth' });
                document.querySelector('input[x-model="chatInput"]')?.focus();
            }

            // Esc: Clear all notifications
            if (e.key === 'Escape') {
                document.querySelectorAll('#notifications > div').forEach(notification => {
                    notification.remove();
                });
            }
        });
    }

    setupLocalStorage() {
        // Save dashboard state periodically
        setInterval(() => {
            this.saveFormData();
        }, 30000); // Every 30 seconds
    }

    saveFormData() {
        const formData = {
            income: document.querySelector('input[x-model="financialData.income"]')?.value || '',
            riskAppetite: document.querySelector('select[x-model="financialData.riskAppetite"]')?.value || 'moderate',
            timestamp: new Date().toISOString()
        };

        localStorage.setItem('moneymentor-form', JSON.stringify(formData));
    }

    loadFormData() {
        const saved = localStorage.getItem('moneymentor-form');
        if (saved) {
            try {
                const data = JSON.parse(saved);
                
                // Check if data is recent (within 24 hours)
                const savedTime = new Date(data.timestamp);
                const now = new Date();
                const hoursDiff = (now - savedTime) / (1000 * 60 * 60);

                if (hoursDiff < 24) {
                    const incomeInput = document.querySelector('input[x-model="financialData.income"]');
                    const riskSelect = document.querySelector('select[x-model="financialData.riskAppetite"]');

                    if (incomeInput && data.income) incomeInput.value = data.income;
                    if (riskSelect && data.riskAppetite) riskSelect.value = data.riskAppetite;

                    this.showNotification('Previous session data restored', 'info');
                }
            } catch (error) {
                console.error('Error loading saved data:', error);
            }
        }
    }

    resizeCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.resize === 'function') {
                chart.resize();
            }
        });
    }

    printDashboard() {
        const printContent = this.generatePrintContent();
        const printWindow = window.open('', '_blank');
        
        printWindow.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>MoneyMentor Financial Report</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .header { text-align: center; margin-bottom: 30px; border-bottom: 2px solid #333; padding-bottom: 10px; }
                    .section { margin-bottom: 25px; }
                    .section h3 { color: #333; border-left: 4px solid #3b82f6; padding-left: 10px; }
                    .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 15px 0; }
                    .metric-card { border: 1px solid #ddd; padding: 15px; border-radius: 5px; }
                    .metric-value { font-size: 24px; font-weight: bold; color: #3b82f6; }
                    .goal-item { border-left: 3px solid #10b981; padding-left: 15px; margin-bottom: 15px; }
                    @media print { body { margin: 0; } }
                </style>
            </head>
            <body>
                ${printContent}
            </body>
            </html>
        `);
        
        printWindow.document.close();
        printWindow.focus();
        setTimeout(() => {
            printWindow.print();
            printWindow.close();
        }, 250);
    }

    generatePrintContent() {
        const income = document.querySelector('input[x-model="financialData.income"]')?.value || '0';
        const risk = document.querySelector('select[x-model="financialData.riskAppetite"]')?.value || 'moderate';
        
        return `
            <div class="header">
                <h1>MoneyMentor Financial Report</h1>
                <p>Generated on ${new Date().toLocaleDateString()}</p>
            </div>

            <div class="section">
                <h3>Financial Profile</h3>
                <div class="metric-grid">
                    <div class="metric-card">
                        <div>Monthly Income</div>
                        <div class="metric-value">₹${parseInt(income).toLocaleString('en-IN')}</div>
                    </div>
                    <div class="metric-card">
                        <div>Risk Appetite</div>
                        <div class="metric-value">${risk.charAt(0).toUpperCase() + risk.slice(1)}</div>
                    </div>
                </div>
            </div>

            <div class="section">
                <h3>Budget Allocation (50/30/20 Rule)</h3>
                <div class="metric-grid">
                    <div class="metric-card">
                        <div>Needs (50%)</div>
                        <div class="metric-value">₹${(income * 0.5).toLocaleString('en-IN')}</div>
                    </div>
                    <div class="metric-card">
                        <div>Wants (30%)</div>
                        <div class="metric-value">₹${(income * 0.3).toLocaleString('en-IN')}</div>
                    </div>
                    <div class="metric-card">
                        <div>Savings (20%)</div>
                        <div class="metric-value">₹${(income * 0.2).toLocaleString('en-IN')}</div>
                    </div>
                </div>
            </div>

            <div class="section">
                <h3>Investment Recommendations</h3>
                <p><strong>Monthly SIP:</strong> ₹${(income * 0.2).toLocaleString('en-IN')}</p>
                <p><strong>Portfolio Allocation (${risk}):</strong></p>
                <ul>
                    <li>Equity: ${risk === 'aggressive' ? '70%' : risk === 'moderate' ? '50%' : '20%'}</li>
                    <li>Debt: ${risk === 'aggressive' ? '15%' : risk === 'moderate' ? '30%' : '60%'}</li>
                    <li>Gold: 10%</li>
                    <li>Liquid: ${risk === 'aggressive' ? '5%' : '10%'}</li>
                </ul>
            </div>

            <div class="section">
                <h3>Tax Planning</h3>
                <p><strong>80C Limit:</strong> ₹1,50,000 (ELSS, PPF, Insurance)</p>
                <p><strong>80D Limit:</strong> ₹25,000 (Health Insurance)</p>
                <p><strong>Potential Tax Savings:</strong> ₹35,000 - ₹52,500</p>
            </div>

            <div class="section">
                <h3>Emergency Fund</h3>
                <p><strong>Target Amount:</strong> ₹${(income * 6).toLocaleString('en-IN')} (6 months expenses)</p>
                <p><strong>Recommended:</strong> Keep in liquid funds or savings account</p>
            </div>
        `;
    }

    exportData() {
        const dashboardData = this.collectDashboardData();
        const dataStr = JSON.stringify(dashboardData, null, 2);
        const dataBlob = new Blob([dataStr], {type: 'application/json'});
        
        const link = document.createElement('a');
        link.href = URL.createObjectURL(dataBlob);
        link.download = `moneymentor-data-${new Date().toISOString().split('T')[0]}.json`;
        link.click();
        
        this.showNotification('Data exported successfully', 'success');
    }

    collectDashboardData() {
        return {
            exportDate: new Date().toISOString(),
            financialData: {
                income: document.querySelector('input[x-model="financialData.income"]')?.value || 0,
                riskAppetite: document.querySelector('select[x-model="financialData.riskAppetite"]')?.value || 'moderate'
            },
            userProfile: {
                username: '{{ user.username }}',
                userId: '{{ user.id }}'
            },
            preferences: {
                theme: this.theme,
                notifications: this.notifications
            }
        };
    }

    // Utility functions
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    formatCurrency(amount) {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(amount || 0);
    }

    formatPercentage(value) {
        return new Intl.NumberFormat('en-IN', {
            style: 'percent',
            minimumFractionDigits: 1,
            maximumFractionDigits: 1
        }).format(value / 100);
    }

    validateFinancialInput(input) {
        const value = parseFloat(input.value);
        const min = parseFloat(input.min) || 0;
        const max = parseFloat(input.max) || Infinity;

        if (isNaN(value) || value < min || value > max) {
            input.classList.add('border-red-500');
            return false;
        } else {
            input.classList.remove('border-red-500');
            input.classList.add('border-green-500');
            setTimeout(() => input.classList.remove('border-green-500'), 2000);
            return true;
        }
    }
}

// Enhanced Chart Utilities
class ChartManager {
    constructor() {
        this.defaultColors = {
            primary: '#3b82f6',
            success: '#10b981', 
            warning: '#f59e0b',
            danger: '#ef4444',
            info: '#6b7280',
            purple: '#8b5cf6'
        };
    }

    createResponsiveChart(ctx, config) {
        const baseConfig = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        font: { size: 12 },
                        padding: 15
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: 'white',
                    bodyColor: 'white',
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeOutQuart'
            }
        };

        // Merge configurations
        const mergedConfig = this.deepMerge(config, { options: baseConfig });
        return new Chart(ctx, mergedConfig);
    }

    deepMerge(target, source) {
        const output = Object.assign({}, target);
        if (this.isObject(target) && this.isObject(source)) {
            Object.keys(source).forEach(key => {
                if (this.isObject(source[key])) {
                    if (!(key in target))
                        Object.assign(output, { [key]: source[key] });
                    else
                        output[key] = this.deepMerge(target[key], source[key]);
                } else {
                    Object.assign(output, { [key]: source[key] });
                }
            });
        }
        return output;
    }

    isObject(item) {
        return item && typeof item === 'object' && !Array.isArray(item);
    }
}

// Goal Management Utilities
class GoalManager {
    constructor() {
        this.goals = JSON.parse(localStorage.getItem('moneymentor-goals')) || [];
    }

    addGoal(goalData) {
        const goal = {
            id: Date.now(),
            ...goalData,
            createdAt: new Date().toISOString(),
            progress: 0
        };

        this.goals.push(goal);
        this.saveGoals();
        return goal;
    }

    updateGoal(id, updates) {
        const index = this.goals.findIndex(goal => goal.id === id);
        if (index !== -1) {
            this.goals[index] = { ...this.goals[index], ...updates };
            this.saveGoals();
            return this.goals[index];
        }
        return null;
    }

    deleteGoal(id) {
        this.goals = this.goals.filter(goal => goal.id !== id);
        this.saveGoals();
    }

    saveGoals() {
        localStorage.setItem('moneymentor-goals', JSON.stringify(this.goals));
    }

    calculateSIP(targetAmount, years, annualReturn = 12) {
        const monthlyReturn = annualReturn / 12 / 100;
        const months = years * 12;
        
        if (monthlyReturn === 0) {
            return targetAmount / months;
        }
        
        return targetAmount * monthlyReturn / (Math.pow(1 + monthlyReturn, months) - 1);
    }

    getGoalProgress(goal) {
        const currentTime = new Date().getTime();
        const createdTime = new Date(goal.createdAt).getTime();
        const targetTime = createdTime + (goal.timeYears * 365 * 24 * 60 * 60 * 1000);
        
        return Math.min(100, ((currentTime - createdTime) / (targetTime - createdTime)) * 100);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard
    window.moneyMentorDashboard = new MoneyMentorDashboard();
    window.chartManager = new ChartManager();
    window.goalManager = new GoalManager();

    // Load saved form data
    setTimeout(() => {
        window.moneyMentorDashboard.loadFormData();
    }, 1000);

    // Add export data functionality to user menu
    const userMenu = document.querySelector('[x-show="showMenu"]');
    if (userMenu) {
        const exportButton = document.createElement('a');
        exportButton.href = '#';
        exportButton.className = 'block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100';
        exportButton.innerHTML = '<i class="fas fa-download mr-2"></i>Export Data';
        exportButton.onclick = (e) => {
            e.preventDefault();
            window.moneyMentorDashboard.exportData();
        };
        userMenu.insertBefore(exportButton, userMenu.querySelector('hr'));
    }

    // Welcome notification
    setTimeout(() => {
        window.moneyMentorDashboard.showNotification(
            'Welcome to MoneyMentor! Start by entering your monthly income.',
            'info',
            8000
        );
    }, 2000);
});

// Service Worker Registration (for offline capability)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/sw.js')
            .then(registration => {
                console.log('SW registered: ', registration);
            })
            .catch(registrationError => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}

// Export for use in other modules
window.MoneyMentorUtils = {
    dashboard: () => window.moneyMentorDashboard,
    charts: () => window.chartManager,
    goals: () => window.goalManager
};
