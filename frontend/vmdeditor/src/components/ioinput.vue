<script setup>
import { ref, nextTick, onMounted, reactive, watch } from "vue";
import { useStore } from "vuex";
import { useRoute, useRouter } from "vue-router";
import { Search } from '@element-plus/icons-vue'
const props = defineProps({

  input: {
    type: [String, Array],
    default: () => '',
  },
  output: {
    type: [String, Array],
    default: () => '',
  },
  messages: {
    type: [Array],
    default: () => undefined,
  },
  isShowOutput: {
    type: Boolean,
    default: false,
  },

});
const emits = defineEmits(['subfn', 'update:modelValue'])
const route = useRoute();
const router = useRouter();
const store = useStore();
import icon from "@/components/icon.vue"
// replace(/\n/g, '<br>')


const close = () => {
  emits('update:modelValue', false)
}

const sub = (params) => {
  emits('subfn', params)
}

</script>
<template>

  <div v-if="!isShowOutput" class="c-ioinputbox">
    <div :title="props.input" class="input ellipsis">
      <span class="btn">输入</span>
      <span class="text">{{ props.input }}</span>
    </div>
  </div>

  <el-popover v-else-if="isShowOutput" size="large" placement="right" :width="500" trigger="hover">
    <template #reference>
      <div class="c-ioinputbox">
        <!-- <div v-if="!isShowOutput" class="input ellipsis">
          <span class="btn">输入</span>
          <span class="text">{{ props.input }}</span>
        </div> -->
        <!-- <div class="row"></div>-->
        <div v-if="isShowOutput && props.output" class="output ellipsis">
          <span class="btn">输出</span>
          <span class="text">{{ props.output || '' }}</span>
        </div>
      </div>

    </template>

    <div class="c-ioinputbox-contain">
      <el-scrollbar max-height="494">
        <div style="margin: 0 20px;">
          <div class="title">
            <icon style="margin-right: 5px;" width="24" height="24" type="shuru"></icon> 输入
          </div>
          <div v-if="props.input" v-html="props.input.replace(/\n/g, '<br>')" class="inpbox">

          </div>
          <div class="title">
            <icon style="margin-right: 5px;" width="24" height="24" type="shuchu"></icon> 输出
          </div>
          <div v-if="props.messages" v-for="item in props.messages" class="human_messagesitem">
            <div class="name">{{ item.from_role }} </div>
            <div v-html="item.message.replace(/\n/g, '<br>')" class="text"></div>
          </div>
          <div v-else-if="props.output" class="human_messagesitem">
            <div v-html="props.output.replace(/\n/g, '<br>')" class="text"></div>
          </div>
        </div>
      </el-scrollbar>

    </div>
  </el-popover>
</template>
<style scoped>
.c-ioinputbox {
  display: block;
  width: 100%;
  position: relative;
  font-size: inherit;
}

.c-ioinputbox-contain {
  margin: 0 -20px;
}

.c-ioinputbox-contain .title {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  font-weight: 500;
  font-size: 14px;
  color: #333333;
  text-align: left;
  font-style: normal;
}

.c-ioinputbox-contain .inpbox {
  background: var(--c-lbg-color);
  border-radius: 12px;
  padding: 12px;
  margin: 8px 0 30px 0;
}

.human_messagesitem {
  padding: 12px 0;
  border-bottom: 1px solid #E6E6E6;
}

.human_messagesitem:nth-last-child(1) {
  border-bottom: none;
}

.human_messagesitem .name {
  font-size: 12px;
  color: #888888;
  line-height: 20px;
  text-align: left;
  font-style: normal;
}

.text {
  line-height: 20px;
  text-align: left;
  font-style: normal;
  margin-top: 8px;
}

.human_messagesitem .text {
  color: #333;
  font-size: 14px;
}

.c-ioinputbox .input,
.c-ioinputbox .output {
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.c-ioinputbox .btn {
  display: inline-block;
  padding: 2px 6px;
  font-size: 12px;
  line-height: 12px;
  border-radius: var(--el-border-radius-base);
  border: 1px solid rgba(0, 0, 0, 0.05);
  margin-right: 4px;
}

.c-ioinputbox .row {
  height: 6px;
  margin: 2px 0;
  position: relative;
}

.c-ioinputbox .row::after {
  content: '';
  position: absolute;
  top: 0;
  left: 19px;
  width: 1px;
  height: 100%;
  background: rgba(0, 0, 0, 0.05);
  background: #D1DFD5;
}

.c-ioinputbox .input .btn {
  color: #6788d5;
  background: var(--el-color-primary-light-9);
}

.c-ioinputbox .output .btn {
  color: var(--el-color-success);
  background: var(--el-color-success-light-9);
}
</style>