<script setup>
import { ref, nextTick, onMounted, reactive,watch } from "vue";
import { useStore } from "vuex";
import { useRoute, useRouter } from "vue-router";
import { Search } from '@element-plus/icons-vue'
const props = defineProps({
  id: {
    type: [String, Number],
    default: () => 0,
  },
  title:{
    type:[String, Number],
    default:'新建文件夹',
  },
  val:{
    type:[String, Number],
    default:'',
  },
  modelValue: { type: Boolean, default: false },
});
const emits = defineEmits(['subfn','update:modelValue'])
const route = useRoute();
const router = useRouter();
const store = useStore();

const dialogFormVisible = ref(false);

watch(
  () => props.modelValue,
  async (n, old) => {
    if (n !== old && n) {
      init()
    }
    dialogFormVisible.value = n;
  }
);

const init = () => {
  
}


const close = () => {
   emits('update:modelValue', false)
}

const sub = (params) => {
   emits('subfn', params)
}

</script>
<template>
  <el-dialog align-center v-model="dialogFormVisible" :title="title" @closed="close" width="500">
    <el-form @submit.native.prevent  @keyup.native.enter="sub(val)" ref="ruleFormRef" :rules="rules" :model="form">
      <el-form-item label=" " prop="name">
        <el-input class="autofocus inp" v-model="val" maxlength="30" autocomplete="off" />
      </el-form-item>
    </el-form>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="close()">取消</el-button>
        <el-button type="primary" @click="sub(val)">
          确定
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>
<style scoped>

</style>