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
    default:'请输入文件夹名称',
  },
  name:{
    type:[String, Number],
    default:() => '',
  },
  maxlength:{
    type:[String, Number],
    default:() => 30,
  },
  caption:{
    type:[String, Number],
    default:() => '',
  },
  modelValue: {
    type:Boolean,
    default:() => false,
  },
});
const emits = defineEmits(['subfn','update:modelValue'])
const route = useRoute();
const router = useRouter();
const store = useStore();

const dialogFormVisible = ref(false);
const inpval = ref('');
const caption = ref('');

onMounted(()=>{
  dialogFormVisible.value = props.modelValue;
  inpval.value = props.name;
  caption.value = props.caption;
  focus();
})

watch(
  () => props.name,
  (n) => {
    
    inpval.value = n;
  }
);
const maxlength = ref(props.maxlength);
watch(
  () => props.maxlength,
  (n) => {
    
    maxlength.value = n;
  }
);
watch(
  () => props.caption,
  (n) => {
    caption.value = n;
  }
);

watch(
  () => props.modelValue,
  (n) => {
    dialogFormVisible.value = n;
  }
);


const close = () => {
   emits('update:modelValue', false)
}

const sub = () => {
  if(inpval.value == ''){
    focus();
    return false;
  }
   emits('subfn', {name:inpval.value,caption:caption.value})
}

const focus = () => {
  setTimeout(() => {
    if(document.querySelectorAll(".c-focus-inp input")[0]){
      document.querySelectorAll(".c-focus-inp input")[0].focus();
    }
  }, 100);
}

</script>
<template>
  <el-dialog align-center v-model="dialogFormVisible" :title="title" @closed="close" width="500">
    <slot></slot>
    <el-form @submit.native.prevent label-width="100" @keyup.native.enter="sub(inpval)" ref="ruleFormRef">
      <el-form-item label="名称">
        <el-input class="c-focus-inp" v-model="inpval" :maxlength="maxlength" autocomplete="off" />
      </el-form-item>
      
    </el-form>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="close()">取消</el-button>
        <el-button type="primary" @click="sub(inpval)">
          确定提交
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>
<style scoped>

</style>