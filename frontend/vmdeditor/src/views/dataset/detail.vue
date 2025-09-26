<script setup>
import {
  ref,
  nextTick,
  onMounted,
  reactive,
  watch,
  getCurrentInstance,
} from "vue";
import { useStore } from "vuex";
import { useRoute, useRouter } from "vue-router";
import Wbsj from "./components/wbsj.vue";
import Index from "./components/index.vue";
import ChangeTree from "@/components/changeTree.vue";
import {
  knowledgesGet,
  knowledges,
  categories,
  categoriesAdd,
  categoriesDelete,
  documents,
  documentsDelete,
  documentsDeleteIndex,
  documentsConverter,
  documentsMarkdown,
  documentsMove,
  similaritysearch,
  download,
  updatesxl,
} from "@/api/api";
import Add from "./components/add.vue";
import xltest from "@/components/xltest.vue";
import { Delete, Plus, Eleme } from "@element-plus/icons-vue";
import CompApp from "@/views/app/list.vue";
import { goback, getTime } from "@/components/comp.js";
import icon from "@/components/icon.vue"
const route = useRoute();
const router = useRouter();
const store = useStore();
const detailData = ref(null);
const dataSource = ref([]);

let searchParams = reactive({
  knowledgebase_id: route.query.id,
  category_id: undefined,
  keyword: undefined,
  page: 1,
  pagesize: 30,
});

onMounted(async () => {
  knowledgesGet({ id: route.query.id }).then((res) => {
    detailData.value = res;
    document.title = detailData.value.name;
  });
  searchParams.knowledgebase_id = route.query.knowledgebase_id || undefined;
  searchParams.keyword = route.query.keyword || undefined;
  searchParams.category_id =
    route.query.category_id === undefined
      ? undefined
      : parseInt(route.query.category_id);
  searchParams.page = parseInt(route.query.page) || 1;
  searchParams.pagesize = parseInt(route.query.pagesize) || 30;
  search("noquery");
  searchCate();
});

watch(
  () => route.query.it,
  (newval, oldval) => {
    //要执行的方法
    if (newval == 0 && (oldval == 1 || oldval == 2)) {
      search("noquery");
    }
  },
  { immediate: true, deep: true }
);

const total = ref(0);
const list = ref([]);
const search = (type) => {
  if (type == "init") {
    searchParams.page = 1;
  }

  searchParams.knowledgebase_id = route.query.id;
  documents(searchParams).then((res) => {
    total.value = res.total_records;
    list.value = res.rows;
  });

  if (type != "noquery") {
    let query = { ...route.query, ...searchParams };
    router.replace({ path: route.path, query: query });
  }
};
const treeSelect = ref(null);
const isShowAdd = ref(false);
const pid = ref(null);
const curid = ref(null);
const curcate = reactive({
  id: "",
  name: "",
  caption: "",
});

const editfn = (data) => {
  pid.value = data.pid;
  curcate.id = data.id;
  curcate.name = data.name;
  curcate.caption = data.caption;
  isShowAdd.value = true;
};

const del = (id) => {
  _this.$confirm("确定要删除该类目吗？").then(() => {
    categoriesDelete({ id }).then(() => {
      _this.$message("删除成功");
      searchCate();
    });
  });
};

const addfn = (data) => {
  pid.value = data.id;
  curcate.id = "";
  curcate.name = "";
  curcate.caption = "";
  isShowAdd.value = true;
};

const searchCate = (params) => {
  categories({
    knowledgebase_id: route.query.id,
  })
    .then(async (res) => {
      dataSource.value = res || [];
      await nextTick();
      treeSelect.value.setCurrentKey(parseInt(searchParams.category_id));
    })
    .catch((err) => {
      if (err.response && err.response.data && err.response.data.detail == "知识库类目不存在") {
        dataSource.value = [];
      }
    });
};

