<script setup>
import { useStore } from "vuex";
import { watch, ref, onMounted, onUnmounted, provide } from "vue";
import { useRoute, useRouter } from "vue-router";
import icon from "@/components/icon.vue"
import options from "@/components/options.vue"
import { formatDate } from "@/assets/utils/timefn"
const route = useRoute();
const router = useRouter();
const store = useStore();


const updateWindowHeight = () => {
  store.dispatch('updateWindowHeight');
};
onMounted(() => {
  window.addEventListener('resize', updateWindowHeight);
  updateWindowHeight(); // 初始化时也调用一次以设置初始值
});
onUnmounted(() => {
  window.removeEventListener('resize', updateWindowHeight);
});

const list = ref([
  {
    path: "/flowlist",
    icon: "icon-liuchengtu-weixuanzhong",
    icon1: "icon-liuchengtu-xuanzhong-caidanicon",
    class: "c-i-lct",
    txt: "流程图",
  },
  {
    path: "/reportflow",
    icon: "icon-liuchengrizhi-weixuanzhong-caidanicon",
    icon1: "icon-liuchengrizhi-xuanzhong-caidanicon",
    class: "c-i-lcrz",
    txt: "流程日志",
  },
  {
    path: "/app/list",
    icon: "icon-tishici-weixuanzhong-caidanicon",
    icon1: "icon-tishici-xuanzhong-caidanicon",
    class: "c-i-tsc",
    txt: "提示词",
  },
  {
    path: "/shoplist",
    icon: "icon-shangpinguanli-weixuanzhong-caidanicon",
    icon1: "icon-shangpinguanli-xuanzhong-caidanicon",
    class: "c-i-spgl",
    txt: "商品管理",
  },
  {
    path: "/dataset/list",
    icon: "icon-zhishiku-weixuanzhong-caidanicon",
    icon1: "icon-zhishiku-xuanzhong-caidanicon",
    class: "c-i-zsk",

    txt: "知识库",
  },

  {
    path: "/test",
    icon: "icon-a-liuchengceshi-weixuanzhong-caidanicon2",
    icon1: "icon-a-liuchengceshi-xuanzhong-caidanicon2",
    class: "c-i-lccs",

    txt: "流程测试",
  },
  {
    path: "/unittest",
    icon: "icon-danyuanceshi-weixuanzhong-caidanicon",
    icon1: "icon-danyuanceshi-xuanzhong-caidanicon",
    class: "c-i-dycs",
    txt: "单元测试",
  },
  {
    path: "/testplan",
    icon: "icon-ceshijihua-weixuanzhong-caidanicon",
    icon1: "icon-ceshijihua-xuanzhong-caidanicon",
    class: "c-i-csjh",
    txt: "测试计划",
  },
  {
    path: "/testreport",
    icon: "icon-ceshibaogao-weixuanzhong-caidanicon",
    icon1: "icon-ceshibaogao-xuanzhong-caidanicon",
    class: "c-i-csbg",
    txt: "测试报告",
  },

  {
    path: "/edu",
    icon: "icon-xunlian-weixuanzhong-caidanicon",
    icon1: "icon-xunlian-xuanzhong-caidanicon",
    class: "c-i-xl",
    txt: "语料",
  },
  {
    path: "/learn",
    icon: "icon-a-qianghuaxuexi1",
    icon1: "icon-a-qianghuaxuexi1",
    class: "c-i-qhxx",
    txt: "强化学习",
  },

  {
    path: "/llmlist",
    icon: "icon-moxingpeizhi-weixuanzhong-caidanicon",
    icon1: "icon-moxingpeizhi-xuanzhong-caidanicon",
    class: "c-i-mxpz",
    txt: "模型配置",
  },
  {
    path: "/utillist",
    icon: "icon-gongjuchajian-weixuanzhong-caidanicon",
    icon1: "icon-gongjuchajian-xuanzhong-caidanicon",
    class: "c-i-gjcj",
    txt: "工具插件",
  },
  {
    path: "/userlist",
    icon: "icon-yonghuguanli-weixuanzhong-caidanicon",
    icon1: "icon-yonghuguanli-xuanzhong-caidanicon",
    class: "c-i-yhgl",
    txt: "用户管理",
  },
  // {
  //   path: "/login",
  //   icon: "icon-jieshu1",
  //   txt: "退出登录",
  // },
]);
const refresh = () => {
  window.location.reload();
};
const rindex = ref(-1);
const initIndex = () => {
  let cpath = route.path;
  list.value.forEach((item, index) => {
    if (item.path == cpath || isPath(item.path, route.meta.fpath)) {
      rindex.value = index;
    }
  });
  let top = document
    .querySelectorAll(".leftnav .item")
  [rindex.value].getBoundingClientRect().top;
  curTop.value = top + 12;
};
const curTop = ref(0);
const getCurTop = (e, index) => {
  let top = e.target.getBoundingClientRect().top;
  curTop.value = top + 12;
  rindex.value = index;
};
// initIndex();

