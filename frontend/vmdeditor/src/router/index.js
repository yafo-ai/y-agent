import { createRouter, createWebHistory } from 'vue-router'
import indexRouter from './routes';
import store from '@/store';
const routes = [{
  name: 'Error',
  path: '/:pathMatch(.*)*',
  component: () => import('@/views/404.vue'),
  meta: {
    title: '404',
    noLogin: true,
    hideNav: true,
  },
},{
  name: 'console',
  path: '/console',
  component: () => import('@/views/console.vue'),
  meta: {
    title: '调试模式',
    noLogin: true,
  },
},
{
  name: '/',
  path: '/',
  redirect: '/reportflow',
},
...indexRouter,
];
const baseUrl = import.meta.env.VITE_APP_PATH || '/';
const router = createRouter({
  // 4. 内部提供了 history 模式的实现。为了简单起见，我们在这里使用 hash 模式。
  history: createWebHistory(baseUrl),
  base: baseUrl,
  routes, // `routes: routes` 的缩写
})
router.beforeEach(async (to, from, next) => {
  // next();
  let token = window.localStorage.getItem('token');
  if (to.meta.noLogin) {

    // 如果不需要登录拦截 或者token存在
    next();
    /*eslint-disable*/
  } else if (token) {
    next();
  }else {
    
    store.commit('routeData',{to:to,from:from})
    next('/login');
  }
 
})

router.afterEach(async (to, from) => {
  if (to.path !== from.path) {
    document.title = to.meta.title || '加载中...';
  }
});


export default router;