const saveFileName = async (params) => {
  // 添加类目
  let param = {
    knowledgebase_id: route.query.id,
    p_id: pid.value,
    id: curcate.id,
    ...params,
  };
  categoriesAdd(param).then((res) => {
    _this.$message("提交成功");
    searchCate();
    isShowAdd.value = false;
  });
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

const handleDragEnd = (draggingNode, dropNode, dropType, ev) => {
  if (!draggingNode || !dropNode) return;

  if (
    draggingNode.data.id != dropNode.data.id &&
    dropNode.data.pid != draggingNode.data.id
  ) {
    let innode = findNodeById(dataSource.value, draggingNode.data.id);
    if (innode && innode.children && innode.children.length > 0) {
      // 查询是不是子节点
      let curnode = findNodeById(innode.children, dropNode.data.id);
      if (curnode) {
        return false;
      }
    }

    draggingNode.data.pid = dropNode.data.id;

    categoriesAdd({
      id: draggingNode.data.id,
      p_id: draggingNode.data.pid,
      name: draggingNode.data.name,
      knowledgebase_id: route.query.id,
      caption: "",
    }).then((res) => {
      searchCate();
    });
  }
};

const checkCate = async (data) => {
  searchParams.keyword = undefined;
  searchParams.category_id = data.id;
  dataSource.value = [].concat(dataSource.value);
  await nextTick();
  treeSelect.value.setCurrentKey(parseInt(searchParams.category_id));
  search("init");
};

const changePage = (type, id) => {
  let query = { ...route.query };
  query.it = type;
  query.did = id;
  router.replace({ path: route.path, query: query });
};

// 文档操作
const deldoc = (id) => {
  _this.$confirm("确定要删除该文档吗？").then((res) => {
    documentsDelete({ id }).then((res) => {
      _this.$message("删除成功");
      search();
    });
  });
};

const delXl = (id) => {
  _this.$confirm("确定要删除该向量库数据吗？").then((res) => {
    documentsDeleteIndex({ id }).then((res) => {
      _this.$message("删除成功");
      search();
    });
  });
};
const addXl = (id) => {
  documentsConverter({ id }).then((res) => {
    _this.$message("添加成功");
    search();
  });
};

const isShowDialog = ref(false);

const curcateData = ref({});
const curcateData1 = ref({});

const curDomid = ref("");
const curDomname = ref("");

const openDialog = (item) => {
  curDomid.value = "";
  ChangeTreeItem.value = null;
  if (item) {
    ChangeTreeItem.value = { ...item };
    curDomid.value = item.id;
    curDomname.value = item.category_id
      ? findNodeById(dataSource.value, item.category_id).name
      : "未分类";
  }
  curcateData1.value = {};
  curcateData.value = {};

  isShowChangeTree.value = true;
};
const ChangeTreeItem = ref(null)
const isShowChangeTree = ref(false);
const subChangeTree = (res) => {
  curcateData.value = res.curcateData;
  curcateData1.value = res.curcateData1;
  curDomid.value = res.curDomid;
  sub()

};

const sub = () => {
  if (!curcateData1.value) return false;
  let param = {
    target_category_id: curcateData1.value.id,
  };
  if (curDomid.value) {
    // 调整文档类目单独
    param.id = curDomid.value;
  } else {
    // 调整类目
    if (!curcateData.value) return false;
    param.category_id = curcateData.value.id;
  }

  if (!param.target_category_id) return false;
  documentsMove(param).then((res) => {
    _this.$message("提交成功");
    isShowChangeTree.value = false;
    search();
  });
};


const textlist = ref([]);
const splist = ref([]);
const excellist = ref([]);
knowledges().then((res) => {
  let arr = res || [];
  textlist.value = [];
  splist.value = [];
  excellist.value = [];
  arr.forEach((item) => {
    if (item.type == 2) {
      splist.value.push(item);
    } else if (item.type == 1) {
      textlist.value.push(item);
    } else if (item.type == 3) {
      excellist.value.push(item);
    }
  });
});

const xlDialog = ref(false);
const xlform = reactive({
  knowledgebase_k: 5,
  knowledgebase_ids: [],
  file_knowledgebase_ids: [],
  product_model_ids: [],
  file_knowledgebase_k: 5,
  product_model_top_k: 5,
  question: "",
});
const curContext = ref([]);
const openxlDialog = (item) => {
  curContext.value = [];
  xlform.knowledgebase_k = 5;
  xlform.knowledgebase_ids = [detailData.value.id];
  xlform.product_model_ids = [];
  xlform.file_knowledgebase_ids = [];
  xlform.product_model_top_k = 5;
  xlform.file_knowledgebase_k = 5;
  xlform.question = "";

  xlDialog.value = true;
};

const similaritysearchfn = () => {
  if (!xlform.question) {
    return false;
  }
  similaritysearch(xlform).then((res) => {
    res.forEach((citem) => {
      citem.isOpen = false;
    });
    curContext.value = res;
    nextTick(() => {
      let arr = document.querySelectorAll(".js-intro");
      arr.forEach((item, index) => {
        if (item.offsetHeight < item.querySelector(".text").offsetHeight) {
          item.querySelector(".js-btn").style.cssText = "";
        }
      });
    });
  });
};
const tableRef = ref(null);

const openWind = (item) => {
  if (item.metadata) {
    let id = item.metadata.knowledgebase_id;
    let type = item.metadata.type;
    let did = item.metadata.ref_real_id;
    let rid = item.metadata.ref_id;
    if (type == "excel_document") {
      window.open(`/chat/detail?id=${id}&type=${type}&did=${did}&rid=${rid}`);
    } else if (type == "product_model") {
      window.open(`/dataset/shop?id=${id}&curid=${did}`);
    } else if (type == "knowledge_document") {
      window.open(`/dataset/detail?it=2&id=${id}&did=${did}`);
    }
  }
};

const getIcon = (type) => {
  // 定义一个对象来映射type到curtype的值，使得代码更简洁且易于维护
  const typeToCurtypeMap = {
    knowledge_document: 1,
    product_model: 2,
    excel_document: 3,
  };

  // 使用逻辑或操作符为curtype提供一个默认值
  const curtype = typeToCurtypeMap[type] || 1;

  return store.getters.iconMaps.knowledgeIcons[curtype];
};


const updateList = () => {
  let params = {
    knowledgebase_id:route.query.id
  }
  updatesxl(params).then((res) => {
    if(res){
      _this.$message("批量更新向量库提交成功");
      search("init");
    } 
  })
  
}



</script>
<template>
  <div v-if="detailData" class="dataset-detail">
    <div class="c-titlebox">
      <span class="title">
        <span class="c-pointer" style="color: #909BA5;;margin-right: 5px;" @click="goback(null, router,'/dataset/list?active=1')">
          全部知识库
          <span class="iconfont icon-xiangyoujiantou"></span>
        </span>
        {{ detailData.name }}</span>

      <div class="btns">
        
        <el-button size="small" @click="openDialog()" plain>调整类目</el-button>
        <el-button size="small" @click="openxlDialog()" plain>向量检测</el-button>
        <el-button size="small" @click="updateList()" plain>批量更新向量库</el-button>
      </div>
    </div>
    <div class="c-bodybox">

      <div class="catebox leftbox">


        <div class="topbtns">
          <span class="title">文档类目</span>
          <el-button @click="checkCate({ id: undefined })" class="on noradius" plain>
            <span class="iconfont icon-anniu-zhankai"></span>
            查看全部
          </el-button>
        </div>


        <div class="treebox contain">
          <el-scrollbar>
            <div class="el-tree el-tree--highlight-current" role="tree" style="width:100%;">
              <div class="el-tree-node" :class="{ 'is-current': searchParams.category_id == 0 }">
                <div class="el-tree-node__content" style="padding-left: 0px">
                  <div title="1" @click="checkCate({ id: 0 })" style="padding-left: 35px" class="custom-tree-node">
                    <span class="ellipsis">未分类</span>
                  </div>
                </div>
              </div>
            </div>
            <el-tree ref="treeSelect" style="width:100%;" :data="dataSource" draggable @node-drag-end="handleDragEnd"
              node-key="id" empty-text="暂无商品类目信息" highlight-current
              @node-click="checkCate"
              :current-node-key="searchParams.category_id?parseInt(searchParams.category_id):undefined" default-expand-all :expand-on-click-node="false">
              <template #default="{ node, data }">
                <div @click="checkCate(data)" :title="data.name" class="custom-tree-node">
                  <span class="ellipsis">{{ data.name }}</span>
                  <div class="btns">
                    <span title="添加子类目" @click.stop="addfn(data)" class="iconfont icon-shuzhuang-tianjia"></span>
                    <span title="修改" @click.stop="editfn(data)" class="iconfont icon-xiugai"></span>
                    <span title="删除类目" @click.stop="del(data.id)" class="iconfont icon-shuzhuang-shanchu"></span>
                  </div>
                </div>
              </template>
            </el-tree>
          </el-scrollbar>
        </div>

        <div class="botbtns">
          <el-button style="width: 100%;" plain class="on noradius" @click="addfn({ id: null })"><span class="iconfont icon-liebiao-xinzeng"></span>
            新增类目</el-button>
        </div>
      </div>



      <div class="tablebox rightbox">
        <template v-if="route.query.it == 3">
          <Index></Index>
        </template>
        <template v-else-if="route.query.it == 1 || route.query.it == 2">
          <Wbsj></Wbsj>
        </template>
        <template v-else>
          <div class="c-top-searchbox searchbox">
            <div class="lbox re">
              <el-button style="margin-right: 16px;" size="small" @click="changePage(1)" type="primary">新建文档</el-button>
              <el-input style="width:300px;" v-model="searchParams.keyword" placeholder="关键词查询"
                clearable />
                <el-button style="position: absolute;right: 0;top: 0;border-radius: var(--el-border-radius-base);" @click="search()" type="primary">查询</el-button>
            </div>
            <div class="rbox">
              <span @click="goback(null, router,'/dataset/list?active=1')" class="c-iconbackbox">
          <span class="iconfont icon-fuwenben-chexiao"></span> 返回
        </span>
            </div>
          </div>
          <div class="tableboxContain">
              <el-table ref="tableRef" :data="list" 
              :max-height="store.getters.innerHeight - 238"
              style="width: 100%">
                <!-- <el-table-column type="selection" width="55" /> -->
                <el-table-column label="编号" width="80" type="index" />
                <el-table-column label="id" width="80" prop="id" />
                <el-table-column label="文档名称">
                  <template #default="scope">
                    <span class="pointer" @click="changePage(2, scope.row.id)">{{ scope.row.name }}</span>
                  </template>
                </el-table-column>

                <el-table-column align="center" label="日期">
                  <template #default="scope">
                    <span>{{
                      getTime(scope.row.updated_at) ||
                      getTime(scope.row.created_at)
                    }}</span>
                  </template>
                </el-table-column>

                <el-table-column align="right" width="400" label="向量库">
                  <template #default="scope">
                    

                      <div @click="changePage(3, scope.row.id)" v-if="scope.row.is_index" class="c-table-ibtn">
                      <span class="iconfont icon-liebiao-chakan"></span>
                      查看
                    </div>

                    
                    <div @click="addXl(scope.row.id)" :style="scope.row.is_index?'color:var(--el-color-primary)':''" 
                    v-if="scope.row.is_markdown" class="c-table-ibtn">
                      <span class="iconfont icon-liebiao-gengxinxiangliang"></span>
                      <span style="display: flex;align-items: center;">{{
                        scope.row.is_index ? "更新向量库" : "添加至向量库"
                      }}<span v-if="scope.row.is_index_refresh && scope.row.is_index" title="文档已修改，请更新向量库"
                    class="iconfont icon-gantanhao"></span></span>
                      </div> 

                      <div v-if="scope.row.is_index" @click="delXl(scope.row.id)" class="c-table-ibtn c-btn-del">
                      <span class="iconfont icon-shuzhuang-shanchu"></span>
                      从向量库删除
                    </div>
                  </template>
                </el-table-column>

                <el-table-column width="240" align="right" label="操作">
                  <template #default="scope">

                    <div @click="openDialog(scope.row)" class="c-table-ibtn">
                      <span class="iconfont icon-liebiao-xiugaileimu"></span>
                      修改类目
                    </div>

                    <div @click="changePage(2, scope.row.id)" class="c-table-ibtn">
                      <span class="iconfont icon-xiugai"></span>
                      修改
                    </div>
                    <div @click="deldoc(scope.row.id)" class="c-table-ibtn c-btn-del">
                      <span class="iconfont icon-shuzhuang-shanchu"></span>
                      删除
                    </div>
                    
                  </template>
                </el-table-column>
                <template #empty="scope">
                  <div class="c-emptybox"><icon type="empzwssjg" width="100" height="100"></icon>暂无数据~~</div>
                </template>
              </el-table>

              <div v-if="total > 0" class="c-pagination">
                <el-pagination :hide-on-single-page="false" background :page-size="searchParams.pagesize"
                  :current-page="searchParams.page" @size-change="
                    (val) => {
                      searchParams.pagesize = val;
                      searchParams.page = Math.min(
                        Math.ceil(total / searchParams.pagesize),
                        searchParams.page
                      );
                      search();
                    }
                  " @current-change="
                    (val) => {
                      searchParams.page = val;
                      tableRef && tableRef.scrollTo(0,0)
                      search();
                    }
                  " :page-sizes="[30, 50, 100, 900]" layout="total,sizes,jumper,prev, pager, next" :total="total" />
              </div>
          </div>
        </template>
      </div>

    </div>
  </div>

  <template v-if="isShowAdd">
    <Add v-model="isShowAdd" :name="curcate.name" :caption="curcate.caption" @subfn="saveFileName"
      :title="curcate.name ? '修改商品类目' : '添加商品类目'"></Add>
  </template>


  <ChangeTree :dataSource="dataSource" v-model="isShowChangeTree" @subfn="subChangeTree" :item="ChangeTreeItem">
  </ChangeTree>

  <xltest :xlform="xlform" v-model="xlDialog"></xltest>
</template>
<style></style>
<style scoped>


.js-btn {
  cursor: pointer;
  position: absolute;
  right: 30px;
  bottom: 18px;
  background: #fff;
  padding: 2px;
  color: var(--el-color-primary);
  display: inline-block;
  font-size: 12px;
}

.intro {
  display: block;
  height: 40px;
  overflow: hidden;
  line-height: 20px;
}

.intro.open {
  height: auto;
}


.icon-zhishiku {
  color: var(--el-color-primary);
}

.icon-gantanhao {
  color: var(--el-color-danger);
  position: relative;
  cursor: pointer;
}

.icon-zhengquewancheng-xianxingyuankuang {
  font-size: 14px;
  margin-left: 5px;
}

.tableboxContain {
  display: block;
  position: relative;
  width: 100%;
  height: auto;
}

.catebox .tip {
  font-size: 12px;
  color: #ccc;
}

.treedialog {
  display: flex;
  align-items: flex-start;
  justify-content: center;
}

.treedialog .title {
  text-align: left;
  padding: 10px;
  font-weight: bold;
}

.treedialog .empty {
  color: #ccc;
  font-weight: normal;
}

.treedialog .treebox {
  width: 50%;
  box-sizing: border-box;
  border: 1px solid var(--el-border-color);
}



.searchbox .lbox {
  font-size: 18px;
  font-weight: bold;
  position: relative;
}

.searchbox .rbox {
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.searchbox .rbox .btnbox {
  margin-left: 10px;
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

.tablebox .title {
  padding: 10px;
}

.catebox .btns {
  padding-right: 5px;
}

.dataset-detail {
  display: block;
  width: 100%;
  height: 100%;
}

.dataset-detail .nav {
  display: block;
  position: relative;
  box-sizing: border-box;
  height: 100%;
  width: 300px;
  flex-shrink: 0;
  border-right: 2px solid var(--chakra-colors-gray-100);
}

.tablebox {
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  display: block;
  width: calc(100% - 300px);
  position: relative;
  padding: 20px;
  box-sizing: border-box;
}

.bitem {
  display: inline-flex;
  align-items: center;
  justify-content: flex-start;
  background: var(--chakra-colors-myGray-100);
  border: 1px solid var(--chakra-colors-myGray-200);
  border-radius: var(--chakra-radii-md);
  padding: 0px 10px;
  margin: 10px 5px;
}

.bitem .iconfont {
  color: #333;
}

.navtop {
  padding: 10px 15px;
  text-align: left;
  border-bottom: 1px solid var(--chakra-colors-gray-200);
  margin-bottom: 20px;
}

.navtop .namebox {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  text-align: left;
}

.navtop .namebox .iconfont {
  flex-shrink: 0;
  font-weight: bold;
  font-size: 26px;
  color: var(--chakra-colors-primary-600);
}

.navtop .namebox .name {
  word-break: break-all;
  font-weight: bold;
  font-size: 14px;
}

.navitem {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding: 5px 10px;
  cursor: pointer;
  margin: 10px 10px 0 10px;
  border-radius: var(--chakra-radii-md);
  font-size: 14px;
}

.navitem .iconfont {
  font-size: 20px;
  margin-right: 3px;
}

.navitem.on {
  color: var(--chakra-colors-primary-600);
  background: var(--chakra-colors-primary-100);
}

.navitem:hover {
  background: var(--chakra-colors-gray-100);
}

.backlist {
  cursor: pointer;
  position: absolute;
  bottom: 10px;
  left: 0;
  right: 0;
  font-size: 16px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.backlist .iconfont {
  font-size: 30px;
  color: var(--chakra-colors-primary-600);
}
</style>