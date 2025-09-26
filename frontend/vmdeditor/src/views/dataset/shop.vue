<script setup>
import { ref, nextTick, onMounted, reactive, watch, onUnmounted } from "vue";
import { useStore } from "vuex";
import {
  useRoute,
  useRouter,
  onBeforeRouteUpdate,
  onBeforeRouteLeave,
} from "vue-router";
import { goback, getTime } from "@/components/comp.js";
import Wbsj from "./components/wbsj.vue";
import Index from "./components/index.vue";
import {
  knowledgesGet,
  products,
  productsAdd,
  productsGet,
  productsDelete,
  productsGettemp,
  productsmove,
  updatesxl,
} from "@/api/api";
import Add from "./components/add.vue";
import { Delete, Plus, Eleme } from "@element-plus/icons-vue";
import icon from "@/components/icon.vue"
const route = useRoute();
const router = useRouter();
const store = useStore();
const detailData = ref(null);
const dataSource = ref([]);

const curid = ref(undefined);

if (route.query.curid) {
  curid.value = parseInt(route.query.curid);
}

knowledgesGet({ id: route.query.id }).then((res) => {
  detailData.value = res;
  document.title = detailData.value.name;
});

onMounted(async () => {
  productsGetfn(curid.value);
});


const addListfn = (data) => {
  form.attrs.push({
    id: 0,
    attr_id: 0,
    attr_key: "",
    attr_value: [""],
    attr_value_datatype: 1,
    sort: 0,
  });
};



const del = (id) => {
  _this.$confirm("确定要删除该商品节点吗？").then((res) => {
    productsDelete({ id }).then((res) => {
      _this.$message("删除成功");
      if (curNodeData.value && id == curNodeData.value.id) {
        addNodeFn({ p_id: undefined });
        let query = { ...route.query, curid: undefined };
        router.replace({ path: route.path, query: query });
      }
      productsfn();
    });
  });
};


const loadParams = reactive({
  knowledgebase_id: route.query.id,
  p_id: 0,
  page: 1,
  pagesize: 10000,
  keyword: "",
});

const treeSelect = ref(null);
const productsfn = () => {
  products(loadParams)
    .then(async (res) => {

      if (res.rows.length < 1) {
        addNodeFn({});
      }
      dataSource.value = [].concat(buildTree(res.rows));
      await nextTick();
      treeSelect.value.setCurrentKey(parseInt(curid.value))

    })
    .catch((err) => { });
};
productsfn();

const addNodeFn = (item) => {
  const defaultValues = {
    id: undefined,
    p_id: 0,
    name: "",
    caption: "",
    note: "",
    is_sku: false,
    barcode: "",
    nccode: "",
    attrs: [],
  };

  // 使用Object.assign合并对象，将item的属性与defaultValues合并
  // 如果有相同的属性，item的属性会覆盖defaultValues的属性
  Object.assign(form, { ...defaultValues, ...item });
};

const checkCate = (data) => {
  productsGetfn(data.id);
};

const addfn = (data) => {
  curNodeData.value = { ...data };
  productsGettemp({ p_id: data.id })
    .then((res) => {
      let parr = res.parent_attrs;
      parr.forEach((item) => {
        item.disabled = true;
      });
      let arr = res.same_attrs;
      arr.forEach((item) => {
        item.attr_value = [""];
      });
      addNodeFn({
        p_id: data.id,
        attrs: parr.concat(arr),
      });
    })
    .catch((err) => {
      addNodeFn({
        p_id: data.id,
        attrs: [],
      });
    });
};

const curNodeData = ref(null);

const productsGetfn = (id) => {
  if (!id) return;

  let query = { ...route.query, curid: id };
  router.replace({ path: route.path, query: query });
  curid.value = parseInt(id);
  productsGet({ id: id })
    .then((res) => {
      if (res.parent_attrs) {
        res.parent_attrs.forEach((item) => {
          item.disabled = true;
        })
        res.product.attrs = res.parent_attrs.concat(res.product.attrs);
      }
      curNodeData.value = res.product;
      addNodeFn(res.product);
    })
    .catch((err) => { });
};

const form = reactive({
  knowledgebase_id: route.query.id,
  p_id: undefined,
  name: "",
  caption: "",
  note: "",
  is_sku: false,
  barcode: "",
  nccode: "",
  attrs: [],
});

