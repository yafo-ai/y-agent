<script setup>
import { ref} from "vue";
const props = defineProps({
  
  title:{
    type:[String, Number],
    default:'新建文件夹',
  }
});


</script>
<template>
  <div class="emptybox">
    <div class="empty">
      <div class="empty-icon"><span class="iconfont icon-shujukong"></span></div>
      <div class="empty-title">{{ title }}</div>
    </div>
  </div>
</template>
<style scoped>
.emptybox{
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.empty-icon{
  border: 1px dashed #ccc;
  border-radius: 25px;
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
}
.icon-shujukong{
  font-size: 25px;
  color: #7b838b;
}
.empty-title{
  text-align: center;
  margin: 10px auto;
}
</style>