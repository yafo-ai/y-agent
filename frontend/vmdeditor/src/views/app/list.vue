<script setup>
import {
  ref,
  nextTick,
  shallowRef,
  getCurrentInstance,
  onActivated,
  reactive,
  watch,

} from "vue";
import { onBeforeRouteLeave, useRoute, useRouter } from "vue-router";
import { useStore } from "vuex";
import {
  promptsDelete, prompts, promptstree,
  promptstreedelete,
  promptstreeadd,
} from "@/api/api";
import { goback, getTime } from "@/components/comp.js";
import tscEdit from "@/views/app/edit.vue";
import icon from "@/components/icon.vue"
import { copyData } from "@/assets/utils/util";
import { cloneDeep } from "lodash"; // 引入lodash库的cloneDeep方法进行深拷贝
const route = useRoute();
const router = useRouter();

const props = defineProps({
  proType: {
    type: [String, Number],
    default: () => "",
  },
  curflowid: {
    type: [String, Number],
    default: "",
  },
  curdataid: {
    type: [String, Number],
    default: "",
  },
  nodes: {
    type: [Array],
    default: () => [],
  },
  edges: {
    type: [Array],
    default: () => [],
  },
  nodeid: {
    type: String,
    default: "",
  },
  isCheck: {
    type: [Boolean],
    default: () => false,
  },
  checkList: {
    type: [Array],
    default: () => [],
  },
});

watch(
  () => props.checkList,
  (n) => {
    initChecked();
  }
);

const initChecked = () => {
  let arr = pagelist.value;
  arr.forEach((item) => {
    item.checked = false;
    props.checkList.forEach((item1) => {
      if (item.id == item1.id) {
        item.checked = true;
      }
    });
  });
  pagelist.value = arr;
};

const store = useStore();
let { proxy } = getCurrentInstance();
const dialogFormVisible1 = ref(false);

// 创建文件夹

let pagelist = ref([]);

const total = ref(0);

const page = ref(1);
const pagesize = ref(36);

if (route.query.page) {
  page.value = parseInt(route.query.page);
}
if (route.query.pagesize) {
  pagesize.value = parseInt(route.query.pagesize);
}
const searchParams = reactive({
  page: page.value || 1,
  pagesize: pagesize.value || 30,
  type: props.proType || undefined,
  prompt_type_id: props.proType || null,
});

copyData(searchParams, route.query, "prompt_type_id");
const search = (type) => {
  if (type == 'init') {
    searchParams.page = 1;
    searchParams.pagesize = pagesize.value || 30;
  }


  prompts(searchParams).then((res) => {
    let arr = res.rows || [];
    if (props.proType) {
      arr = res || [];
      total.value = 0;
    } else {
      total.value = res.total_records;
    }
    pagelist.value = arr;
    initChecked();
  });
  if (type != "noquery" && route.path == "/app/list") {
    let query = { ...route.query, ...searchParams };
    router.replace({ path: route.path, query: query });
  }
};

search("noquery");

const emits = defineEmits(["subfn"]);
const checkItem = (item) => {
  
  if (props.proType || props.isCheck) {
    item.checked = !item.checked;
    console.log(item);
    emits("subfn", [cloneDeep(item)]);
  } else {
    openDialog(item);
  }
};

const openDialog = async (item) => {
  resetForm();
  if (item) {
    setFormValues(item);
  }
  dialogFormVisible1.value = true;
};

const resetForm = () => {
  form1.id = "";
  form1.name = "";
  form1.content = "";
  form1.prompt_type_id = searchParams.prompt_type_id || null;
};

const setFormValues = (item) => {
  form1.id = item.id;
  form1.name = item.name;

  form1.content = item.content;
  form1.prompt_type_id = item.prompt_type_id || null;
};

const del = (id) => {
  _this.$confirm("此操作将永久删除该知识库, 是否继续?").then((res) => {
    promptsDelete({ id }).then((res) => {
      _this.$message("删除成功");
      search();
    });
  });
};

