import COMMON_ENV from '@/config/env';
import store from '@/store/index'


function findPathByLeafId(leafId, nodes, path = []) {
  for (let i = 0; i < nodes.length; i++) {
    const currentNode = nodes[i];
    const newPath = [...path, currentNode];

    if (currentNode.id === leafId) {
      return newPath;
    }

    if (currentNode.children && currentNode.children.length > 0) {
      const findResult = findPathByLeafId(leafId, currentNode.children, newPath);
      if (findResult) {
        return findResult;
      }
    }
  }

  return null;
}

function setCookie(name, value, day = 30) {
  // 写cookies
  if (!value) {
    return null;
  }
  try {
    const exp = new Date();
    const val = typeof value === 'string' ? value : JSON.stringify(value);
    const expires = day ? `;expires=${exp.setTime(exp.getTime() + day * 24 * 60 * 60 * 1000).toGMTString()}` : '';
    document.cookie = `${escape(name)}=${escape(val)}${expires};`;
  } catch (e) {
    console.error('Failed to set cookie:', e);
    return null;
  }
  return true;
}

function getCookie(name) {
  // 读cookie
  const reg = new RegExp(`(^| )${name}=([^;]*)(;|$)`);
  const arr = document.cookie.match(reg);
  if (arr) {
    return unescape(arr[2]);
  }
  return null;
}

function delCookie(name) {
  // 删除cookie
  const exp = new Date();
  exp.setTime(exp.getTime() - 1);
  const cval = getCookie(name);
  if (cval != null) {
    document.cookie = `${name}=${cval};expires=${exp.toGMTString()}`;
  }
}

// 获取url中的参数
function getUrlParam(name, url) {
  let href = url || window.location.href;
  const reg = new RegExp(`(^|&)${name}=([^&]*)(&|$)`);
  const query = href.split('?')[1] || '';
  const r = query.match(reg);
  if (r != null) {
    return decodeURI(r[2]);
  }
  return null;
}

// 将url中code=xxx 替换成空字符串
function replaceCode(fullPath) {
  // 获取当前页面的完整URL
  const currentUrl = window.location.href;
  // 提取URL中的协议、主机名和端口号部分
  const host = currentUrl.split('#')[0];

  // 如果提供了fullPath参数，则使用它；否则，使用当前页面的hash值（去除'#'）
  const hashUrl = fullPath || window.location.hash.replace('#', '');

  // 将hashUrl分割为路径和查询参数两部分
  const [path, queryString] = hashUrl.split('?');
  // 对路径进行URL编码
  const encodedPath = encodeURIComponent(path.substring(1));

  // 构建新的URL，将原路径替换为COMMON_ENV.COMMON_REPLACE_URL，并添加查询参数（如果有的话）
  const newUrl = `${host}?${COMMON_ENV.COMMON_REPLACE_URL}=${encodedPath}${queryString || ''}`;

  // 使用正则表达式替换URL中的'code=xxx'部分
  const replacedUrl = newUrl.replace(/code\=\w*(&|$)/, '');

  // 如果URL的最后一个字符是'?'或'&'，则去除它
  const finalUrl = replacedUrl.endsWith('?') || replacedUrl.endsWith('&') ?
    replacedUrl.slice(0, -1) :
    replacedUrl;

  return finalUrl;
}

function getTokenFn() {
  return getCookie(COMMON_ENV.COMMON_TOKEN);
  // return window.sessionStorage.getItem(COMMON_TOKEN);
}

function setTokenFn(token) {
  if (token) {
    setCookie(COMMON_ENV.COMMON_TOKEN, token, COMMON_ENV.COMMON_TOKEN_DAY);
  } else {
    delCookie(COMMON_ENV.COMMON_TOKEN);
    // 清除本地缓存信息
    window.sessionStorage.removeItem('commonUserData');
  }
}

function getScrollTop() {
  // 获取当前滚动条高度
  return document.documentElement.scrollTop || document.body.scrollTop;
}