function findNodeById(tree, id) {
  for (let i = 0; i < tree.length; i++) {
    if (tree[i].id == id) {
      return tree[i];
    }
    if (tree[i].children && tree[i].children.length > 0) {
      return findNodeById(tree[i].children, id)
    }
  }
  return null;
}

const handleDragEnd = (draggingNode, dropNode, dropType, ev) => {

  if (!draggingNode || !dropNode) return;

  if (draggingNode.data.id != dropNode.data.id && dropNode.data.p_id != draggingNode.data.id) {
    let innode = findNodeById(dataSource.value, draggingNode.data.id);
    if (innode && innode.children && innode.children.length > 0) {
      // 查询是不是子节点
      let curnode = findNodeById(innode.children, dropNode.data.id);
      if (curnode) {
        return false;
      }
    }

    draggingNode.data.p_id = dropNode.data.id;

    productsmove({
      id: draggingNode.data.id,
      target_pid: dropNode.data.id,
    }).then((res) => {
      productsfn();
    }).catch(err => {
      productsfn();
    })
  }

};

function buildTree(arr, p_id = 0) {
  const tree = [];
  for (let i = 0; i < arr.length; i++) {
    if (arr[i].p_id === p_id) {
      const children = buildTree(arr, arr[i].id);
      if (children.length) {
        arr[i].children = children;
      }
      tree.push(arr[i]);
    }
  }
  tree.sort((a, b) => {
    if (a.is_sku === b.is_sku) {
      if (a.id > b.id) {
        return 1
      } else {
        return -1;
      }
    } else if (a.is_sku) {
      return 1
    } else {
      return -1;
    }
  });
  return tree;
}

const ruleForm = ref();
const subfn = (formEl) => {
  if (!formEl) return;
  formEl.validate((valid) => {
    if (valid) {
      let params = Object.assign({}, form);
      let arr = [];
      params.attrs.forEach((item) => {
        item.id = item.id || 0;
        item.attr_id = item.id;
        item.sort = item.sort || 0;
        if (!item.disabled) {
          arr.push(item);
        }
      });
      params.attrs = arr;
      productsAdd(params)
        .then((res) => {
          _this.$message("提交成功");
          if (form.id) {
            curNodeData.value = form;
          }

          productsfn();
        })
        .catch((err) => { });
    } else {
      return false;
    }
  });
};


const checked1 = ref(false);
const isShowItem = (item) => {
  if (!checked1.value) {
    return true;
  } else {
    return !item.disabled;
  }

}


