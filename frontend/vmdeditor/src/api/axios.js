import Axios from 'axios';
import store from '@/store';
import {
  getCookie,
} from '@/assets/utils/util';
import router from '@/router/index';
import {
  ElMessageBox,
  ElMessage,
  ElNotification
} from 'element-plus'
const $message = (mes) => {
  return new Promise((resolve) => {
    ElMessageBox.alert(mes, '提示信息', {
      // if you want to disable its autofocus
      // autofocus: false,
      confirmButtonText: '确定',
      callback: (action) => {
        resolve(true)
      },
    })
  })
}


let isHideerrMessageMap = {}

let reqMap = new Map(); //存放正在发送的请求  后续取消 
let loadingMap = []; //存放正在loading的请求
let reqtimer = null;
let __axiosPromiseArr = [];
let hideloadtimer = null;
const axios = Axios.create({
  timeout: 1000 * 60 * 60, // 超时时间60s
  // baseURL: '',
  withCredentials: false, // 跨域请求时，允许其他域设置自身站点下的cookie
  cache: false,
});
axios.interceptors.request.use(
  (config) => {

    config.headers._csrf = getCookie('csrfToken');
    // console.log(store)
    let token = window.localStorage.getItem('token');
    if(token){
      config.headers.authorization = 'Bearer ' + token;
    }else{
      config.headers.authorization = '';
    }
    

    if (config.isHideerrMessage) {
      isHideerrMessageMap[config.url] = true;
    }

    if (config.isCancel) {
      let cindex = -1;
      __axiosPromiseArr.forEach((item, index) => {
        if (item.url === config.url) {
          cindex = index;
        }
      })
      if (cindex !== -1) {
        // 已经有请求  取消后续请求
        let cancelfn = null;
        config.cancelToken = new Axios.CancelToken(cancel => {
          cancelfn = cancel;
        })
        cancelfn();
        // 900000  代表重复请求
        throw new Error('900000');
      } else {
        // 第一次请求 存储
        __axiosPromiseArr.push({
          url: config.url
        })
      }

    }
    if (!config.isHideLoading) {
      setLoadingMap(config)
    }
    if (loadingMap.length > 0) {
      store.commit('loading', true);
      clearTimeout(reqtimer)
      reqtimer = setTimeout(() => {
        store.commit('loading', false);
      }, 1000 * 60 * 3)
    }

    if (reqMap.has(getKeyByConfig(config))) {
      if(config.isCancel){
        console.log('重复请求', getKeyByConfig(config))
        // 如果存在 取消请求
        const controller = new AbortController();
        config.signal = controller.signal;
        controller.abort();
      }
     
    } else {
      reqMap.set(getKeyByConfig(config), true);
    }


    return config;
  }, (error) => {
    return Promise.reject(error);
  },
);

axios.interceptors.response.use(
  async (response) => {
    let token = window.localStorage.getItem('token');
    if(response.headers['x-new-token'] && response.headers['x-new-token'] !== token){
      window.localStorage.setItem('token', response.headers['x-new-token']);
      store.commit('token', response.headers['x-new-token']);
    }
    
      // 延迟500ms  预留成功处理时间
      setTimeout(() => {
        __axiosPromiseArr.forEach((item, index) => {
          if (item.url === response.config.url) {
            __axiosPromiseArr.splice(index, 1);
          }
        });
      }, 500)
      setLoadingMap(response.config, 'delete')
      if (loadingMap.length < 1) {
        store.commit('loading', false)
      }
      if (reqMap.has(getKeyByConfig(response.config))) {
        // 返回后 取消
        reqMap.delete(getKeyByConfig(response.config))
      }
      if (!(response.data && response.data.Success)) {
        // 不成功 提示
        let ErrProcess = response.data.ErrProcess;
        let Err = response.data.Err || '服务器错误，请稍后再试'
        // ErrProcess = 1;
        if (ErrProcess === 1) {
          // 提示错误信息
          $message(Err);
        } else if (ErrProcess === 2) {
          // 登录过期
          // await $message('登录过期，请重新登录');
          store.commit('token', '');
        } else if (ErrProcess === 3) {
          await $message(Err);
          router.replace('/404')
        } else if (ErrProcess === 4) {
          // 强制刷新页面
          await $message(Err);
          window.location.reload();
        } else if (ErrProcess === 5) {
          // 去首页
          await $message(Err);
          router.replace('/')
        }
      }
      if(response.config.isfile){
        return response;
      }else{
        return response.data;
      }
      
    },
    (error) => {
      if (error.message === '900000') {
        // 重复请求
        __axiosPromiseArr = []
        return Promise.reject(error.message);
      }
      setTimeout(() => {
        __axiosPromiseArr.forEach((item, index) => {
          if (error.config && item.url === error.config.url) {
            __axiosPromiseArr.splice(index, 1);
          }
        });
      }, 500)
      setLoadingMap(error.config, 'delete')
      
      if (loadingMap.length < 1) {
        store.commit('loading', false)
      }
      if (error.message.indexOf('Network') !== -1) {
        store.commit('netError', true)
      }
      if (reqMap.has(getKeyByConfig(error.config))) {
        // 返回后 取消
        reqMap.delete(getKeyByConfig(error.config))
      }
      if(error.response.status === 401){
        // 登录过期
        let msg = '登录状态失效，请重新登录'
        if(error.response.data && error.response.data.detail){
          msg = error.response.data.detail;
        }
        ElMessage.closeAll();
        ElNotification.closeAll();
        window._this.$message(msg, 'error');
        store.commit('token', '');
        store.commit('routeData',{from:router.currentRoute.value});
        router.push('/login')
      }else if (error.response && error.response.data && error.response.data.detail && !isHideerrMessageMap[error.config.url]) {
        window._this.$message(error.response.data.detail, 'error');
      } else if (!(error.response && error.response.data) && error.response.status === 500) {
        let url = error.request?.responseURL;
        ElMessage.closeAll();
        ElNotification.closeAll();
        window._this.$message('请求出错，请刷新页面再试。错误信息：(500)  '+url, 'error');
      }else if(error.response.status === 502){
        let url = error.request?.responseURL;
        ElMessage.closeAll();
        ElNotification.closeAll();
        window._this.$message('请求出错，请刷新页面再试。错误信息：(502)  '+url, 'error');
      }
      return Promise.reject(error);
    }
);


function getKeyByConfig(config) {
  let {
    url,
    method,
    data,
    params
  } = config;
  return method + url;
}

function setLoadingMap(config, type) {
  let url = getKeyByConfig(config);
  const index = loadingMap.findIndex(item => item === url);
  if (type === 'delete') {
    if (index !== -1) {
      loadingMap.splice(index, 1);
    }
  } else {
    // 如果不是需要取消的请求 可以重复添加url
    if (!config.isCancel || index === -1) {
      loadingMap.push(url);
    }
  }
}

export default axios;