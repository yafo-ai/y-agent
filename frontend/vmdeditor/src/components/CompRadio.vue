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
  list:{
    type:Array,
    default:() => [],
  },
  modelValue: {
    type:[String, Number],
    default:() => 0,
  },
});
const emits = defineEmits(['update:modelValue'])
const route = useRoute();
const router = useRouter();
const store = useStore();

const curindex = ref(0);

watch(
  () => props.modelValue,
  (n) => {
    console.log(n);
    curindex.value = n;
  }
);


const change = (index) => {
  emits('change', index)
  curindex.value = index;
   emits('update:modelValue', index)
}





</script>
<template>
  <div class="zsktypebox">
      <div v-for="(item,index) in list" class="item" @click="change(index)" :class="{on:index == curindex}">
        <span :class="item.icon"></span>
        <div class="name">
          {{item.name}}
          <div class="intro">{{item.intro}}</div>
        </div>
        
        <span class="radiobtn"></span>
      </div>
      
    </div>
</template>
<style scoped>
.zsktypebox .item .name{
  width: calc(100% - 50px);
}
.zsktypebox .item{
  display: flex;
  width: 100%;
  position: relative;
  text-align: left;
  box-sizing: border-box;
  align-items: center;
  justify-content: space-between;
  padding: 10px 10px;
  cursor: pointer;
  border: 1px solid var(--chakra-colors-gray-200);
  background: var(--chakra-colors-myWhite-300);
  border-radius: 10px;
  margin-bottom: 10px;
}

.zsktypebox .item .iconfont{
  display: inline-block;
  text-align: center;
    width: 30px;
  flex-shrink: 0;
}
.zsktypebox .item .radiobtn{
  display: block;
  background: #fff;
  border-radius: 10px;
  border: 2px solid #ccc;
  width: 16px;
  height: 16px;
  box-sizing: border-box;
  flex-shrink: 0;
  transition: all 0.3s;
}
.zsktypebox .item:hover,
.zsktypebox .item.on{
  background: var(--chakra-colors-primary-50);
  border-color: var(--chakra-colors-primary-400);
}
.zsktypebox .item.on .radiobtn{
  border: 5px solid var(--chakra-colors-primary-600);
}
.icon-shugui{
  color: var(--chakra-colors-primary-600);
  font-size: 20px;
}
.zsktypebox .icon-shugui{
  font-size: 22px;
  margin-left: -2px;
}
</style>