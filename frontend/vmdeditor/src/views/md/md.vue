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
});
const emit = defineEmits(['subfn','update:modelValue'])
const route = useRoute();
const router = useRouter();
const store = useStore();

const text = ref('');

</script>
<template>
<div class="mdbox">
 <v-md-editor v-model="text" height="100%"></v-md-editor>
 </div>
</template>
<style scoped>
.mdbox{
  position: relative;
  width: 90%;
  height: 80%;
  margin: 10px auto;
}
</style>