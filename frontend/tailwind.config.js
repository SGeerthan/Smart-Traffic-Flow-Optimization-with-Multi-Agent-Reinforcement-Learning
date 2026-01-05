/** @type {import('tailwindcss').Config} */
export default {
    darkMode: 'class',
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                neon: {
                    blue: '#00f3ff',  // Cyan/Electric Blue
                    red: '#ff003c',   // Neon Red
                    green: '#0aff00', // Neon Green
                    purple: '#bc13fe',// Neon Purple
                },
                dark: {
                    base: '#050505',   // Matte Black
                    surface: '#0a0a0a', // Slightly lighter
                    highlight: '#121212',
                }
            },
            boxShadow: {
                'neon-blue': '0 0 10px #00f3ff, 0 0 20px #00f3ff44',
                'neon-red': '0 0 10px #ff003c, 0 0 20px #ff003c44',
            }
        },
    },
    plugins: [],
}