function setScrollTop(top) {
  // 设置当前滚动条高度
  if (document.documentElement) {
    document.documentElement.scrollTop = top;
    document.body.scrollTop = top;
  } else {
    document.body.scrollTop = top;
  }
}

function getImgBySize(src, size) {
  // 获取缩略图
  if (!src || src.indexOf('files.haocai.com.cn/files/product/') === -1) {
    // 如果不是files.haocai.com.cn 这个域名下的  返回原路径
    return src;
  }
  let cursize = size || '_200x200';
  let index = src.lastIndexOf('/') + 1;
  let path = src.substr(0, index);
  let name = src.substr(index, src.length);
  let nindex = name.lastIndexOf('.');
  let rename = path + name.substr(0, nindex) + cursize + name.substr(nindex, name.length);
  return rename;
}

function getSystem() {
  // 获取系统环境
  /*eslint-disable*/
  let sys = {
    wx: false,
    android: false,
    ios: false,
  };
  let ua = window.navigator.userAgent;
  let wxua = window.navigator.userAgent.toLowerCase();
  if (wxua.match(/MicroMessenger/i) == 'micromessenger') {
    sys.wx = true;
  } else {
    sys.wx = false;
  }
  sys.android = ua.indexOf('Android') > -1 || ua.indexOf('Linux') > -1;
  sys.ios = !!ua.match(/\(i[^;]+;( U;)? CPU.+Mac OS X/);
  /* eslint-enable */
  return sys;
}

function transferString(content) {
  // 替换回车

  let string = content;
  if (!string) return null;
  // let ele = document.createElement('span');
  // ele.appendChild(document.createTextNode(string));
  // string = ele.innerHTML;
  try {
    string = string.replace(/\r\n/g, '<br>');
    string = string.replace(/\n/g, '<br>');
  } catch (e) {
    console.log(e);
  }
  return string;
}

function IsPC() {
  // 判断是否是pc端
  let userAgentInfo = navigator.userAgent;
  let Agents = ['Android', 'iPhone', 'SymbianOS', 'Windows Phone', 'iPad', 'iPod'];
  let flag = true;
  for (let v = 0; v < Agents.length; v++) {
    if (userAgentInfo.indexOf(Agents[v]) > 0) {
      flag = false;
      break;
    }
  }
  return flag;
}
// if (/(iPhone|iPad|iPod|iOS)/i.test(navigator.userAgent)) {
//  //alert(navigator.userAgent);
//  window.location.href ="iPhone.html";
// } else if (/(Android)/i.test(navigator.userAgent)) {
//  //alert(navigator.userAgent);
//  window.location.href ="Android.html";
// } else {
//  window.location.href ="pc.html";
// };
function removeHtmlStyle(html) {
  // 移除html里的style
  let rel = /style\s*?=\s*?([‘"])[\s\S]*?\1/;
  let newHtml = '';
  if (html) {
    newHtml = html.replace(rel, '');
  }
  return newHtml;
}

function payBrowser() {
  // 获取当前浏览器环境
  let t = '';
  let ua = window.navigator.userAgent;
  if (/MicroMessenger/.test(ua)) {
    /*eslint-disable*/
    let isWxWork = ua.match(/WxWork/i) == 'wxwork';
    /* eslint-enable */
    if (isWxWork) {
      // 企业微信
      t = 'wechart-qy';
    } else {
      // 微信
      t = 'wechart';
    }
  } else if (/AlipayClient/.test(ua)) {
    t = 'alipay';
  } else if (ua.indexOf('DingTalk') > -1) {
    // 钉钉
    t = 'dingtalk';
  }
  return t;
}

function replaceCodeToken() {
  let querylist = window.location.search.substring(1, window.location.search.length).split('&');
  let arr = [];
  querylist.forEach((item) => {
    // 过滤token code corpId
    if (item.indexOf('token') === -1 && item.indexOf('code') === -1 && item.indexOf('corpId') === -1) {
      arr.push(item);
    }
  });
  let url = arr.join('&');
  if (url) {
    url = `?${url}`;
  }
  return url;
}
// 替换所有的回车换行

/*eslint-disable*/
function findPathById(leafId, nodes, path, keyMap) {
  if (path === undefined) {
    path = [];
  }
  if (!keyMap) {
    keyMap = {
      childkey: 'list',
      idkey: 'Id',
    };
  }
  for (let i = 0; i < nodes.length; i++) {
    let tmpPath = path.concat();
    tmpPath.push(nodes[i]);

    if (leafId == nodes[i][keyMap.idkey]) {
      return tmpPath;
    }

    if (nodes[i][keyMap.childkey] && nodes[i][keyMap.childkey].length > 0) {
      let findResult = findPathById(leafId, nodes[i][keyMap.childkey], tmpPath, keyMap);
      if (findResult) {
        return findResult;
      }
    }
  }


}

function copyText(text, callback) { // text: 要复制的内容， callback: 回调
  let tag = document.createElement('input');
  tag.setAttribute('id', 'cp_hgz_input');
  tag.value = text;
  document.getElementsByTagName('body')[0].appendChild(tag);
  document.getElementById('cp_hgz_input').select();
  document.execCommand('copy');
  document.getElementById('cp_hgz_input').remove();
  callback && callback();
}

function scrollToTop(domClass) {
  /* eslint-disable */
  if (domClass && document.querySelector(domClass)) {
    document.querySelector(domClass).scrollIntoView({
      behavior: 'smooth', // 默认 auto
      block: 'start', // 默认 center
      inline: 'nearest', // 默认 neares
    });
    return;
  }
  if (!document.querySelector('#c-top-header')) return;
  setTimeout(() => {


    document.querySelector('#c-top-header').scrollIntoView({
      behavior: 'smooth', // 默认 auto
      block: 'start', // 默认 center
      inline: 'nearest', // 默认 neares
    });
  }, 100)
  // document.body.scrollTop = document.documentElement.scrollTop = 0;
  /* eslint-enable */
}

function withInstall(component, alias) {
  component.install = function (app) {
    app.component(component.name, component)
    if (alias) {
      app.config.globalProperties[alias] = component
    }
  }
  return component;
}

function copyData(data, target,undefinedKeys) {
  for (let key in target) {
    if (target[key] && (data[key] !== undefined || (undefinedKeys && undefinedKeys.indexOf(key) > -1))) {
      if(typeof target[key] === typeof data[key]) {
        // 如果类型相同  直接赋值  如果类型不同 默认把字符串转成数字
        data[key] = target[key];
      }else if (typeof data[key] === 'boolean'){
        // boolean类型 直接赋值
        data[key] = target[key] === "false" ? false : !!target[key];
      }else if (isNaN(parseInt(target[key]))) {
        data[key] = target[key];
      } else {
        data[key] = parseInt(target[key]);
      }
    }
  }
}

function renameChildrenKey(tree, newKey = 'object_fields', oldKey = 'children') {
  if (Array.isArray(tree)) {
    return tree.map(node => renameChildrenKey(node, newKey, oldKey));
  }

  if (tree && typeof tree === 'object') {
    const newTree = {
      ...tree
    };
    if (newTree[oldKey]) {
      newTree[newKey] = newTree[oldKey];
      // delete newTree[oldKey];
    }

    return Object.keys(newTree).reduce((acc, key) => {
      acc[key] = renameChildrenKey(newTree[key], newKey, oldKey);
      return acc;
    }, {});
  }

  return tree;
}


function getColor(text) {
  let colorList = ['#c7f69c', '#f2d975', '#f68ab9', '#ce9bf3', '#afd6ed','#bef2dc','#d9f9c7','#f9dec7'];
  let hash = 0;
  for (let i = 0; i < text.length; i++) {
      hash = text.charCodeAt(i) + ((hash << 5) - hash);
  }
  let color = '#';
  let rgba = 'rgba(255,255,255,0.6)';
  let rgblist = []
  for (let i = 0; i < 3; i++) {
      let value = (hash >> (i * 8)) & 0xFF;
      // 减少饱和度


      // value = Math.round(value + 128 - Math.pow(value - 128, 2) / 128);
      // rgblist.push(value)
      color += ('00' + value.toString(16)).substr(-2);
      
  }
  return color;
}


function uniqueByField(arr, field) {
  return arr.filter((item, index) => {
    return arr.findIndex(i => i[field] === item[field]) === index;
  });
}

function guid() {
  function S4() {
    return (((1 + Math.random()) * 0x10000) | 0).toString(16).substring(1);
  }
  return S4() + S4() + S4() + S4() + S4() + S4() + S4() + S4();
}

function countWordSplit(text) {
  // 使用正则表达式分割字符串，匹配非换行符、非空格、非下划线、非逗号的字符
  const words = text.split(/[\s=[\]{}()（）‘’|''\n_，、,=]+/);
  
  // 创建一个空对象来存储每个单词及其出现次数
  const wordCount = {};

  let max = 0;
  let min = 0;
  let wmax = 0;
  let wlength = words.length;
  // 遍历分割后的词汇数组，统计每个词汇的出现次数

  let maxSequenceLength = 0;
  let currentSequenceLength = 1;
  let previousNumber = null;
  words.forEach((word,i) => {
      if (word) { // 确保词汇不为空
       
          wordCount[word.toLowerCase()] = (wordCount[word.toLowerCase()] || 0) + 1;
          if (wordCount[word.toLowerCase()] > max) max = wordCount[word.toLowerCase()];
          if (wordCount[word.toLowerCase()] < min) min = wordCount[word.toLowerCase()];
          if(word.toLowerCase().length>wmax) wmax = word.toLowerCase().length;

          const match = words[i].match(/\d+$/); // 提取字母前缀和数字部分
          if (match) {
              let number = parseInt(match[0], 10);
              let prevnum = null;

              // 检查前一个词汇是否存在且数字连续递增
              if(words[i - 1] && words[i - 1].match(/\d+$/)){
                prevnum = parseInt(words[i - 1].match(/\d+$/)[0]) 
              }
              if ( previousNumber !== null && prevnum && number === prevnum + 1) {
                  currentSequenceLength++; // 如果是连续递增，则增加当前序列长度
              } else {
                  // 如果不是连续递增，重置当前序列长度为1，并更新最大序列长度（如果需要）
                  maxSequenceLength = Math.max(maxSequenceLength, currentSequenceLength);
                  currentSequenceLength = 1;
              }
              previousNumber = number; // 更新前一个数字为当前数字
          }
          
      }
  });

  maxSequenceLength = Math.max(maxSequenceLength, currentSequenceLength);
  
  // 返回结果对象
  return {word:wordCount,max,min,wlength,wmax,nummax:maxSequenceLength};
}

function initTableHeight(el,borderheight){
  setTimeout(function () {
    if(!el){
      let els = document.querySelectorAll(".c-js-initTableHeight");
      if(els.length==0) return false;
      els.forEach(item =>{
        initTableHeight(item,borderheight)
      })
      return false;
    }
    store.commit('scrollbarIndex')
    
    if(!el.querySelector(".c-js-body") || !el.querySelector(".c-js-item")) return;

    let height = 20;
    let arr = el.querySelectorAll(".c-js-item");
    for (let index = 0; index < arr.length; index++) {
        height += arr[index].offsetHeight;
    }
    el.querySelector(".c-js-body").style = "height:calc(100% - " + (height+borderheight) + "px)";
  }, 300);
}
/* eslint-enable */
export {
  initTableHeight,
  countWordSplit,
  guid,
  uniqueByField,
  getColor,
  renameChildrenKey,
  copyData,
  withInstall,
  scrollToTop,
  copyText,
  findPathById,
  replaceCodeToken,
  payBrowser,
  removeHtmlStyle,
  IsPC,
  transferString,
  getSystem,
  getImgBySize,
  setCookie,
  getCookie,
  delCookie,
  getUrlParam,
  replaceCode,
  getTokenFn,
  setTokenFn,
  setScrollTop,
  getScrollTop,
  findPathByLeafId,
};