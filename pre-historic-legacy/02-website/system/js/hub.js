/**
 * SATOR eXe Hub JavaScript
 * ========================
 * Navigation and interaction logic for the SATOR eXe platform
 */

// SATOR Hub Namespace
const SATOR = {
    version: '2.0.1',
    currentProfile: null,
    
    // Initialize hub
    init() {
        this.loadProfileFromURL();
        this.initNavigation();
        this.initKeyboardShortcuts();
        console.log(`SATOR eXe v${this.version} initialized`);
    },

    // Profile Management
    profiles: {
        radiantx: {
            name: 'RadiantX',
            game: 'Valorant',
            accent: '#ff4655',
            path: 'radiantx/index.html'
        },
        counterx: {
            name: 'CounterX',
            game: 'CS2',
            accent: '#f0c040',
            path: 'counterx/index.html'
        },
        apexx: {
            name: 'ApexX',
            game: 'Apex Legends',
            accent: '#da292a',
            path: 'apexx/index.html'
        }
    },

    // Load profile based on URL
    loadProfileFromURL() {
        const path = window.location.pathname;
        if (path.includes('radiantx')) {
            this.currentProfile = 'radiantx';
        } else if (path.includes('counterx')) {
            this.currentProfile = 'counterx';
        } else if (path.includes('apexx')) {
            this.currentProfile = 'apexx';
        }
    },

    // Switch game profile
    switchProfile(profileId) {
        const profile = this.profiles[profileId];
        if (!profile) {
            console.error(`Profile ${profileId} not found`);
            return;
        }

        this.currentProfile = profileId;
        
        // Animate transition
        this.animateTransition(() => {
            window.location.href = '../' + profile.path;
        });
    },

    // Navigation helpers
    navigateTo(path) {
        this.animateTransition(() => {
            window.location.href = path;
        });
    },

    // Transition animation
    animateTransition(callback) {
        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: radial-gradient(ellipse at center, 
                transparent 0%, 
                rgba(0, 240, 255, 0.3) 30%, 
                #0a1628 70%
            );
            z-index: 9999;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;
        document.body.appendChild(overlay);

        // Trigger animation
        requestAnimationFrame(() => {
            overlay.style.opacity = '1';
            overlay.style.animation = 'warpZoom 0.5s ease-out forwards';
        });

        // Execute callback after animation
        setTimeout(() => {
            callback();
        }, 400);
    },

    // Initialize navigation
    initNavigation() {
        // Handle profile switcher if present
        const profileSelector = document.getElementById('profileSelector');
        if (profileSelector) {
            profileSelector.addEventListener('change', (e) => {
                this.switchProfile(e.target.value);
            });
        }

        // Handle back to hub links
        document.querySelectorAll('[data-nav="hub"]').forEach(el => {
            el.addEventListener('click', (e) => {
                e.preventDefault();
                this.navigateTo('../launchpad.html');
            });
        });

        // Handle back to landing
        document.querySelectorAll('[data-nav="landing"]').forEach(el => {
            el.addEventListener('click', (e) => {
                e.preventDefault();
                this.navigateTo('../landing.html');
            });
        });
    },

    // Keyboard shortcuts
    initKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Alt + H = Hub
            if (e.altKey && e.key === 'h') {
                e.preventDefault();
                this.navigateTo('launchpad.html');
            }
            // Alt + L = Landing
            if (e.altKey && e.key === 'l') {
                e.preventDefault();
                this.navigateTo('landing.html');
            }
            // Escape = Back
            if (e.key === 'Escape') {
                if (window.location.pathname.includes('index.html') && 
                    !window.location.pathname.includes('landing')) {
                    this.navigateTo('../launchpad.html');
                }
            }
        });
    },

    // Utility: Generate starfield
    generateStarfield(container, count = 100) {
        if (typeof container === 'string') {
            container = document.getElementById(container);
        }
        if (!container) return;

        for (let i = 0; i < count; i++) {
            const star = document.createElement('div');
            star.className = 'star';
            star.style.left = Math.random() * 100 + '%';
            star.style.top = Math.random() * 100 + '%';
            const size = Math.random() * 2 + 1;
            star.style.width = size + 'px';
            star.style.height = size + 'px';
            star.style.setProperty('--duration', (Math.random() * 3 + 2) + 's');
            star.style.setProperty('--delay', Math.random() * 5 + 's');
            star.style.setProperty('--opacity', Math.random() * 0.5 + 0.3);
            container.appendChild(star);
        }
    },

    // Utility: Animate number counter
    animateCounter(element, target, duration = 1000) {
        const start = 0;
        const startTime = performance.now();

        const update = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easeProgress = 1 - Math.pow(1 - progress, 3); // Ease out cubic
            const current = Math.floor(start + (target - start) * easeProgress);
            
            element.textContent = current.toLocaleString();

            if (progress < 1) {
                requestAnimationFrame(update);
            }
        };

        requestAnimationFrame(update);
    },

    // Utility: Create glass panel
    createGlassPanel(content, options = {}) {
        const panel = document.createElement('div');
        panel.className = 'glass-panel';
        panel.innerHTML = content;
        
        if (options.hoverable) {
            panel.classList.add('glass-panel-hover');
        }
        
        return panel;
    }
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    SATOR.init();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SATOR;
}
