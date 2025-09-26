const hostUrl = 'http://193.111.99.22:8087/';
// const hostUrl = 'https://vip.haocai.com/';
const pageProxy = {
  '/api': {
    target: hostUrl,
    changeOrigin: true,
    pathRewrite: { '^/api': '/api' },
  },
};

module.exports = pageProxy;


// https://devfl.haocai.com.cn/     master
// http://193.111.99.44:8082   test
// http://193.111.99.22:8087/   dev
