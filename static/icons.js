// Professional SVG Icons for UMUHUZA Platform
// All icons are designed to match the system's green (#4CAF50) color scheme

const Icons = {
    // User Role Icons
    farmer: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 2C13.1 2 14 2.9 14 4C14 5.1 13.1 6 12 6C10.9 6 10 5.1 10 4C10 2.9 10.9 2 12 2ZM21 9V7L15 1H5C3.89 1 3 1.89 3 3V21C3 22.11 3.89 23 5 23H11V21H5V3H13V9H21ZM14 10V12H16V10H14ZM18 10V12H20V10H18ZM14 14V16H16V14H14ZM18 14V16H20V14H18ZM14 18V20H16V18H14ZM18 18V20H20V18H18Z" fill="currentColor"/>
    </svg>`,
    
    dealer: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M19 3H5C3.9 3 3 3.9 3 5V19C3 20.1 3.9 21 5 21H19C20.1 21 21 20.1 21 19V5C21 3.9 20.1 3 19 3ZM19 19H5V5H19V19ZM7 10H9V17H7V10ZM11 7H13V17H11V7ZM15 13H17V17H15V13Z" fill="currentColor"/>
    </svg>`,
    
    processor: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 2L2 7L12 12L22 7L12 2ZM2 17L12 22L22 17V12L12 17L2 12V17ZM2 12V17L12 22L22 17V12L12 7L2 12Z" fill="currentColor"/>
    </svg>`,
    
    researcher: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM13 17H11V15H13V17ZM13 13H11V7H13V13Z" fill="currentColor"/>
        <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.5" fill="none"/>
    </svg>`,
    
    policy: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 1L3 5V11C3 16.55 6.84 21.74 12 23C17.16 21.74 21 16.55 21 11V5L12 1ZM12 7C13.4 7 14.8 8.6 14.8 10V11.5C15.4 11.5 16 12.1 16 12.7V16.2C16 16.8 15.4 17.3 14.8 17.3H9.2C8.6 17.3 8 16.7 8 16.1V12.6C8 12 8.6 11.5 9.2 11.5V10C9.2 8.6 10.6 7 12 7ZM12 8.2C11.2 8.2 10.5 8.7 10.5 9.5V11.5H13.5V9.5C13.5 8.7 12.8 8.2 12 8.2Z" fill="currentColor"/>
    </svg>`,
    
    // Feature Icons
    lock: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M18 8H17V6C17 3.24 14.76 1 12 1C9.24 1 7 3.24 7 6V8H6C4.9 8 4 8.9 4 10V20C4 21.1 4.9 22 6 22H18C19.1 22 20 21.1 20 20V10C20 8.9 19.1 8 18 8ZM12 3C13.66 3 15 4.34 15 6V8H9V6C9 4.34 10.34 3 12 3ZM18 20H6V10H18V20Z" fill="currentColor"/>
        <path d="M12 17C13.1 17 14 16.1 14 15C14 13.9 13.1 13 12 13C10.9 13 10 13.9 10 15C10 16.1 10.9 17 12 17Z" fill="currentColor"/>
    </svg>`,
    
    weather: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M6.76 4.84L4.96 3.05L3.54 4.46L5.34 6.25C4.53 7.25 4 8.55 4 10C4 13.31 6.69 16 10 16C13.31 16 16 13.31 16 10C16 6.69 13.31 4 10 4C8.55 4 7.25 4.53 6.25 5.34L4.46 3.54L3.05 4.96L4.84 6.76C4.03 7.76 3.5 9.06 3.5 10.5C3.5 14.09 6.41 17 10 17C13.59 17 16.5 14.09 16.5 10.5C16.5 6.91 13.59 4 10 4H10.5C10.5 4 10 4 10 4Z" fill="currentColor"/>
        <path d="M12 8V12L15 15L13.5 16.5L10 13V8H12Z" fill="currentColor"/>
    </svg>`,
    
    market: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M7 18C5.9 18 5.01 18.9 5.01 20C5.01 21.1 5.9 22 7 22C8.1 22 9 21.1 9 20C9 18.9 8.1 18 7 18ZM1 2V4H3L6.6 11.59L5.25 14.04C5.09 14.32 5 14.65 5 15C5 16.1 5.9 17 7 17H19V15H7.42C7.28 15 7.17 14.89 7.17 14.75L7.2 14.66L8.1 13H15.55C16.3 13 16.96 12.59 17.3 11.97L20.88 6H22.54L20.68 4H6.27L5.21 2H1ZM17 18C15.9 18 15.01 18.9 15.01 20C15.01 21.1 15.9 22 17 22C18.1 22 19 21.1 19 20C19 18.9 18.1 18 17 18Z" fill="currentColor"/>
    </svg>`,
    
    inventory: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M20 6H16L14 4H10L8 6H4C2.9 6 2 6.9 2 8V19C2 20.1 2.9 21 4 21H20C21.1 21 22 20.1 22 19V8C22 6.9 21.1 6 20 6ZM20 19H4V8H6.83L8.83 6H15.17L17.17 8H20V19ZM12 9C9.24 9 7 11.24 7 14C7 16.76 9.24 19 12 19C14.76 19 17 16.76 17 14C17 11.24 14.76 9 12 9ZM12 17C10.35 17 9 15.65 9 14C9 12.35 10.35 11 12 11C13.65 11 15 12.35 15 14C15 15.65 13.65 17 12 17Z" fill="currentColor"/>
    </svg>`,
    
    orders: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M14 2H6C4.9 2 4 2.9 4 4V20C4 21.1 4.89 22 5.99 22H18C19.1 22 20 21.1 20 20V8L14 2ZM18 20H6V4H13V9H18V20ZM8 15.01L9.41 16.42L11 14.84V18H13V14.84L14.59 16.43L16 15.01L12.01 11L8 15.01Z" fill="currentColor"/>
    </svg>`,
    
    crops: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M17.5 12C15.01 12 13 14.01 13 16.5C13 18.99 15.01 21 17.5 21C19.99 21 22 18.99 22 16.5C22 14.01 19.99 12 17.5 12ZM17.5 19C16.12 19 15 17.88 15 16.5C15 15.12 16.12 14 17.5 14C18.88 14 20 15.12 20 16.5C20 17.88 18.88 19 17.5 19ZM12.5 2C10.01 2 8 4.01 8 6.5C8 8.99 10.01 11 12.5 11C14.99 11 17 8.99 17 6.5C17 4.01 14.99 2 12.5 2ZM12.5 9C11.12 9 10 7.88 10 6.5C10 5.12 11.12 4 12.5 4C13.88 4 15 5.12 15 6.5C15 7.88 13.88 9 12.5 9ZM5 11C2.79 11 1 12.79 1 15C1 17.21 2.79 19 5 19C7.21 19 9 17.21 9 15C9 12.79 7.21 11 5 11ZM5 17C3.9 17 3 16.1 3 15C3 13.9 3.9 13 5 13C6.1 13 7 13.9 7 15C7 16.1 6.1 17 5 17Z" fill="currentColor"/>
    </svg>`,
    
    tips: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM13 17H11V15H13V17ZM13 13H11V7H13V13Z" fill="currentColor"/>
    </svg>`,
    
    reports: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M19 3H5C3.9 3 3 3.9 3 5V19C3 20.1 3.9 21 5 21H19C20.1 21 21 20.1 21 19V5C21 3.9 20.1 3 19 3ZM19 19H5V5H19V19ZM17 12H7V10H17V12ZM15 16H7V14H15V16ZM17 8H7V6H17V8Z" fill="currentColor"/>
    </svg>`,
    
    alerts: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M1 21H23L12 2L1 21ZM13 18H11V16H13V18ZM13 14H11V10H13V14Z" fill="currentColor"/>
    </svg>`,
    
    chart: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M3.5 18.49L9.5 12.49L13.5 16.49L22 6.92V20.5C22 21.05 21.55 21.5 21 21.5H3C2.45 21.5 2 21.05 2 20.5V18.49L3.5 18.49ZM21 4.5H3C2.45 4.5 2 4.95 2 5.5V7.51L3.5 7.51L9.5 13.51L13.5 9.51L21 1.92V4.5Z" fill="currentColor"/>
    </svg>`,
    
    research: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M15.5 14H14.71L14.43 13.73C15.41 12.59 16 11.11 16 9.5C16 5.91 13.09 3 9.5 3C5.91 3 3 5.91 3 9.5C3 13.09 5.91 16 9.5 16C11.11 16 12.59 15.41 13.73 14.43L14 14.71V15.5L19 20.49L20.49 19L15.5 14ZM9.5 14C7.01 14 5 11.99 5 9.5C5 7.01 7.01 5 9.5 5C11.99 5 14 7.01 14 9.5C14 11.99 11.99 14 9.5 14Z" fill="currentColor"/>
    </svg>`
};

// Helper function to render icon
function renderIcon(iconName, className = 'icon', size = 24) {
    const icon = Icons[iconName];
    if (!icon) return '';
    return `<span class="${className}" style="display: inline-flex; align-items: center; width: ${size}px; height: ${size}px; color: #4CAF50;">${icon}</span>`;
}

// Export for use in templates
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { Icons, renderIcon };
}