// 创建知识库
const form1 = reactive({
  name: "",
  content: "",
  id: undefined,
  prompt_type_id: null,
});

const tableRef = ref(null);

const dataSource = ref([]);
const treeSelect = ref(null);
const checkType = async (item) => {
  console.log(item);

  searchParams.prompt_type_id = item.id;
  search("init");
};

const searchCate = (params) => {
  promptstree()
    .then(async (res) => {
      dataSource.value = res || [];
      await nextTick();
      treeSelect.value.setCurrentKey(parseInt(searchParams.prompt_type_id));
    })
    .catch((err) => {
      // if (err.response.data && err.response.data.detail == "知识库类目不存在") {
      //   dataSource.value = [];
      // }
    });
};
searchCate();
const isShowAdd = ref(false);
const addparam = reactive({ name: "", id: 0, note: "", pid: 0 });



// 使用函数
const addTypefn = async (item, type) => {
  addparam.pid = item.pid || 0;
  addparam.id = item.id || 0;
  addparam.name = item.name || "";
  addparam.note = item.note || "";
  if (type == "child") {
    // 添加子节点
    addparam.pid = item.id;
    addparam.name = "";
    addparam.note = "";
    addparam.id = undefined;
  }
  isShowAdd.value = true;
  setTimeout(() => {
    inputRef.value.focus();
  }, 500);
};

const delTypefn = (item) => {
  _this.$confirm("确定要删除所选数据?").then(() => {
    promptstreedelete({ id: item.id }).then((res) => {
      _this.$message("删除成功");
      searchCate();
    });
  });
};
const inputRef = ref(null);
const subaddfn = () => {


  if (!addparam.name) {
    inputRef.value.focus();
    return false;
  }
  promptstreeadd(addparam)
    .then((res) => {

      isShowAdd.value = false;
      searchCate();
      _this.$message("操作成功");
    })
    .catch((err) => { });
};

const subAddtscEditFn = (params) => {
  console.log(params);
  findAndAddCategory(dataSource.value, params.prompt_type_id || 0, (category) => {
    params.prompt_type_name = category.name;
  })
  if (props.isCheck) {
    // 如果是弹框选择  直接自动选中
    checkItem(params)
  }
  search();
  dialogFormVisible1.value = false;
}

const findAndAddCategory = (categories, parentId, fn) => {
  // 递归查找类型名称
  categories.forEach((category) => {
    if (category.id === parentId) {
      fn && fn(category);
      return true;
    }

    if (category.children && category.children.length > 0) {
      findAndAddCategory(category.children, parentId, fn);
    }
  });
};

</script>

