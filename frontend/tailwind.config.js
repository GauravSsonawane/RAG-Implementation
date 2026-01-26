/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                'bg-main': '#1f1f1f',      // Perplexity-like soft dark grey
                'bg-sidebar': '#131313',   // Slightly darker sidebar
                'bg-surface': '#2d2d2d',   // Lighter surface for cards
                'bg-surface-hover': '#383838',

                'border-subtle': '#333333',
                'border-active': '#454545',

                'text-primary': '#e8e8e6', // Off-white, easier on eyes than #fafafa
                'text-secondary': '#a0a09c', // Warm grey
                'text-tertiary': '#737373',

                'accent': '#10a37f',       // Perplexity/ChatGPT Teal-ish/Green hint (or we can go Perplexity Blue #24b47e ?? Perplexity is more teal) - let's stick to a clean subtle teal/blue.
                'accent-hover': '#1a7f64',
            },
            fontFamily: {
                sans: ['"Inter"', 'sans-serif'],
                serif: ['"Merriweather"', 'serif'], // For headings to give that "knowledge" feel
            }
        }
    }
},
plugins: [],
}
