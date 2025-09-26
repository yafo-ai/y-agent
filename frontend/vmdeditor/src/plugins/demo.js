export default {
  install: (app, options) => {
    // 在这里编写插件代码
    app.config.globalProperties.$myMethod = function () {
      return options.someOption
    }
  }
}

// import { createApp } from 'vue'

// const app = createApp({})

// app.use(myPlugin, {
//   /* 可选的选项 */
//   someOption: true
// })
// $myMethod()  //返回true