/*eslint-disable*/
//防止浏览器调整字体大小

(function flexible (window, document) {
  var docEl = document.documentElement
  var dpr = window.devicePixelRatio || 1
  window.user_webset_font = undefined;
  // adjust body font size
  function setBodyFontSize () {
    setRemUnit()
    if (document.body) {
      document.body.style.fontSize = (12 * dpr) + 'px'
    }
    else {
      document.addEventListener('DOMContentLoaded', setBodyFontSize)
    }
  }
  setBodyFontSize();
  function modifileRootRem () {
    var root = document.documentElement
    var fontSize = parseFloat(root.style.fontSize)
    var finalFontSize = parseFloat(window.getComputedStyle(root).getPropertyValue('font-size'))
    if (finalFontSize <= fontSize) return fontSize;
    return fontSize + (fontSize - finalFontSize);
  }
  // set 1rem = viewWidth / 10
  function setRemUnit () {
     //      用原生方法获取用户设置的浏览器的字体大小(兼容ie)
     if(!window.user_webset_font){
        
        if (docEl.currentStyle) {
          window.user_webset_font = docEl.currentStyle.fontSize;
        } else {
          window.user_webset_font = window.getComputedStyle(docEl, false).fontSize;
        }
        //      取整后与默认16px的比例系数
        // user_webset_font = modifileRootRem();
        let xs = parseFloat(user_webset_font) / 16;
        if(xs<1){
          xs = 1;
        }
        var cwidth = docEl.clientWidth > 750 ? 750 : docEl.clientWidth;
        var rem = cwidth / 10
        docEl.style.fontSize = rem/xs + 'px'
      }
  }

  // setRemUnit()
  window.setRemUnit = setRemUnit;
  // reset rem unit on page resize
  // window.addEventListener('resize', setRemUnit)
  window.setRemUnit = setRemUnit;
  window.addEventListener('pageshow', function (e) {
    if (e.persisted) {
      setRemUnit()
    }
  })
  window.addEventListener('load', function (e) {
      setRemUnit()
  })

  // detect 0.5px supports
  if (dpr >= 2) {
    var fakeBody = document.createElement('body')
    var testElement = document.createElement('div')
    testElement.style.border = '.5px solid transparent'
    fakeBody.appendChild(testElement)
    docEl.appendChild(fakeBody)
    if (testElement.offsetHeight === 1) {
      docEl.classList.add('hairlines')
    }
    docEl.removeChild(fakeBody)
  }

  if (typeof WeixinJSBridge == "object" && typeof WeixinJSBridge.invoke == "function") {
    handleFontSize();
  } else {
    if (document.addEventListener) {
      document.addEventListener("WeixinJSBridgeReady", handleFontSize, false);
    } else if (document.attachEvent) {
      document.attachEvent("WeixinJSBridgeReady", handleFontSize);
      document.attachEvent("onWeixinJSBridgeReady", handleFontSize);
    }
  }

  function handleFontSize() {
    // 设置网页字体为默认大小
    WeixinJSBridge.invoke('setFontSizeCallback', {
      'fontSize': 0
    });
    // 重写设置网页字体大小的事件
    WeixinJSBridge.on('menu:setfont', function () {
      
      WeixinJSBridge.invoke('setFontSizeCallback', {
        'fontSize': 0
      });
    });
    // 重新计算rem
    window.setRemUnit();
  }
}(window, document))