<template>
  <div :class="{ 'component': (props.proType || props.isCheck) }" class="c-titlebox">
    <span class="title">提示词</span>
    <el-button @click="openDialog()" type="primary" size="small">新建</el-button>
  </div>

  <div class="c-bodybox" :class="{ 'component': (props.proType || props.isCheck) }">
    <div class="catebox leftbox">
      <div class="topbtns">
        <span class="title">提示词分类</span>
        <el-button @click="checkType({ id: undefined })" class="on noradius" plain>
          <span class="iconfont icon-anniu-zhankai"></span>
          查看全部
        </el-button>

      </div>
      <div class="contain">
        <el-scrollbar>
          <div class="el-tree el-tree--highlight-current" role="tree" style="width: 100%">
            <div class="el-tree-node" :class="{ 'is-current': searchParams.prompt_type_id == 0 }">
              <div class="el-tree-node__content">
                <div @click="checkType({ id: 0 })" style="padding-left: 35px" class="custom-tree-node">
                  <div class="item">
                    未分类
                  </div>
                </div>
              </div>
            </div>
          </div>
          <el-tree ref="treeSelect" style="width: 100%" :data="dataSource" node-key="id" empty-text="暂无数据"
            highlight-current
            :current-node-key="searchParams.prompt_type_id ? parseInt(searchParams.prompt_type_id) : undefined"
            default-expand-all @node-click="checkType" :expand-on-click-node="false">
            <template #default="{ node, data }">
              <div :title="data.name" class="custom-tree-node">
                <div class="item">
                  <p class="ellipsis">{{ data.name }}</p>
                </div>
                <div class="btns">
                  <span title="添加子类目" @click.stop="addTypefn(data, 'child')"
                    class="iconfont icon-shuzhuang-tianjia"></span>
                  <span title="修改" @click.stop="addTypefn(data)" class="iconfont icon-xiugai"></span>
                  <span title="删除类目" @click.stop="delTypefn(data)" class="iconfont icon-shuzhuang-shanchu"></span>
                </div>
              </div>
            </template>
          </el-tree>
        </el-scrollbar>
      </div>

      <div class="botbtns">
        <el-button style="width: 100%;" plain class="on noradius" @click="addTypefn({ id: 0 })"><span
            class="iconfont icon-liebiao-xinzeng"></span> 新增分类</el-button>
      </div>
    </div>

    <div class="scrollbox rightbox">
      <el-scrollbar :max-height="store.getters.innerHeight - 186" ref="tableRef">
        <div class="contain ">
          <div class="c-cardbox">
            <div v-if="pagelist.length < 1" class="c-emptybox">
              <icon type="empzwssjg" width="100" height="100"></icon>
              该分类下暂无数据
            </div>
            <div v-for="item in pagelist" @click="checkItem(item, index)" class="item c-pointer" :key="item.id"
              :class="{ active: item.checked }">
              <el-popover :width="160">
                <template #reference>
                  <span class="iconfont icon-gengduo c-cardbtn-icon"></span>
                </template>
                <template #default>
                  <div @click.stop class="c-cardbtn-btns">


                    <div @click="openDialog(item)" class="item">
                      <span class="name">修改</span>
                    </div>
                    <div @click="del(item.id)" class="item">
                      <span class="name">删除</span>
                    </div>
                  </div>
                </template>
              </el-popover>
              <div class="top ellipsis">
                {{ item.prompt_type_name }}
              </div>
              <div class="title ellipsis">
                {{ item.name }}
              </div>
              <div class="intro">
                <el-popover v-if="item.content" placement="bottom" :width="416" trigger="hover">
                  <template #reference>
                    <div class="ellipsis3">
                      <span class="base_name">{{ item.content }}</span>
                    </div>
                  </template>

                  <div style="margin: 0 -20px;">
                    <el-scrollbar max-height="400">
                      <div v-html="item.content.replace(/\n/g, '<br>')" style="margin:0 20px;">
                      </div>
                    </el-scrollbar>
                  </div>
                </el-popover>
              </div>
            </div>

          </div>

        </div>
      </el-scrollbar>

      <div v-if="total > 0" style="padding-right: 20px;" class="c-pagination">
        <el-pagination :hide-on-single-page="false" background :page-size="searchParams.pagesize"
          :current-page="searchParams.page" @size-change="
            (val) => {
              searchParams.pagesize = val;
              searchParams.page = Math.min(Math.ceil(total / searchParams.pagesize), searchParams.page);
              search();
            }
          " @current-change="
            (val) => {
              searchParams.page = val;
              tableRef && tableRef.scrollTo(0, 0);
              search();
            }
          " :page-sizes="[36, 50, 100, 1000]" layout="total,sizes,jumper,prev, pager, next" :total="total" />
      </div>
    </div>
  </div>

  <tscEdit v-model="dialogFormVisible1" @subfn="subAddtscEditFn" :curflowid="props.curflowid" :curdataid="props.curdataid" :nodeid="nodeid" :nodes="nodes" :edges="edges" :item="form1">
  </tscEdit>


  <el-drawer v-model="isShowAdd" :title="addparam.id ? '修改分类' : '新增分类'" size="600px">
    <div class="formbox">
      <el-form ref="formRef" style="width: 100%;" :model="addparam" @submit.native.prevent
        @keyup.native.enter.prevent="subaddfn()" label-width="auto" class="demo-dynamic">
        <el-form-item prop="name" label=" " :rules="[
          {
            required: true,
            message: '请输入分类名称',
            trigger: 'blur',
          },
        ]">
          <el-input v-model="addparam.name" ref="inputRef" placeholder="分类名称" />
        </el-form-item>
      </el-form>
    </div>
    <div class="dialog-footer">
      <el-button plain @click="isShowAdd = false"> 取消 </el-button>
      <el-button type="primary" @click="subaddfn()"> 确定 </el-button>
    </div>
  </el-drawer>

