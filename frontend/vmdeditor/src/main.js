import App from './App.vue'
import {
  createApp
} from 'vue'
import '@/assets/css/style.css'

/* import the necessary styles for Vue Flow to work */
import "@vue-flow/core/dist/style.css";

/* import the default theme, this is optional but generally recommended */
import "@vue-flow/core/dist/theme-default.css";

import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import router from '@/router/index'
import store from '@/store/index'

import JsonViewer from "vue3-json-viewer";
import "vue3-json-viewer/dist/index.css"; // 引入样式

import VMdEditor from '@kangc/v-md-editor';
import '@kangc/v-md-editor/lib/style/base-editor.css';
import githubTheme from '@kangc/v-md-editor/lib/theme/github.js';
import '@kangc/v-md-editor/lib/theme/style/github.css';
import {
  ElNotification,
  ElMessageBox,
  ElMessage 
} from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

import VMdPreview from '@kangc/v-md-editor/lib/preview';
import '@kangc/v-md-editor/lib/style/preview.css';



// highlightjs
import hljs from 'highlight.js';

VMdEditor.use(githubTheme, {
  Hljs: hljs,
});

VMdPreview.use(githubTheme, {
  Hljs: hljs,
});

import '@/assets/css/common.css'

import {initTableHeight} from '@/assets/utils/util'




let app = createApp(App)
app.use(ElementPlus, {
  locale: zhCn,
})
// import VueDiff from "vue-diff";
// import "vue-diff/dist/index.css";

// app.use(VueDiff)
app.use(router)

app.use(store)
app.use(VMdEditor);
app.use(VMdPreview);
app.use(JsonViewer);


app.config.globalProperties.$toast = (msg,type) => {
  ElMessage({
    message: msg,
    type: type || 'success',
  })
};

app.config.globalProperties.$message = (msg, type, title) => {
  ElNotification({
    title: title || '提示信息',
    type: type || 'success',
    position: 'bottom-right',
    duration: 3000,
    message: msg,
    offset: 120,
  })
};

app.config.globalProperties.$confirm = (msg, title, opt) => {
  return ElMessageBox.confirm(msg, title || "删除提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning",
    ...opt,
  })
};





 
function fallbackCopyTextToClipboard(text,fn) {
  // 创建一个文本框元素并设置其值为要复制的文本
  var textArea = document.createElement("textarea");
  textArea.value = text;
  
  // 将文本框置于页面外，使其不可见
  textArea.style.position = "fixed";
  textArea.style.top = "0";
  textArea.style.left = "0";
  textArea.style.width = "2em";
  textArea.style.height = "2em";
  textArea.style.padding = "0";
  textArea.style.border = "none";
  textArea.style.outline = "none";
  textArea.style.boxShadow = "none";
  textArea.style.background = "transparent";
  
  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();

  
 
  try {
    var successful = document.execCommand('copy');
    if(fn){
      fn()
    }else if(successful){
      _this.$message('复制成功', 'success');
    }
    var msg = successful ? '成功' : '失败';
    console.log('文本 ' + msg + ' 复制到剪贴板');
  } catch (err) {
    console.error('无法复制文本', err);
  }
 
  document.body.removeChild(textArea);
}

function copyToClipboard(text,fn) {
   // 创建一个临时的输入框来存储文本
   if (navigator.clipboard && window.isSecureContext) {
    // 使用Clipboard API复制文本
    navigator.clipboard.writeText(text).then(function() {
      if(fn){
        fn()
      }else{
        _this.$message('复制成功', 'success');
      }
    }, function(err) {
      console.error('无法复制文本: ', err);
    });
  } else {
    // 对于不支持Clipboard API的浏览器，使用后备方法
    fallbackCopyTextToClipboard(text,fn);
  }
   
}

app.config.globalProperties.$copy = (text,fn) => {
  copyToClipboard(text,fn)
}


app.directive('initTableHeight', (el, binding) => {
  // 这会在 `mounted` 和 `updated` 时都调用
  el.classList.add("c-js-initTableHeight");
  let borderheight = 0;
  if(binding.value && binding.value.height !== undefined){
    borderheight = binding.value.height;
  }
 
  initTableHeight(el,borderheight)
})




const vFocus = {
  mounted: (el) => el.focus()
}
app.directive('focus', vFocus)

const vCopy = {
  mounted: (el,binding) => {
    el.copyval = binding.value;
    el.addEventListener('click', () => {
      if(el.copyval === undefined || el.copyval === null){
        return false;
      }
      if(typeof(el.copyval) === "string" ){
        copyToClipboard(el.copyval);
      }else{
        copyToClipboard(JSON.stringify(el.copyval, null, 2));
      }
      
    });
  },
  updated:(el, binding, vnode, oldVnode)=> {
    if(el.copyval !== binding.value){
      el.copyval = binding.value;
    }
  }
}

const vSearchOpen = {
  mounted: (el,binding) => {
    let borderheight = 0;
    if(binding.value && binding.value.tableHeight !== undefined){
      borderheight = binding.value.tableHeight;
    }
    
    let formbox = el.parentNode.parentNode;
    let formnode = formbox.querySelector('.el-form');

    // 如果高度超出
    if( formnode.offsetHeight > el.parentNode.offsetHeight + 19){
      // 如果查询条件高度溢出 则显示展开按钮
      el.title="展开查询条件"
      el.setAttribute('maxh',formnode.offsetHeight)
      el.setAttribute('minh',el.parentNode.offsetHeight)
      el.style.display = "inline-block";
      el.classList.remove("open")
      formbox.style.overflow = "hidden";
      formbox.style.height = el.parentNode.offsetHeight + "px";
    }else{
      // 隐藏展开按钮
      el.style.display = "none";
      return false;
    }
    el.addEventListener('click', () => {
      if(el.classList.contains("open")){
        // 展开状态  收起 
        el.title="展开查询条件"
        formbox.style.height = el.parentNode.offsetHeight + "px";
      }else{
        el.title="收起查询条件"
        formbox.style.height = el.getAttribute('maxh') + "px";
      }
      el.classList.toggle("open");
      // 每次切算后 重新计算高度
      // initTableHeight(null,borderheight);
    });
  },
  unmounted: (el) => {
  }
}

app.directive('copy', vCopy)
app.directive('searchOpen', vSearchOpen)
app.mount('#app')

window._this = app.config.globalProperties;



// 在你的主脚本文件中，比如 main.js 或 app.js
import JsonWorker from 'monaco-editor/esm/vs/language/json/json.worker?worker';
import CssWorker from 'monaco-editor/esm/vs/language/css/css.worker?worker';
import HtmlWorker from 'monaco-editor/esm/vs/language/html/html.worker?worker';
import TsWorker from 'monaco-editor/esm/vs/language/typescript/ts.worker?worker';
import EditorWorker from 'monaco-editor/esm/vs/editor/editor.worker?worker';
import { update } from 'lodash';
window.MonacoEnvironment = {
  getWorker: function (workerId, label) {
      switch (label) {
          case 'json':
              return new JsonWorker();
          case 'css':
          case 'scss':
          case 'less':
              return new CssWorker();
          case 'html':
          case 'handlebars':
          case 'razor':
              return new HtmlWorker();
          case 'typescript':
          case 'javascript':
              return new TsWorker();
          default:
              return new EditorWorker();
      }
  }
};


