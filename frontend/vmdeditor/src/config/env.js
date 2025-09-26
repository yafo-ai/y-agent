
/* eslint-disable */
let COMMON_ENV = {
    version:'1.1.1',
    pcurl:'http://192.168.50.33:8080',
    addressVersion:'0000',
    COMMON_ADDRESS:'COMMON_ADDRESS',
    COMMON_ADDRESS_VERSION:'COMMON_ADDRESS_VERSION',
    ENV:'',
  };
  
  if (process.env.VUE_APP_ENV === 'production') {
      // 生产环境
      COMMON_ENV.pcurl = '';
      
  } else if (process.env.VUE_APP_ENV === 'dev') {
      // 开发环境
      COMMON_ENV.pcurl = '';
  } else if (process.env.VUE_APP_ENV === 'test') {
      // 测试环境
      COMMON_ENV.pcurl = '';
  }else if (process.env.VUE_APP_ENV === 'pre') {
      // 预发环境
      COMMON_ENV.pcurl = '';
  }
  COMMON_ENV.ENV = process.env.VUE_APP_ENV;
  
  export default COMMON_ENV;
  