</template>

<style scoped>
.c-titlebox.component {
  position: fixed;
  top: 6px;
  left: 10%;
  padding-left: 20px;
}

.c-bodybox.component {
  margin: -20px;
}

.formbox {
  display: block;
  height: calc(100% - 100px);
}

.catebox .addbtn {
  padding-right: 5px;
}

.catebox .title {
  text-align: left;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.catebox .btns {
  padding-right: 5px;
}

.catebox .tip {
  font-size: 12px;
  color: #ccc;
}

.scrollbox {
  height: auto;
}

.icon-zhishiku {
  color: var(--el-color-primary);
}

.icon-zhishikuguanli {
  color: var(--el-color-success);
}

.titlebox .title {
  background: linear-gradient(to bottom right,
      #1237b3,
      #3370ff 40%,
      #4e83fd 80%,
      #85b1ff);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.titlebox {
  text-align: left;
  font-size: 22px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding: 10px 30px;
  font-weight: bold;
}

.icon-qitaleidengguang {
  font-size: 36px;
  font-weight: bold;
  color: #1948e7;
}

.topbox {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-right: 60px;
}

.listbox {
  display: block;
  text-align: center;
}

.listbox .icon-qitaleidengguang {
  font-size: 20px;
}

.pagelistbox {
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  flex-wrap: wrap;
  padding: 0;
}

.pagelistbox .item {
  width: 400px;
  height: 150px;
  background: #fff;
  border-radius: 10px;
  box-sizing: border-box;
  margin: 0 10px 20px 10px;
  cursor: pointer;
  border: 1px solid #eee;
  padding: 10px 10px 40px 20px;
  position: relative;
}

.pagelistbox .item.active {
  border: 1px solid var(--el-color-success);
}

.pagelistbox .item:hover {
  border: 1px solid var(--el-color-primary);
}

.pagelistbox .item .c-dataset-btns {
  text-align: left;
}

.namebox {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.namebox .rbox {
  flex-shrink: 0;
}

.namebox .lbox {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  font-size: 16px;
}

.namebox .lbox .iconfont {
  flex-shrink: 0;
  font-size: 20px;
  margin-right: 5px;
}

.namebox .lbox .name {
  text-align: left;
  display: inline-block;
  width: 310px;
}

.name {
  word-break: break-all;
}

.introbox {
  word-break: break-all;
  text-align: left;
  color: #999;
  margin-top: 8px;
  font-size: 12px;
}

.botbox {
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: absolute;
  left: 20px;
  bottom: 10px;
  right: 20px;
  height: 30px;
  font-size: 14px;
}

.botbox .rbox .bitem {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  background: var(--chakra-colors-myGray-100);
  border: 1px solid var(--chakra-colors-myGray-200);
  border-radius: var(--chakra-radii-md);
  padding: 0px 10px;
}

.botbox .rbox .bitem .iconfont {
  color: #333;
}

.icon-shugui {
  color: var(--chakra-colors-primary-600);
  font-size: 20px;
}
</style>

<style>
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
