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
    default:'调整类目',
  },
  val:{
    type:[String, Number],
    default:'',
  },
  item:{
    type: Object,
    default: () => null,
  },
  dataSource:{
    type: Array,
    default: () => [],
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
      init(props.item)
    }
    dialogFormVisible.value = n;
  }
);


const close = () => {
   emits('update:modelValue', false)
}

const sub = (params) => {
  if ((!curDomid.value && (!curcateData.value || curcateData.value.id === undefined))||(!curcateData1.value || curcateData1.value.id === undefined)){ 
    window._this.$message('请选择当前类目以及目标类目','warning')
    return false
  };
   emits('subfn', {
    curcateData:curcateData.value,
    curcateData1:curcateData1.value,
    curDomid:curDomid.value
   })
}

const curcateData = ref({});
const curcateData1 = ref({});

const curDomid = ref("");
const curDomname = ref("");
const init = (item) => {
  curDomid.value = "";
  if (item) {
    curDomid.value = item.id;
    curDomname.value = item.category_id
      ? findNodeById(props.dataSource, item.category_id).name
      : "未分类";
  }
  curcateData1.value = {};
  curcateData.value = {};

  dialogFormVisible.value = true;
};

function findNodeById(tree, id) {
  for (let i = 0; i < tree.length; i++) {
    if (tree[i].id == id) {
      return tree[i];
    }
    if (tree[i].children && tree[i].children.length > 0) {
      let node = findNodeById(tree[i].children, id);
      if (node) {
        return node;
      }
    }
  }
  return null;
}

</script>
<template>
  <el-dialog align-center v-model="dialogFormVisible" :title="title" @closed="close" width="900">
    <div class="treedialog">
      
      
      <div v-if="curDomid" class="treebox">
        <div class="title">
          当前类目： {{ curDomname || "未分类" }}
        </div>
        <div class="treecontent">
        </div>
      </div>

      <div v-else class="treebox">
        <div class="title">
          当前类目： {{ curDomid
          }}<span v-if="curcateData">{{ curcateData.name }}</span
          ><span v-else class="empty">请选择当前类目</span>
        </div>
        <div class="treecontent">
          <el-scrollbar>
            <el-tree
          style="width:100%"
          :data="dataSource"
          @current-change="
            (data) => {
              curcateData = data;
            }
          "
          :current-node-key="curcateData.id"
          node-key="id"
          empty-text="暂无商品类目信息"
          highlight-current
          default-expand-all
          :expand-on-click-node="false"
        >
          <template #default="{ node, data }">
            <div class="custom-tree-node">
              <span class="ellipsis">{{ data.name }}</span>
            </div>
          </template>
        </el-tree>
          </el-scrollbar>
        </div>
        
      </div>

      <div class="treebox">
        <div class="title">
          目标类目：<span v-if="curcateData1">{{ curcateData1.name }}</span
          ><span v-else class="empty">请选择目标类目</span>
        </div>
        <div class="treecontent">
          <el-scrollbar>
        <el-tree
          style="width:100%"
          :data="dataSource"
          node-key="id"
          :current-node-key="curcateData1.id"
          @current-change="
            (data) => {
              
              curcateData1 = data;
            }
          "
          empty-text="暂无商品类目信息"
          highlight-current
          default-expand-all
          :expand-on-click-node="false"
        >
          <template #default="{ node, data }">
            <div class="custom-tree-node">
              <span class="ellipsis">{{ data.name }}</span>
            </div>
          </template>
        </el-tree>
      </el-scrollbar></div>
      </div>
    </div>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="close()">取消</el-button>
        <el-button type="primary" @click="sub()">
          确定
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>
<style scoped>

.treedialog {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  margin: -16px -20px;
}

.treedialog .title {
  text-align: left;
    padding: 20px;
    font-weight: bold;
    border-bottom: 1px solid var(--el-border-color);
}

.treedialog .empty {
  color: #ccc;
  font-weight: normal;
}

.treedialog .treebox {
  width: 50%;
  border-right: 1px solid var(--el-border-color);
  box-sizing: border-box;
}
.treedialog .treebox:nth-last-child(1) {
  border:none;
}
.treecontent{
  height: 500px;
}
</style>