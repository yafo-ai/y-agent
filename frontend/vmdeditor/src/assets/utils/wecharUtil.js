
import { payBrowser } from '@/assets/utils/util';
import store from '@/store';
import {
  AgentConfig,
  Config,
} from '@/api/api';
/*eslint-disable*/ 
function wechartConfig() {
  let url = window.encodeURIComponent(window.location.href);
  // wx.config({
  //   beta: true, // 必须这么写，否则wx.invoke调用形式的jsapi会有问题
  //   debug: true, // 开启调试模式,调用的所有api的返回值会在客户端alert出来，若要查看传入的参数，可以在pc端打开，参数信息会通过log打出，仅在pc端时才会打印。
  //   appId: '', // 必填，企业微信的corpID
  //   timestamp: '', // 必填，生成签名的时间戳
  //   nonceStr: '', // 必填，生成签名的随机串
  //   signature: '', // 必填，签名，见 附录-JS-SDK使用权限签名算法
  //   jsApiList: [], // 必填，需要使用的JS接口列表，凡是要调用的接口都需要传进来
  // });
  return new Promise(async (resolve, reject) => {
    if (payBrowser().split('-')[0] == 'wechart') {
      //是微信内置浏览器  走config
      let res = await Config({url:url})
      if(res.Success){

        let wconfig = await configfn({
            beta: true, // 必须这么写，否则wx.invoke调用形式的jsapi会有问题
            debug: false, // 开启调试模式,调用的所有api的返回值会在客户端alert出来，若要查看传入的参数，可以在pc端打开，参数信息会通过log打出，仅在pc端时才会打印。
            appId: res.Data.CorpId, // 必填，企业微信的corpID
            timestamp: res.Data.Timestamp, // 必填，生成签名的时间戳
            nonceStr: res.Data.NonceStr, // 必填，生成签名的随机串
            signature: res.Data.Signature, // 必填，签名，见 附录-JS-SDK使用权限签名算法
            jsApiList: ['selectEnterpriseContact'], // 必填，需要使用的JS接口列表，凡是要调用的接口都需要传进来
        }).catch(()=>{
          reject()
        });
      }
    }

    // 授权企业微信
    let agRes = await AgentConfig({ url:url }).catch(()=>{
      reject()
    });
    
    if (agRes && agRes.Success) {
      store.commit('wechart/setangintConfig', agRes.Data);
      let agResConfig = await wechartAgentConfig(agRes.Data).catch(()=>{
        reject()
      });;
    }else{
      store.commit('wechart/setangintConfig', {
        ClientType:'-1',
      });
    }
    resolve(true)
  })
  
}

async function configfn(config) {
  let { wx } = window;
  return new Promise((resolve, reject) => {
      wx.config(config)
      wx.ready(resolve)
      wx.error(reject)
  }).then(() => {
      console.info('wx.ready')
  }, error => {
      console.error('wx.error', error)
      // alert('wx.error',JSON.stringify(error))
      // throw error
  })
}


function wechartAgentConfig(config) {

  if(!config){
    return;
  }
  let configOpt={
    corpid:config.AuthCorpId,
    agentid: config.Agentid, // 必填，企业微信的应用id （e.g. 1000247）
    timestamp: config.Timestamp, // 必填，生成签名的时间戳
    nonceStr: config.NonceStr, // 必填，生成签名的随机串
    signature: config.Signature,// 必填，签名，见附录1
    jsApiList:['selectExternalContact'],
  }
  let { wx } = window;
  return new Promise((success, fail) => {
    wx.agentConfig({ ...configOpt, success, fail });
  }).then((res) => {
    return res;
  }, (error) => {
    console.error('wx.agentConfig fail', error);
    // alert('wx.agentConfig fail'+JSON.stringify(error))
    // throw error;
  });
}

function ddconfig(config){
  if(!config){
    return;
  }
  dd.config({
    agentId: '', // 必填，微应用ID
    corpId: '',//必填，企业ID
    timeStamp: '', // 必填，生成签名的时间戳
    nonceStr: '', // 必填，自定义固定字符串。
    signature: '', // 必填，签名
    type:0/1,   //选填。0表示微应用的jsapi,1表示服务窗的jsapi；不填默认为0。该参数从dingtalk.js的0.8.3版本开始支持
    jsApiList : [
        'runtime.info',
        'biz.contact.choose',
        'device.notification.confirm',
        'device.notification.alert',
        'device.notification.prompt',
        'biz.ding.post',
        'biz.util.openLink',
    ] // 必填，需要使用的jsapi列表，注意：不要带dd。
});

dd.error(function (err) {
    alert('dd error: ' + JSON.stringify(err));
})//该方法必须带上，用来捕获鉴权出现的异常信息，否则不方便排查出现的问题
}

export {
  wechartConfig,
  wechartAgentConfig,
};
