import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
const resolve = (dir) => path.resolve(__dirname, '.', dir)

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue()
  ],
  define: {
    'process.env': {},
  },
  resolve: {
    // 配置路径别名
    alias: {
      '@': resolve('src'),
    },
  },
  server: {
    /** 设置 host: true 才可以使用 Network 的形式，以 IP 访问项目 */
    host: true, // host: "0.0.0.0"
    /** 端口号 */
    port: 5173,
    /** 是否自动打开浏览器 */
    open: false,
    /** 跨域设置允许 */
    cors: true,
    /** 端口被占用时，是否直接退出 */
    strictPort: false,
    /** 接口代理 */
    proxy: {
      // 选项写法
      '^/api': { 

        target: 'http://193.111.99.208/',//正式环境
        // target: 'http://192.168.50.71:8011/',//英杰的
        // target: 'http://192.168.50.109:8011/', //尹经理


        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api')
      },
    },

  },
  build: {
    /** 单个 chunk 文件的大小超过 2048KB 时发出警告 */
    chunkSizeWarningLimit: 2048,
    /** 禁用 gzip 压缩大小报告 */
    reportCompressedSize: false,

    /** 打包后静态资源目录 */
    assetsDir: "static",
    rollupOptions: {
      output: {
        manualChunks: {
          // 每个 '键' 都表示一个分包块，'值' 包含列出的模块及其所有依赖项
          vue: ['vue', 'vue-router', 'axios'],
          element: ['element-plus'],
          editor: ['@kangc/v-md-editor']
        },
      },
    },

  },
})
