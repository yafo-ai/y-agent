<script setup>
// import { useRoute } from 'vue-router'
import { ref, onMounted, onBeforeUnmount, reactive, watch } from "vue";
import JsMark from "js-mark";
import VueDiff from "vue-diff";
import "vue-diff/dist/index.css";
// import { useStore } from 'vuex';
// let { proxy } = getCurrentInstance();
// const store = useStore()
// const route = useRoute()
import { diffChars } from "diff";

const a = ref("这是第一行文字。\n这是第二行文字。1\n这是第二行文字。1");
const a1 = ref("这是第一行文字。\n这是2第二行文字。1");

const diffString = diffChars(a.value, a1.value);

const newVal = ref("");
const oldVal = ref("");
</script>

<template>
  <Diff
    class="c-v-diff"
    mode="split"
    theme="light"
    language="text"
    :prev="newVal"
    :current="oldVal"
    style="height: calc(100% - 340px); width: 100%; overflow: scroll"
  />

  <div class="inpbox c-diffbox-input">
    <div class="item">
      <el-input
        class="lboxinput"
        v-model="newVal"
        @focus="$event.target.select()"
        style="width: 100%; height: 100%"
        :rows="14"
        type="textarea"
        placeholder="请输入对比文本"
      />
    </div>
    <div class="item">
      <el-input
        v-model="oldVal"
        class="rboxinput"
        @focus="$event.target.select()"
        style="width: 100%; height: 100%"
        type="textarea"
        :rows="14"
        placeholder="输入对比文本"
      />
    </div>
  </div>
</template>

<style scoped>
.c-diffbox-input {
  display: flex;
  justify-content: space-around;
  height: 300px;
}
.c-diffbox-input .item {
  width: calc(50% - 10px);
  height: 100%;
}
.c-diffbox-input .lboxinput :deep(.el-textarea__inner) {
  box-shadow: 0 0 0 1px #ffc3c3 inset;
}
.c-diffbox-input .rboxinput :deep(.el-textarea__inner) {
  box-shadow: 0 0 0 1px #c3ffe1 inset;
}
</style>
