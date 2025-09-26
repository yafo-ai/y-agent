<script setup>
import {
  ref,
  onMounted,
  onBeforeUnmount,
  watch,
  onUnmounted,
} from "vue";
import { useRoute, useRouter } from "vue-router";
import { login, register } from "@/api/api";
import { useStore } from "vuex";
import icon from "@/components/icon.vue";
const route = useRoute();
const router = useRouter();
const form = ref({
  "username": "",
  "password": "",
  "nickname": "",
  "email": "",
  "phone": ""
});
const store = useStore();

const isLogin = ref(route.path === "/login");

const loginfn = (formEl) => {
  if (!formEl) return
  formEl.validate(async (valid, fields) => {
    if (valid) {
      sublogin({ username: form.value.username, password: form.value.password })

    }
  })
}
const sublogin = async (param, isReg) => {
  let res = await login(param)
  if (res && res.token) {
    window.localStorage.setItem('username', param.username);
    store.commit('username', param.username);
    store.commit('token', res.token);
    store.commit('userData', res);
    if (!isReg) {
      _this.$message('登录成功', 'success')
    }
    let url = '/'
    const fromPath = store.getters.routeData?.from?.fullPath
    if (fromPath && fromPath !== '/login') {
      url = fromPath
    }
    router.push(url)
  }
}

const reg = (formEl) => {
  if (!formEl) return
  formEl.validate(async (valid, fields) => {
    if (valid) {
      let res = await register(form.value)
      if (res && res.result === 'success') {
        _this.$message('注册成功', 'success')
        sublogin({ username: form.value.username, password: form.value.password }, true)
      }
    } else {
    }
  })
}
store.commit('token', '');
const fromModel = ref(null)

onMounted(() => {
  const interBubble = document.querySelector('.interactive');
  let curX = 0;
  let curY = 0;
  let tgX = 0;
  let tgY = 0;

  const move = () => {
    if (!interBubble) return;
    curX += (tgX - curX) / 20;
    curY += (tgY - curY) / 20;
    interBubble.style.transform = `translate(${Math.round(curX)}px, ${Math.round(curY)}px)`;
    requestAnimationFrame(move);
  };

  window.addEventListener('mousemove', event => {
    tgX = event.clientX;
    tgY = event.clientY;
  });

  move();
})
onUnmounted(() => {
  window.removeEventListener('mousemove', event => {
    tgX = event.clientX;
    tgY = event.clientY;
  });
})

</script>