const isPath = (path, fpath) => {
  if (!fpath) return false;
  if (route.query.fpath) {
    fpath = route.query.fpath;
    let qpath = fpath.split("?")[0];
    if (qpath == path) return true;
  }
  let arr = fpath.split(",");
  let flag = false;
  arr.forEach((item) => {
    if (item == path) {
      flag = true;
    }
  });
  return flag;
};



// const curtime = ref(formatDate(new Date().getTime(), "yy-mm-dd"))
const curtime = ref('版本：0.0.0-beta')
const isShowOpt = ref(false)
</script>

<template>
  <div v-if="route.path != '/'" class="app-contain">

    <div v-if="route.meta.fullscreen" class="layout">
      <div class="routerbox fullscreen">
        <router-view></router-view>
      </div>
    </div>
    <div v-else class="layout">

      <div class="navbox c-leftnav">
        <icon type="logo1" width="40" height="40"></icon>
        <div class="navcontain">
          <el-scrollbar>
            <div class="leftnav">
              <!-- <div v-if="rindex !== -1" :style="'top:' + curTop + 'px'" class="bg"></div> -->
              <div class="item" @mouseenter="getCurTop($event, index)" @mouseleave="initIndex()" :class="{
                on:
                  item.path == $route.path ||
                  isPath(item.path, $route.meta.fpath),
              }" @click="$router.push(item.path)" v-for="(item, index) in list" :key="index">
                <span :class="'iconfont nocheck ' + item.icon"></span>
                <span :class="'iconfont check ' + item.icon1"></span>
                {{ item.txt }}
              </div>
            </div>
          </el-scrollbar>
        </div>
      </div>
      <div class="app-userbox">
        <div style="margin-right: 10px;" class="userbox">
          <div class="btn-kefu btn" title="客服">
            <span style="left: 1px;" class="iconfont icon-daohanglan-xiaoxitongzhi"></span>
          </div>
        </div>
        <div class="searchbox">
          <span class="iconfont icon-daohanglan-sousuo"></span>
          <input type="text" placeholder="搜索">
        </div>
        <div class="userbox">
          <div @click="isShowOpt = true;" class="btn-kefu btn" title="系统配置">
            <span style="left: 1px;" class="iconfont icon-moxingpeizhi-weixuanzhong-caidanicon"></span>
          </div>
          <div class="btn-logout btn" @click="$router.push('/login')" title="退出登录">
            <span style="left: 1px;" class="iconfont icon-daohanglan-tuichudenglu"></span>
          </div>
          <div class="user">
            <div class="phone btn">
              <icon width="30" height="30" type="userphone"></icon>
              <span class="status on"></span>
            </div>
            <div v-if="store.state.username" class="namebox">
              <div class="name">{{ store.state.username }}</div>
              <div class="time">{{ curtime }}</div>
            </div>
          </div>
        </div>
      </div>
      <div class="routerbox">
        <router-view></router-view>
      </div>
    </div>

    <!-- loading -->
    <div class="c-loading" v-show="store.state.loading">
      <!-- showVuxMask纯遮罩层使用 -->
      <div class="el-loading-spinner">
        <svg viewBox="25 25 50 50" class="circular">
          <circle cx="50" cy="50" r="20" fill="none" class="path"></circle>
        </svg><!---->
      </div>
    </div>

    <div v-show="store.state.netError" class="c-networkErrorBox">
      <!-- 网络连接失败报错 -->
      <div style="width: 100%; margin-top: -60px">
        <div class="c-emptybox">
          <icon type="empzwwl" width="100" height="100"></icon>
        </div>
        <div class="tc">网络信号弱，请稍后再试</div>
        <el-button @click="refresh()" type="primary">重新加载</el-button>
      </div>
    </div>
  </div>
  <options v-model="isShowOpt"></options>
</template>

<style scoped>
.logoutbox {
  position: absolute;
  right: 30px;
  top: 0px;
  z-index: 11;
}