const updateList = () => {
  let params = {
    knowledgebase_id:route.query.id
  }
  updatesxl(params,true).then((res) => {
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
      <span class="title"><span class="c-pointer" style="color: #909BA5;;margin-right: 5px;"
          @click="goback(null, router, '/dataset/list?active=2')">
          全部知识库
          <span class="iconfont icon-xiangyoujiantou"></span>
        </span>{{ detailData.name }}</span>
        <!-- <div class="btns">
        <el-button size="small" @click="updateList()" plain>批量更新向量库</el-button>
      </div> -->
    </div>
    <div class="c-bodybox">

      <div style="width: 50%;" class="catebox leftbox">
      

        <div class="topbtns">
          <span class="title">商品节点</span>
        </div>
        <div style="height: 100%;" class="treebox contain">
          <el-scrollbar>
            <el-tree ref="treeSelect" :data="dataSource" draggable @node-drag-end="handleDragEnd" node-key="id"
              empty-text="暂无商品节点信息" highlight-current :current-node-key="parseInt(curid)" default-expand-all
              @node-click="checkCate"

              :expand-on-click-node="false">
              <template #default="{ node, data }">
                <div :title="data.name" class="custom-tree-node">
                  <div class="item">
                  <icon width="18" height="18" v-if="data.is_sku" type="spzsksp"></icon>
                  <icon width="18" height="18"  v-else type="spzskfl"></icon>
                  <div class="ellipsis">
                    {{ data.name }}
                  </div>
                  <div class="btns">
                    <el-button v-if="!data.is_sku" @click.stop="addfn(data)" title="添加子节点" size="small" text>
                      <span class="iconfont icon-shuzhuang-tianjia"></span>
                      添加
                    </el-button>

                    <el-button style="margin-left: 0" @click.stop="del(data.id)" title="删除节点" type="danger" size="small"
                      text>
                      <span class="iconfont icon-shuzhuang-shanchu"></span>
                      删除
                    </el-button>
                  </div>
                  </div>
                </div>
              </template>
            </el-tree>
          </el-scrollbar>
        </div>
      </div>



      <div v-if="form.p_id !== undefined" class="tablebox rightbox">
        <div class="tableboxContain">
          <el-scrollbar>
            <div class="mg20">
            <div v-if="dataSource.length < 1" class="tipTitle">
              <span class="err bold" v-if="form.p_id === 0">
                还没有添加节点信息，请完善以下节点信息
              </span>
            </div>
            <div v-else-if="form.p_id && !form.id" class="tipTitle">
              在
              <span class="bold">{{ curNodeData && curNodeData.name }}</span>
              下添加节点
            </div>
            <div v-else-if="form.id" class="tipTitle">
              <span class="bold">{{ curNodeData && curNodeData.name }}</span>
            </div>

            <el-form class="tl" :model="form" ref="ruleForm" label-width="auto" label-position="top" inline style="width: 100%">
              <el-form-item style="width: calc(100% - 226px);margin-right: 16px;" prop="name" :rules="[
                {
                  required: true,
                  message: '请输入名称',
                  trigger: 'blur',
                },
              ]" label="名称">
                <el-input v-model="form.name" type="text" placeholder="" />
              </el-form-item>
              <el-form-item class="c-switchbox-label" style="width: 210px;margin-right: 0;" label="是否商品">
                <div class="c-switchbox">
                    <div class="label"></div>
                    <div class="switch">
                      <el-switch v-model="form.is_sku" inline-prompt active-text="是" inactive-text="否" />
                    </div>
                  </div>
              </el-form-item>
              <el-form-item class="c-switchbox-label" style="width: calc(50% - 8px);margin-right: 16px;margin-top: -26px;" label="是否停用">

                <div class="c-switchbox">
                    <div class="label"></div>
                    <div class="switch">
                      <el-switch v-model="form.is_disabled" inline-prompt active-text="是" inactive-text="否" />
                    </div>
                  </div>
              </el-form-item>
              <el-form-item class="c-switchbox-label" style="width: calc(50% - 8px);margin-right: 0px;margin-top: -26px;" label="是否停产">
                <div class="c-switchbox">
                    <div class="label"></div>
                    <div class="switch">
                      <el-switch v-model="form.is_stop_production" inline-prompt active-text="是" inactive-text="否" />
                    </div>
                  </div>
              </el-form-item>
              <el-form-item style="width: calc(50% - 8px);margin-right: 16px;" v-if="form.is_sku" prop="barcode" :rules="[
                {
                  required: true,
                  message: '请输入69码',
                  trigger: 'blur',
                },
              ]" label="69码">
                <el-input v-model="form.barcode" type="text" placeholder="" />
              </el-form-item>
              <el-form-item style="width: calc(50% - 8px);margin-right: 0px;" v-if="form.is_sku" prop="nccode" :rules="[
                {
                  required: true,
                  message: '请输入NC编码',
                  trigger: 'blur',
                },
              ]" label="NC编码">
                <el-input v-model="form.nccode" type="text" placeholder="" />
              </el-form-item>

              <el-form-item style="width: 100%;margin-right: 0px;" label="介绍">
                <el-input v-model="form.note" :rows="2" type="textarea"
                  placeholder="填写关于此产品的介绍，例如：名词是“华为D16系列”的介绍为：华为D16系列是华为笔记本D系列，其中16是指屏幕是16存大小，具有大屏特点，适合对需要大屏幕的用户，例如学生、视频图片编辑等用户。" />
              </el-form-item>
            </el-form>

            <div class="searchbox">
              <div class="lbox">
                <el-button @click="addListfn()" style="margin-right:20px" type="primary">添加属性</el-button>
                <el-checkbox v-model="checked1" label="隐藏父级属性" size="small" />
              </div>
              <div class="rbox"></div>
            </div>
            <div class="itemsbox">
              <div class="itemstitle">
                <div class="label">属性名</div>
                <div class="vals">属性值</div>
              </div>
              <div v-if="form.attrs.length > 0" class="items">
                <div v-for="(item, index) in form.attrs" :key="index" v-show="isShowItem(item)" class="item">
                  <div class="label">
                    <el-input :disabled="item.disabled" v-model="item.attr_key" placeholder="属性名" />
                    <el-select style="width: 160px" :disabled="item.disabled" v-model="item.attr_value_datatype"
                      placeholder="类型">
                      <el-option :value="1" label="字符串"></el-option>
                      <el-option :value="2" label="数值"></el-option>
                      <el-option :value="3" label="日期"></el-option>
                      <el-option :value="4" label="列表"></el-option>
                    </el-select>
                  </div>
                  <div class="vals">
                    <span v-if="!item.disabled" :title="'删除属性:'+item.attr_key" @click="form.attrs.splice(index, 1)" class="addbtn c-danger-btn"
                      >
                      <span class="iconfont icon-liebiao-shanchu"></span>删除
                    </span>
                    <div v-for="(vitem, vindex) in item.attr_value" :key="vindex" class="val">
                      <el-input class="inp" :disabled="item.disabled" v-model="item.attr_value[vindex]"
                        placeholder="属性值" />
                      <span style="margin-left: 10px;" class="delbtn c-pointer" title="删除当前属性值" @click="item.attr_value.splice(vindex, 1)"
                        v-if="item.attr_value.length > 1 && !item.disabled" >
                        <span class="iconfont icon-liebiao-shanchu"></span>
                      </span>
                      <span title="添加属性值" v-if="
                        item.attr_value.length == vindex + 1 && !item.disabled
                      " @click="item.attr_value.push('')" class="addbtn1 c-pointer" >
                        <span class="iconfont icon-xinzengcanshu"></span>
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="items">
                <div class="empty">暂无属性数据</div>
              </div>
            </div>
          </div>
          </el-scrollbar>
        </div>
        <div style="justify-content: flex-end;" class="c-footerbtns">
          <el-button @click="subfn(ruleForm)" type="primary">提交信息</el-button>
        </div>
      </div>

    </div>
  </div>
