<script setup>
import { ref, nextTick, onMounted, reactive,watch } from "vue";
import { useStore } from "vuex";
import { useRoute, useRouter } from "vue-router";
import { Search } from '@element-plus/icons-vue'
import { cloneDeep } from "lodash"; // 引入lodash库的cloneDeep方法进行深拷贝
import Sortable from 'sortablejs';
const emits = defineEmits(['subfn','update:modelValue'])
const route = useRoute();
const router = useRouter();
const store = useStore();

const props = defineProps({
  list: {
    type: [Array],
    default: () => [],
  },
  iszdy: {
    type: [Boolean],
    default: () => false,
  },
  width: {
    type: [String],
    default: () =>'310px',
  },
  searchLocalKey:{
    type: [String],
    default: () =>'s-' + Date.now(),
  },
  params:{
    type: [Object],
    default: () => null,
  },
});

const dialogFormVisible = ref(false);

watch(
  () => props.list,
  async (n, old) => {
    console.log(n,old)
    if (n !== old && n) {
      getList()
    }
  },
  {
    deep: true, // 开启深度监听
  }
);


const close = () => {
   emits('update:modelValue', false)
}

const sub = () => {
  let params = {}
  checkList.value.forEach((item)=>{
    params[item.prop] = item.value;
  })
  console.log(params)
   emits('subfn', {
    searchParams:params,
    checkList:checkList.value,
    noCheckList:noCheckList.value
   })
}

const checkList = ref([])
const noCheckList = ref([])
const searchList = ref([])
const init = (type) => {
  checkList.value = []
  noCheckList.value = []
  searchList.value.forEach((item,index) => {
    if (item.check) {
      if(props.params && props.params[item.prop] !== undefined && type != 'reset'){
        item.value = props.params[item.prop];
      }
      checkList.value.push(item);
    }else{
      noCheckList.value.push(item)
    }
  });
};

const changeCheck = (curitem) =>{
  searchList.value.forEach((item,index) => {
    // 根据关键字查询 设置是否选中
    if (item.prop ==curitem.prop) {
      item.checked = !item.checked
    }
  });
  init()
}

const reset = () =>{
  searchList.value.forEach((item,index) => {
    if(item.valType == 'number'){
      item.value = undefined;
    }else if(item.valType == 'array'){
      item.value = [];
    }else{
      item.value = "";
    }
  });
  init('reset')
}


const check = () => {
  // 设置自定义选项
  checkList.value = curchecklist.value;
  localStorage.setItem(props.searchLocalKey, JSON.stringify(checkList.value));
  dialogFormVisible.value = false;
}

const getList = () =>{
  console.log(props)
  let proplist = cloneDeep(props.list)
  let list = localStorage.getItem(props.searchLocalKey);
  if (list) {
    try {
      let checklist = JSON.parse(list);
      proplist.forEach((item,index) => {
        if (checklist.find((it) => it.prop == item.prop)) {
          item.checked = true;
        } else {
          item.checked = false;
        }
      });
    } catch (error) {}
  }

  searchList.value = proplist;
  init()
}

getList()

const listRef = ref(null);
const curchecklist = ref([])
const isDragging = ref(false);
const initDrag = async () =>{
  dialogFormVisible.value=true;
  curchecklist.value = cloneDeep(checkList.value);
  if(isDragging.value) return;

  await nextTick();
  if (listRef.value) {
    isDragging.value = true;
    new Sortable(listRef.value, {
      animation: 150,
      onEnd: (event) => {
        console.log(event)
        console.log(curchecklist.value)
        const movedItem = curchecklist.value.splice(event.oldIndex, 1)[0];
        curchecklist.value.splice(event.newIndex, 0, movedItem);
      }
    });
  }
}

</script>

<!--  
    <Search :list="searchList" :params="searchParams" searchLocalKey="s-userlist"
      @subfn="(param) => { searchParams = { ...searchParams, ...param.searchParams }; search(); }">
      <el-button @click="addfn()" plain style="margin-left: 12px;">{{
        searchParams.active == 1 ? "新增用户" : "新增角色"
      }}</el-button>
    </Search> -->
<template>
  <div class="com-search-box">
  
    <div class="contain">
    <div class="items">
      <div v-for="item in checkList" :style="{width:props.width}" class="item">
        <div class="label">{{ item.label }}</div>
        <div class="inpbox">
          <template v-if="item.type == 'input'">
            <el-input size="small" v-model="item.value" autocomplete="off" :clearable="item.clearable" />
          </template>
        </div>
      </div>
    </div>
  </div>
  <div class="btns">
      <el-button type="primary" @click="sub()">查询</el-button>
      <el-button type="primary" plain @click="reset()">重置</el-button>
      <slot></slot>
  </div>
  </div>
  <el-dialog align-center v-model="dialogFormVisible" title="自定义筛选" @closed="close" width="576">
    <div class="dialogbox">
      <div class="c-title-l3">
        我的选择 <span class="c-tips">拖拽可以排序</span>
      </div>
        <div ref="listRef" class="items checkList">
          <div v-for="(item,index) in curchecklist" :key="item.prop" class="item">{{ item.label }}
            <div @click="noCheckList.push(item);curchecklist.splice(index,1);" class="btn">
              <span class="iconfont icon-guanbi"></span>
            </div>
          </div>
        </div>
      <div class="c-title-l3">
        其他筛选 <span class="c-tips">点击添加筛选</span>
      </div>
      <div class="noCheckList items">
        <div v-for="(item,index) in noCheckList" class="item">{{ item.label }}
          <div @click="curchecklist.push(item);noCheckList.splice(index,1);" class="btn">
              <span class="iconfont icon-jiahao1"></span>
            </div>
        </div>
      </div>
    </div>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="close()" plain>取消</el-button>
        <el-button type="primary" @click="check()">
          确定
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>
<style scoped>
.com-search-box{
  display: block;
  width: 100%;
  margin-top: 24px;
}
.com-search-box .contain{
  display: block;
  width: 100%;
  overflow: hidden;
  height: 72px;
}
.com-search-box .items{
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: flex-start;
}
.com-search-box .items .item{
  width: 306px;
  margin: 0 16px 16px 0;
}
.com-search-box .items .item .label{
  font-weight: 400;
  font-size: 14px;
  color: #333333;
  line-height: 20px;
  text-align: left;
  font-style: normal;
  padding-bottom: 8px;
}
.com-search-box .btns{
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 24px 0;
}

.dialogbox .items{
text-align: left;
margin-right: -16px;
margin-top: 8px;
}
.dialogbox .item{
  display: inline-block;
  min-width: 120px;
  line-height: 40px;
  background: #f4f4f4;
  border-radius: var(--el-border-radius-base);
  text-align: center;
  margin: 0 16px 16px 0;
  position: relative;
  box-sizing: border-box;
}
.dialogbox .item .btn{
  position: absolute;
  right: 0;
  top: 0;
  display: flex;
  align-items: flex-start;
  justify-content: flex-end;
  padding: 4px 4px 10px 10px;
  cursor: pointer;
}
.dialogbox .item .btn .iconfont{
  font-size: 12px;
  line-height: 12px;
}
.dialogbox .item .btn:hover .iconfont{
  color: var(--el-color-primary);
}
.dialogbox .checkList .item{
  background: #f4f4f4;
  cursor: move;
}
.dialogbox .noCheckList .item{
  border-radius: var(--el-border-radius-base);
  border: 1px solid #E6E6E6;
  background: #fff;
}
</style>