<template>

  <div class="gradient-bg">

    <div class="pagelogin c-pagelogin">
      <div class="bg"></div>

      <div class="rbox">

        <div class="loginbox">

          <div v-if="isLogin" class="c-logo">
            <icon type="logo" width="300" height="120"></icon>
          </div>



          <!-- <div class="login-title">{{ isLogin ? '登录' : '注册' }}</div> -->
          <div :class="{ 'regbox': !isLogin }" class="formbox">
            <div v-if="!isLogin" class="regtitle">注册</div>
            <el-form :model="form" ref="fromModel" label-width="auto" label-position="top" @submit.native.prevent
              @keyup.native.enter.prevent="loginfn(fromModel)" style="width: 100%;" class="tl">
              <el-form-item label="用户名:" :rules="[
                {
                  required: true,
                  message: '请输入用户名',
                  trigger: 'blur',
                },
              ]" prop="username">
                <el-input size="large" v-model="form.username" placeholder=""></el-input>
              </el-form-item>
              <el-form-item label="密码:" :rules="[
                {
                  required: true,
                  message: '请输入密码',
                  trigger: 'blur',
                },
              ]" prop="password">
                <el-input size="large" v-model="form.password" show-password type="password" placeholder=""></el-input>
              </el-form-item>
              <template v-if="!isLogin">
                <el-form-item prop="nickname" label="昵称:">
                  <el-input size="large" v-model="form.nickname" placeholder=""></el-input>
                </el-form-item>
                <el-form-item prop="email" :rules="[
                  {
                    type: 'email',
                    message: '请输入有效的邮箱地址',
                    trigger: ['blur'],
                  },
                ]" label="邮箱:">
                  <el-input size="large" v-model="form.email" placeholder=""></el-input>
                </el-form-item>
                <el-form-item prop="phone" :rules="[
                  {
                    pattern: /^1[0123456789]\d{9}$/,
                    message: '请输入有效的手机号码',
                    trigger: ['blur'],
                  },
                ]" label="手机号:">
                  <el-input size="large" v-model="form.phone" placeholder=""></el-input>
                </el-form-item>
              </template>
            </el-form>


            <div style="margin-top: 30px;" v-if="!isLogin" class="linkbox"><el-link style="color: #a2a2a2;"
                @click="router.replace('/login'); isLogin = !isLogin" type="primary">
                <!-- <icon type="qdl"></icon> -->
                已有账号？去登录
              </el-link></div>
            <div v-if="isLogin" style="margin-top: 65px;" class="linkbox"><el-link style="color: #a2a2a2;"
                @click="router.replace('/reg'); isLogin = !isLogin" type="primary">
                <!-- <icon type="qzc"></icon> -->
                没有账号？去注册
              </el-link></div>


            <el-button style="width:100%;" @click="loginfn(fromModel)" v-if="isLogin" size="large"
              type="primary">登录</el-button>
            <el-button style="width:100%;margin-top: 0px;" @click="reg(fromModel)" v-if="!isLogin" size="large"
              type="primary">注册并登录</el-button>

              <div v-if="isLogin" class="sflogin">
                <a href="https://github.com/yafo-ai" target="_blank">
                <icon width="30" height="30" type="github"></icon></a>
                <a href="https://gitee.com/yafo-ai" target="_blank"><icon width="32" height="32"  type="loginmy"></icon></a>
                <a href="http://112.126.109.80/" target="_blank"><icon width="32" height="32"  type="logingw"></icon></a>
                <a href="http://112.126.109.80/docs" target="_blank"><icon width="32" height="32"  type="logindoc"></icon></a>
              </div>


              <div class="tip"><span>© Copyright  向量感知（北京）智能科技有限公司 YAFO 2025.</span></div>
          </div>
        </div>

      </div>

    </div>

    <svg viewBox="0 0 100vw 100vw" xmlns='http://www.w3.org/2000/svg' class="noiseBg">
      <filter id='noiseFilterBg'>
        <feTurbulence type='fractalNoise' baseFrequency='0.6' stitchTiles='stitch' />
      </filter>

      <rect width='100%' height='100%' preserveAspectRatio="xMidYMid meet" filter='url(#noiseFilterBg)' />
    </svg>
    <svg xmlns="http://www.w3.org/2000/svg" class="svgBlur">
      <defs>
        <filter id="goo">
          <feGaussianBlur in="SourceGraphic" stdDeviation="10" result="blur" />
          <feColorMatrix in="blur" mode="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 18 -8" result="goo" />
          <feBlend in="SourceGraphic" in2="goo" />
        </filter>
      </defs>
    </svg>
    <div class="gradients-container">
      <div class="g1"></div>
      <div class="g2"></div>
      <div class="g3"></div>
      <div class="g4"></div>
      <div class="g5"></div>
      <div class="interactive"></div>
    </div>
  </div>

</template>
<style>
:root {
  --color1: 18, 113, 255;
  --color2: 107, 74, 255;
  --color3: 100, 100, 255;
  --color4: 50, 160, 220;
  --color5: 80, 47, 122;
  --color-interactive: 140, 100, 255;
  --circle-size: 80%;
  --blending: hard-light;
}
</style>
<style scoped>
.tip{
  position: absolute;
  bottom: 20px;
  left: 0;
  right: 0;
  text-align: center;
  color: #999;
}
.sflogin{
  display: flex;
    align-items: center;
    justify-content: space-around;
    margin-top: 10px;
}
.sflogin a{
  /* margin-left: 20px; */
}
.c-pagelogin :deep(.el-input__wrapper) {
  box-shadow: none;
  border: none;
  background: #f1f1f1;
  border-radius: 20px;
  padding-left: 80px;
}

.c-pagelogin :deep(.el-form-item__error) {
  left: 16px;
}

.c-pagelogin .regbox :deep(.el-form-item) {
  margin-bottom: 0;
}

.c-pagelogin :deep(.el-form-item--label-top .el-form-item__label) {
  color: #a2a2a2;
  transform: translate(16px, 40px);
  z-index: 11;
  position: relative;
  display: block;
  width: 64px;
  text-align-last: justify;
}

.c-pagelogin :deep(.el-form-item--label-top .el-form-item__label::before) {
  display: none;
}

.regtitle {
  font-weight: 600;
  font-size: 24px;
  color: #333333;
  line-height: 33px;
  text-align: left;
  font-style: normal;
  margin-bottom: 24px;
}

