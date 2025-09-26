<script setup>
// import { useRoute } from 'vue-router'
import { ref } from 'vue'

// import { useStore } from 'vuex';
// let { proxy } = getCurrentInstance();
// const store = useStore()
// const route = useRoute()

const isConsole = ref(window.localStorage.getItem('vConsole'))
const change = () =>{
  isConsole.value = !isConsole.value;
  if(isConsole.value){
    // 开启调试模式
    window.localStorage.setItem('vConsole',true);
  }else{
    window.localStorage.removeItem('vConsole');
  }
  window.location.reload();
}



</script>

<template>
  <div>
    <div>{{ msg }}</div>
    <el-button type="primary" @click="change()">{{isConsole?'关闭':'开启'}}调试模式</el-button>
  </div>
</template>

<style scoped>

</style>
