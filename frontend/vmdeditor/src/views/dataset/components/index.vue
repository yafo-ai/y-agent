<script setup>
import {
  ref,
  nextTick,
  shallowRef,
  getCurrentInstance,
  onActivated,
  reactive,
} from "vue";
import { useRoute, useRouter, onBeforeRouteLeave } from "vue-router";
import { useStore } from "vuex";
import {documentsGet} from "@/api/api";
const route = useRoute();
const router = useRouter();

let pagelist = ref([]);


const resData = ref(null);

documentsGet({ id: route.query.did }).then((res) => {
  resData.value = res;

    pagelist.value = res.nodes;
  });

const goback = () => {
  let query = { ...route.query };
  query.it = 0;
  router.replace({ path: route.path, query: query });
};

const dialogFormVisible1 = ref(false);
const mkData = ref('');
const curid = ref('');
const showDialog = (item) => {
  curid.value = item.node_id;
  mkData.value = item.text;
  dialogFormVisible1.value = true;
}


</script>

<template>
  <div class="topbox">
    <span></span>
    <span @click="goback()" class="c-iconbackbox">
          <span class="iconfont icon-fuwenben-chexiao"></span> 返回
        </span>
  </div>
  <div class="pageContain">
  <el-scrollbar>


  <div class="pagelistbox c-cardbox">

    <div v-for="(item, index) in pagelist"
      :key="item.node_id"
      @click="showDialog(item)" class="item">
          
          <div class="top ellipsis">
            {{ resData.category_name }}
          </div>
          <div class="title ellipsis">
            {{ item.node_id }}
          </div>
          <div class="intro ellipsis3">
            <span :title="item.text" class="note" v-if="item.text">
              {{ item.text }}
            </span>
          </div>
        </div>
    
   
    
  </div>
  </el-scrollbar>
  </div>
<el-dialog align-center v-model="dialogFormVisible1" :title="curid" width="800">
    <div class="dialogbox">
      <el-scrollbar>

      <v-md-preview :text="mkData"></v-md-preview>
      </el-scrollbar>
    </div>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="dialogFormVisible1 = false">关闭</el-button>
       
      </div>
    </template>
  </el-dialog>
    
 
</template>
<style>
.dialogbox{
  height: 600px;
  margin: -16px -20px;
  text-align: left;
}
.c-dataset-btns .item {
  display: flex;
  width: 100%;
  text-align: left;
  cursor: pointer;
  padding: 10px;
  box-sizing: border-box;
  border-radius: 5px;
  font-size: 14px;
  align-items: center;
  justify-content: flex-start;
}
.c-dataset-btns .item .iconfont {
  margin-right: 5px;
}
.c-dataset-btns .item:hover {
  background-color: var(--el-fill-color-light);
  color: var(--el-color-primary);
}
.c-dataset-btns .item.err:hover {
  background-color: var(--el-color-danger-light-9);
  color: var(--el-color-danger);
}
</style>
<style scoped>
.backbox {
  font-size: 16px;
}
.icon-fanhui {
  font-size: 26px;
  margin-right: 5px;
}


.titlebox {
  text-align: left;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding-bottom: 10px;
}
.titlebox .iconfont{
  font-size: 22px;
}
.icon-zhishi {
  font-size: 36px;
  font-weight: bold;
  color: #1948e7;
}
.topbox {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-right: 0px;

}
.listbox {
  display: block;
  text-align: center;
}

.listbox .icon-zhishi {
  font-size: 20px;
}
.pageContain{
  position: relative;
  height: calc(100% - 60px);
}
.c-cardbox .item{
  cursor: pointer;
}
</style>
