<script setup>
import {
  ref,
  nextTick,
  shallowRef,
  getCurrentInstance,
  onActivated,
  reactive,
  watch,
} from "vue";
import { onBeforeRouteLeave, useRoute, useRouter } from "vue-router";
import { useStore } from "vuex";
const active = ref('1')
</script>
<template>
  <div class="pagelistbox">
    <div class="c-titlebox">
      <div class="title">强化学习</div>
    </div>
    <div style="margin-bottom: 0;" class="tabbox">
      <el-tabs v-model="active"  class="demo-tabs">
        <el-tab-pane name="1">
          <template #label> 学习任务 </template>
        </el-tab-pane>
        <el-tab-pane name="2">
          <template #label> 奖励函数 </template>
        </el-tab-pane>

      </el-tabs>
    </div>

    <div class="contain">
      10月正式版开放此功能。
    </div>
  </div>
</template>
<style scoped>
.contain{
  display: block;
  padding: 30px 20px;
  text-align: left;
  font-size: 18px;
}
</style>