@keyframes moveInCircle {
  0% {
    transform: rotate(0deg);
  }

  50% {
    transform: rotate(180deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

@keyframes moveVertical {
  0% {
    transform: translateY(-50%);
  }

  50% {
    transform: translateY(50%);
  }

  100% {
    transform: translateY(-50%);
  }
}

@keyframes moveHorizontal {
  0% {
    transform: translateX(-50%) translateY(-10%);
  }

  50% {
    transform: translateX(50%) translateY(10%);
  }

  100% {
    transform: translateX(-50%) translateY(-10%);
  }
}

.gradient-bg {
  width: 100vw;
  height: 100vh;
  position: relative;
  overflow: hidden;
  background: linear-gradient(40deg, rgb(8, 10, 15), rgb(0, 17, 32));
  top: 0;
  left: 0;
}

.gradient-bg .svgBlur {
  display: none;
}

.gradient-bg .noiseBg {
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  z-index: 1;
  mix-blend-mode: soft-light;
  opacity: 0.3;
}

.gradient-bg .gradients-container {
  filter: url(#goo) blur(40px);
  width: 100%;
  height: 100%;
}

.gradient-bg .g1 {
  position: absolute;
  background: radial-gradient(circle at center, rgba(var(--color1), 0.8) 0, rgba(var(--color1), 0) 50%) no-repeat;
  mix-blend-mode: var(--blending);
  width: var(--circle-size);
  height: var(--circle-size);
  top: calc(50% - var(--circle-size) / 2);
  left: calc(50% - var(--circle-size) / 2);
  transform-origin: center center;
  animation: moveVertical 30s ease infinite;
  opacity: 1;
}

.gradient-bg .g2 {
  position: absolute;
  background: radial-gradient(circle at center, rgba(var(--color2), 0.8) 0, rgba(var(--color2), 0) 50%) no-repeat;
  mix-blend-mode: var(--blending);
  width: var(--circle-size);
  height: var(--circle-size);
  top: calc(50% - var(--circle-size) / 2);
  left: calc(50% - var(--circle-size) / 2);
  transform-origin: calc(50% - 400px);
  animation: moveInCircle 20s reverse infinite;
  opacity: 1;
}

.gradient-bg .g3 {
  position: absolute;
  background: radial-gradient(circle at center, rgba(var(--color3), 0.8) 0, rgba(var(--color3), 0) 50%) no-repeat;
  mix-blend-mode: var(--blending);
  width: var(--circle-size);
  height: var(--circle-size);
  top: calc(50% - var(--circle-size) / 2 + 200px);
  left: calc(50% - var(--circle-size) / 2 - 500px);
  transform-origin: calc(50% + 400px);
  animation: moveInCircle 40s linear infinite;
  opacity: 1;
}

.gradient-bg .g4 {
  position: absolute;
  background: radial-gradient(circle at center, rgba(var(--color4), 0.8) 0, rgba(var(--color4), 0) 50%) no-repeat;
  mix-blend-mode: var(--blending);
  width: var(--circle-size);
  height: var(--circle-size);
  top: calc(50% - var(--circle-size) / 2);
  left: calc(50% - var(--circle-size) / 2);
  transform-origin: calc(50% - 200px);
  animation: moveHorizontal 40s ease infinite;
  opacity: 0.7;
}

.gradient-bg .g5 {
  position: absolute;
  background: radial-gradient(circle at center, rgba(var(--color5), 0.8) 0, rgba(var(--color5), 0) 50%) no-repeat;
  mix-blend-mode: var(--blending);
  width: calc(var(--circle-size) * 2);
  height: calc(var(--circle-size) * 2);
  top: calc(50% - var(--circle-size));
  left: calc(50% - var(--circle-size));
  transform-origin: calc(50% - 800px) calc(50% + 200px);
  animation: moveInCircle 20s ease infinite;
  opacity: 1;
}

.gradient-bg .interactive {
  position: absolute;
  background: radial-gradient(circle at center, rgba(var(--color-interactive), 0.8) 0, rgba(var(--color-interactive), 0) 50%) no-repeat;
  mix-blend-mode: var(--blending);
  width: 100%;
  height: 100%;
  top: -50%;
  left: -50%;
  opacity: 0.7;
}

.c-logo {
  margin: 0 auto 60px auto;
}

.login-title {
  font-size: 22px;
  font-weight: bold;
  padding: 20px 0 10px 0;
}

.linkbox {
  text-align: right;
  margin-bottom: 10px;
  color: #999;
}

.linkbox .iconfont {
  font-size: 20px;
}

.pagelogin {
  display: flex;
  width: 1160px;
  height: 636px;
  position: absolute;
  left: 50%;
  top: 50%;
  margin: -318px 0 0 -580px;
  z-index: 11;
  align-items: flex-start;
  justify-content: flex-end;
}

.lbox {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.pagelogin .bg {
  width: 872px;
  height: 770px;
  background-image: url(@/assets/imgs/loginbg.png);
  background-size: cover;
  background-repeat: no-repeat;
  position: absolute;
  top: -40px;
  right: 346px;
}

.rbox {
  display: flex;
  position: relative;
  width: 445px;
  height: 100%;
  background: #Fff;
  box-sizing: border-box;
  align-items: center;
  justify-content: center;
}

.loginbox {
  width: 100%;
  max-width: 600px;
}

.formbox {
  max-width: 300px;
  margin: 0 auto;
}
</style>