</template>
<style></style>
<style scoped>
.c-danger-btn{
  cursor: pointer;
}
.icon-fenlei {
  color: var(--el-color-primary);
}

.icon-shangpin {
  color: var(--el-color-success);
}

.err {
  color: var(--el-color-danger);
}

.tipTitle {
  font-size: 16px;
  text-align: left;
  margin-bottom: 20px;
}

.tipTitle .bold {
  font-weight: bold;
  font-size: 22px;
}

.icon-zhishikuguanli {
  color: var(--el-color-success);
}

.empty {
  display: block;
  text-align: center;
  padding: 20px;
}

.itemsbox {
  height: 100%;
  width: 100%;
  position: relative;
}

.itemsbox .itemstitle {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  box-sizing: border-box;
  background: #f1f1f1;
  border-radius: 5px 5px 0 0;
  border: 1px solid #f1f1f1;
  border-bottom: none;
}

.itemsbox .label {
  width: 40%;
  flex-shrink: 0;
  box-sizing: border-box;
  border-right: 1px solid #f1f1f1;
  padding: 20px;
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
}

.itemsbox .vals {
  width: 60%;
  padding: 10px 20px;
  box-sizing: border-box;
  display: block;
  text-align: left;
  position: relative;
}

.itemsbox .itemstitle .label {
  padding: 10px 20px;
}

.itemsbox .items {
  height: calc(100% - 160px);
}

.itemsbox .items .item {
  display: flex;
  width: 100%;
  box-sizing: border-box;
  border: 1px solid #f1f1f1;
}

.itemsbox .items .item:nth-child(1) {
  border-top: none;
}

.itemsbox .vals .addbtn {
  position: absolute;
  right: 20px;
  top: 20px;
}

.itemsbox .vals .val {
  display: flex;
  width: 100%;
  align-items: center;
  justify-content: flex-start;
  padding: 10px 0;
}

.itemsbox .vals .val .inp {
  width: 50%;
}

.itemsbox .vals .val .addbtn1 {
  margin-left: 10px;
}

.icon-gantanhao {
  color: #f00;
  margin-right: 5px;
  position: relative;
  top: 2px;
}

.icon-zhengquewancheng-xianxingyuankuang {
  font-size: 14px;
  margin-left: 5px;
}

.tableboxContain {
  display: block;
  position: relative;
  width: 100%;
  height: calc(100% - 47px);
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

.searchbox {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
}

.searchbox .lbox {
  font-size: 18px;
  font-weight: bold;
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


.catebox .btns {
  padding-right: 5px;
}

.dataset-detail {
  display: block;
  width: 100%;
  height: 100%;
}

.mg20{
  margin: 0 20px;
}

.tablebox {
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  display: block;
  width: 50%;
  position: relative;
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
  font-size: 22px;
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