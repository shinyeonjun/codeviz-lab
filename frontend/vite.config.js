import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
// https://vitejs.dev/config/
export default defineConfig(function (_a) {
    var mode = _a.mode;
    var env = loadEnv(mode, __dirname, '');
    var backendTarget = env.VITE_BACKEND_TARGET || 'http://127.0.0.1:8000';
    return {
        plugins: [react()],
        resolve: {
            alias: {
                '@': path.resolve(__dirname, './src'),
            },
        },
        server: {
            proxy: {
                '/api': {
                    target: backendTarget,
                    changeOrigin: true,
                },
            },
        },
    };
});