.app-contain {
  display: block;
  width: 100%;
  height: 100%;
  position: fixed;
  left: 0;
  top: 0;
  right: 0;


}

.app-contain .layout {
  display: flex;
  position: absolute;
  left: 0;
  top: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(136deg, #EEF8FF 0%, rgba(238, 248, 255, 0.4) 50%, #F8F8F8 100%);
}

.app-contain .layout .navbox.c-leftnav {
  flex-shrink: 0;
  display: block;
  width: 96px;
  height: 100%;
  box-sizing: border-box;
  background: linear-gradient(177deg, #D1EBFF 0%, #F3F5F8 100%);
  padding-top: 24px;
}

.app-contain .layout .navbox.c-leftnav .navcontain {
  display: block;
  height: calc(100% - 64px);
}





.app-contain .layout .routerbox {
  position: absolute;
  top: 70px;
  /* padding-top: 70px; */
  left: 116px;
  right: 20px;
  bottom: 20px;
  border-radius: 20px;
}

.app-contain .app-userbox {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  position: absolute;
  top: 10px;
  right: 24px;
  height: 40px;
  box-sizing: border-box;
  z-index: 10;
}

.app-userbox .searchbox {
  width: 314px;
  height: 32px;
  box-shadow: 0px 2px 8px 0px #D7E0E7;
  border-radius: 10px;
  padding: 3px 20px 3px 34px;
  box-sizing: border-box;
  background-color: rgba(255, 255, 255, 0.9);
  position: relative;
}

.app-userbox .searchbox>.iconfont {
  position: absolute;
  left: 8px;
  font-size: 20px;
  top: 0px;
}

.app-userbox .userbox {
  display: flex;
  height: 30px;
  align-items: center;
  justify-content: flex-end;
}

.app-userbox .userbox .btn {
  width: 30px;
  height: 30px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0px 2px 6px 0px #B0C0CC;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 100%;
  cursor: pointer;
  margin-left: 24px;
  position: relative;
}

.app-userbox .userbox .btn .status {
  display: block;
  position: absolute;
  width: 8px;
  height: 8px;
  border-radius: 4px;
  background: #00DF6C;
  right: 0;
  bottom: 0;
}

.app-userbox .userbox .btn:hover {
  opacity: 0.7;
}

.app-userbox .userbox .btn .iconfont {
  font-size: 22px;
  font-weight: bold;
  position: relative;
}

.app-userbox .userbox .user {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  text-align: left;
}

.app-userbox .userbox .user .namebox {
  padding-left: 10px;
}

.app-userbox .userbox .user .namebox .name {
  font-weight: bold;
  font-size: 16px;
  color: #333333;
  line-height: 22px;
  text-align: left;
  font-style: normal;
}

.app-userbox .userbox .user .namebox .time {
  font-weight: 400;
  font-size: 12px;
  color: var(--el-text-color-regular);
  line-height: 17px;
  text-align: left;
  font-style: normal;
}

.app-userbox .searchbox input {
  outline: none;
  background: none;
  display: block;
  width: 100%;
  height: 100%;
  box-sizing: border-box;
  font-size: 14px;
  color: var(--el-text-color-regular);
  text-align: left;
}

.app-contain .layout .routerbox.fullscreen {
  left: 0;
  right: 0;
  bottom: 0;
  top: 0;
  border-radius: 0;
}

.c-networkErrorBox,
.c-loading {
  position: fixed;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  top: 0;
  left: 0;
  z-index: var(--zindexMax);
  background: rgba(255, 255, 255, 0.7);
}

.c-networkErrorBox {
  background: var(--appbg);
}

.c-networkErrorBox .tc {
  margin: 10px auto 20px auto;
  font-size: 12px;
  color: var(--containcolor);
}

.c-networkErrorBox img {
  display: block;
  width: 160px;
  height: auto;
  margin: 0 auto;
}

.el-loading-spinner .circular {
  height: 42px;
  width: 42px;
  animation: loading-rotate 2s linear infinite;
}

.el-loading-spinner .path {
  animation: loading-dash 1.5s ease-in-out infinite;
  stroke-dasharray: 90, 150;
  stroke-dashoffset: 0;
  stroke-width: 2;
  stroke: var(--el-color-primary);
  stroke-linecap: round;
}

.el-loading-spinner i {
  color: var(--el-color-primary);
}

.el-loading-fade-enter,
.el-loading-fade-leave-active {
  opacity: 0;
}
</style>
