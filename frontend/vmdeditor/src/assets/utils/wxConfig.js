
import { payBrowser } from '@/assets/utils/util';
// import store from '@/store';
import {
  GetJsSDKConfig,
} from '@/api/api';
/*eslint-disable*/ 
function wxConfig(wxShareData) {
  let url = window.encodeURIComponent(location.href.split('#')[0]);
  return new Promise( async (resolve,reject)=>{
    
  
  if (payBrowser().split('-')[0] == 'wechart') {
    //是微信内置浏览器  走config
    console.log('微信授权===='+location.href.split('#')[0]+'encodeURIComponent==='+url);
    let res = await GetJsSDKConfig({url:url});
    console.log(res)
    if(res.Success){
      let configdata = {
        debug: false, // 开启调试模式,调用的所有 api 的返回值会在客户端 alert 出来，若要查看传入的参数，可以在 pc 端打开，参数信息会通过 log 打出，仅在 pc 端时才会打印。
        appId: res.Data.AppID, // 必填，公众号的唯一标识
        timestamp: res.Data.Timestamp, // 必填，生成签名的时间戳
        nonceStr: res.Data.Noncestr, // 必填，生成签名的随机串
        signature: res.Data.Signature,// 必填，签名
        jsApiList: ['updateAppMessageShareData','updateTimelineShareData'] // 必填，需要使用的 JS 接口列表
      }
      console.log(configdata)
      wx.config(configdata);
      wx.ready(function(){
        console.log('wxready===')
        console.log(wxShareData)
        // 自定义“分享给朋友”及“分享到QQ”按钮的分享内容（1.4.0）
        wx.updateAppMessageShareData({ 
          title: wxShareData.title || '', // 分享标题
          desc: wxShareData.desc || '', // 分享描述
          link: wxShareData.link || '', // 分享链接，该链接域名或路径必须与当前页面对应的公众号 JS 安全域名一致
          imgUrl: wxShareData.imgUrl || '', // 分享图标
          success: function () {
            // 设置成功
            resolve({
              Success:true,
              wxShareData:wxShareData,
            })
          },
          cancel:function(){
            resolve({
              Success:false,
              wxShareData:wxShareData,
              error:'用户取消',
            })
          }
        })
        // 自定义“分享到朋友圈”及“分享到 QQ 空间”按钮的分享内容（1.4.0）
        wx.updateTimelineShareData({ 
          title: wxShareData.title || '', // 分享标题
          link: wxShareData.link || '', // 分享链接，该链接域名或路径必须与当前页面对应的公众号 JS 安全域名一致
          imgUrl: wxShareData.imgUrl || '', // 分享图标
          success: function () {
            // 设置成功
            resolve({
              Success:true,
              wxShareData:wxShareData,
            })
          },
          cancel:function(){
            resolve({
              Success:false,
              wxShareData:wxShareData,
              error:'用户取消',
            })
          }
        })

        //批量隐藏功能按钮接口  调整字体: "menuItem:setFont" 分享到QQ: "menuItem:share:qq"  分享到Weibo: "menuItem:share:weiboApp"
        // wx.hideMenuItems({
        //   menuList: ['menuItem:setFont'] // 要隐藏的菜单项，只能隐藏“传播类”和“保护类”按钮，所有 menu 项见附录3
        // });
      
      });
      wx.error(function(res){
        console.error(res);
        resolve({
          Success:false,
          wxShareData:wxShareData,
          error:res,
        })
        // config信息验证失败会执行 error 函数，如签名过期导致验证失败，具体错误信息可以打开 config 的debug模式查看，也可以在返回的 res 参数中查看，对于 SPA 可以在这里更新签名。
      });
    }
  }

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


export {
  wxConfig,
  wechartAgentConfig,
};
