<script setup>
import { ref, nextTick, onMounted, reactive,watch } from "vue";
import { useStore } from "vuex";
import { useRoute, useRouter } from "vue-router";
import { Search } from '@element-plus/icons-vue'
const props = defineProps({
  list: {
    type: Array,
    default: () => [],
  },
});
const emit = defineEmits(['subfn','update:modelValue'])
const route = useRoute();
const router = useRouter();
const store = useStore();

const meslist = ref([]);

watch(
  () => props.list,
  (n) => {
    meslist.value = n;
  }
);


const close = () => {
   emits('update:modelValue', false)
}

const sub = (params) => {
   emits('subfn', params)
}

</script>
<template>
  
</template>
<style scoped>

</style>