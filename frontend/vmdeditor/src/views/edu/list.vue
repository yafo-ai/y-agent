<script setup>
import { ref, nextTick, shallowRef, onActivated, reactive } from "vue";
import {
  get_train_cases,
  cate_add,
  get_cates,
  cate_delete,
  train_case_delete,
  train_case_export,
  workflowlogs_pagination,
  trainmove_cate,
  download,
  trainunit_cases,
} from "@/api/api";

import { transferString, copyData, countWordSplit } from "@/assets/utils/util";
import { useStore } from "vuex";
import { onBeforeRouteLeave, useRoute, useRouter } from "vue-router";
import content from "@/components/content.vue";
import { goback, getTime } from "@/components/comp.js";
import result from "@/views/flow/components/result.vue";
import addxlDialog from "@/views/edu/components/addxlDialog.vue";
import ChangeTree from "@/components/changeTree.vue";
import ininput from "@/components/ioinput.vue";
import icon from "@/components/icon.vue"
const route = useRoute();
const router = useRouter();
const store = useStore();

let searchParams = reactive({
  page: 1,
  pagesize: 30,
  id: undefined,
  cate_id: undefined,
  is_marked: undefined,
  is_modified: undefined,
  input_data: "",
  output_data: "",
  feature: "",
});
const total = ref(0);

const reset = () => {
  // searchParams.cate_id = undefined;
  searchParams.id = undefined;
  searchParams.is_marked = undefined;
  searchParams.is_modified = undefined;
  searchParams.input_data = "";
  searchParams.output_data = "";
  searchParams.feature = "";
};
copyData(searchParams, route.query, "cate_id,id");

let pagelist = ref([]);

let nodeIDKey = "id";


const search = (type) => {
  if (type == "init") {
    searchParams.page = 1;
  }
  searchParams.id = searchParams.id || undefined;
  get_train_cases(searchParams).then((res) => {
    let arr = res.rows || [];
    let ids = [];
    arr.forEach((aitem) => {
      if (aitem[nodeIDKey]) {
        ids.push(aitem[nodeIDKey]);
      }
    });

    if (ids.length > 0) {
      trainunit_cases({ ids: ids }).then((tres) => {
        initPagelist(tres.rows || [], arr);
      });
    } else {
      pagelist.value = arr;
    }
    total.value = res.total_records;
  });
  if (type != "noquery") {
    let query = { ...route.query, ...searchParams };
    router.replace({ path: route.path, query: query });
  }
};

const initPagelist = (rows, arr) => {
  arr.forEach((aitem) => {
    if (aitem[nodeIDKey]) {
      let tarr = [];
      rows.forEach((ritem) => {
        if (ritem['train_case_id'] == aitem[nodeIDKey]) {
          tarr.push(ritem);
        }
      });
      aitem.test_cates = tarr;
    }
  });
  pagelist.value = arr;
};

search();

const scrollbarRef = ref(null);

const treeSelect = ref(null);
const dataSource = ref([]);
const checkType = async (item) => {
  searchParams.cate_id = item.id;
  search("init");
};

const searchCate = (params) => {
  get_cates().then(async (res) => {
    dataSource.value = res || [];
    await nextTick();
    treeSelect.value.setCurrentKey(parseInt(searchParams.cate_id));
  });
};
searchCate();

const isShowAdd = ref(false);
const addparam = reactive({ name: "", color: "", id: undefined, pid: null });
const formRefedit = ref();
function generateRandomColor() {
  // 生成一个随机的十六进制颜色值
  const color =
    "#" +
    Math.floor(Math.random() * 16777215)
      .toString(16)
      .padEnd(6, "0");
  // 将颜色值转换为大写
  return color.toUpperCase();
}

// 使用函数
const inputRef = ref();
const addTypefn = async (item, type) => {
  addparam.pid = item.pid || null;

  addparam.id = item.id || undefined;
  addparam.name = item.name || "";
  addparam.color = item.color || generateRandomColor();
  if (type == "child") {
    // 添加子节点
    addparam.pid = item.id;
    addparam.name = "";
    addparam.id = undefined;
    addparam.color = generateRandomColor();
  }
  isShowAdd.value = true;
  setTimeout(() => {
    inputRef.value.focus();
  }, 400);
};

const delfn = (item) => {
  _this.$confirm("确定要删除所选数据?").then((res) => {
    train_case_delete({ id: item.id }).then((res) => {
      _this.$message("删除成功");
      search();
    });
  });
};
const delTypefn = (item) => {
  _this.$confirm("确定要删除所选数据?").then((res) => {
    cate_delete({ id: item.id }).then((res) => {
      _this.$message("删除成功");
      searchCate();
    });
  });
};
const editparam = ref({
  id: 0,
  train_cate_id: 0,
  input_data: "",
  output_data: "",
});
const isShowAddDialog = ref(false);

const editfn = async (item) => {
  editparam.value = {
    ...item,
    is_marked: !!item.is_marked,
    is_modified: !!item.is_modified,
  };
  isShowAddDialog.value = true;
};
const subeditfn = async (res) => {
  _this.$message("修改成功");
  isShowAddDialog.value = false;
  search();
};
const subaddfn = () => {
  if (!addparam.color) {
    _this.$message("请选择分类颜色", "error");
    return false;
  }
  if (!addparam.name) {
    inputRef.value.focus();
    return false;
  }
  cate_add(addparam).then((res) => {
    _this.$message("操作成功");
    isShowAdd.value = false;
    searchCate();
  });
};

const exportfn = () => {
  if (
    searchParams.cate_id === undefined ||
    searchParams.cate_id === null ||
    searchParams.cate_id === ""
  ) {
    _this.$message("请先选择分类", "error");
    return false;
  }
  train_case_export({ cate_id: searchParams.cate_id });
};

const runresult = ref({});
const showTest = ref(false);
const workflowrunfn = async (flow_id) => {
  let params = {
    page: 1,
    pagesize: 1,
    flow_id: flow_id,
  };
  workflowlogs_pagination(params).then((res) => {
    let arr = res.rows || [];
    runresult.value = arr[0] || {};
    showTest.value = true;
  });
};
const curnodeId = ref(null);

const isShowChangeTree = ref(false);
const subChangeTree = (data) => {
  trainmove_cate({
    source_cate_id: data.curcateData.id,
    target_cate_id: data.curcateData1.id,
  }).then((res) => {
    _this.$message("操作成功");
    isShowChangeTree.value = false;
    search();
  });
};

const beforeAvatarUpload = (file) => {
  store.commit("loading", true);
  return true;
};
const errfn = (err) => {
  let myError = err.toString();
  myError = myError.replace("UploadAjaxError: ", "");
  myError = JSON.parse(myError);
  _this.$message(myError.detail, "error");
  // 报错也查询一下
  store.commit("loading", false);
  search();
};
const uploadRef = ref(null);
const sucfn = (res, file, files) => {
  _this.$message("导入成功");
  if (uploadRef.value) uploadRef.value.clearFiles();
  store.commit("loading", false);
  search();
};
const tableRef = ref(null);
const searchheight = ref(0);
</script>

<template>
  <div class="pagelistbox">
    <div class="c-titlebox">
      <span class="title">语料 <span style="font-size: 18px;color: #999;" v-if="searchParams.cate_id !== undefined"> [id:{{ searchParams.cate_id }}]</span></span>
    </div>
    <div class="c-bodybox">
      <div class="catebox leftbox">

        <div class="topbtns">
          <span class="title">语料类型</span>
          <el-button @click="checkType({ id: undefined })" class="on noradius" plain>
            <span class="iconfont icon-anniu-zhankai"></span>
            查看全部
          </el-button>
        </div>

        <div class="treebox contain">
          <el-scrollbar>
            <div class="el-tree el-tree--highlight-current" role="tree" style="width:100%">
              <div class="el-tree-node" :class="{ 'is-current': searchParams.cate_id == 0 }">
                <div class="el-tree-node__content" style="padding-left: 0px">
                  <div @click="checkType({ id: 0 })" style="padding-left: 35px" class="custom-tree-node">
                    <div class="item">
                      <span class="c-color" :style="'background-color:#ff0000'"></span>未分类
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <el-tree ref="treeSelect" style="width:100%" :data="dataSource" node-key="id" empty-text="暂无语料类目信息"
              highlight-current :current-node-key="searchParams.cate_id ? parseInt(searchParams.cate_id) : undefined"
              default-expand-all @node-click="checkType" :expand-on-click-node="false">
              <template #default="{ node, data }">
                <div @click="checkType(data)" :title="data.name" class="custom-tree-node">
                  <div class="item">
                    <span class="c-color" :style="'background-color:' + data.color"></span>
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
          <el-button style="width: 100%;" plain class="on noradius"
            @click="addTypefn({ name: '', color: '', id: undefined, pid: null })"><span
              class="iconfont icon-liebiao-xinzeng"></span>
            新增分类</el-button>
        </div>
      </div>
      <div v-initTableHeight class="c-tablebox tableboxContain c-tooltip rightbox">
        <div style="margin-left: 24px;margin-right: 24px;" class="c-top-searchbox c-js-item">
          <el-form :model="searchParams" ref="searchFormRef" inline class="demo-form-inline">
            <el-form-item style="width: 210px;" label="id" prop="id">
              <el-input v-model="searchParams.id" type="text"></el-input>
            </el-form-item>
            <el-form-item style="width: 210px;" label="输入" prop="input_data">
              <el-input v-model="searchParams.input_data" type="text"></el-input>
            </el-form-item>

            <el-form-item style="width: 210px;" label="输出" prop="output_data">
              <el-input v-model="searchParams.output_data" type="text"></el-input>
            </el-form-item>

            <el-form-item style="width: 210px;" label="特征概要" prop="feature">
              <el-input v-model="searchParams.feature" type="text"></el-input>
            </el-form-item>

            <el-form-item style="width: 210px;" label="是否审核" prop="is_marked">
              <el-select clearable v-model="searchParams.is_marked" placeholder="请选择">
                <el-option label="未审核" :value="false" />
                <el-option label="已审核" :value="true" />
              </el-select>
            </el-form-item>

            <el-form-item style="width: 210px;" label="是否更正" prop="is_modified">
              <el-select clearable v-model="searchParams.is_modified" placeholder="请选择">
                <el-option label="未更正" :value="false" />
                <el-option label="已更正" :value="true" />
              </el-select>
            </el-form-item>
          </el-form>
          <div class="rbox">
            <span v-searchOpen
              @click="searchheight == 0 ? searchheight = 67 : searchheight = 0; tableRef && tableRef.update()"
              class="c-search-openbtn">
              <span class="iconfont icon-anniu-zhankai"></span><span class="opentext">展开</span><span
                class="closetext">收起</span>
            </span>
            <el-button @click="search('init')" type="primary">查询</el-button>
            <el-button @click="reset()" plain>重置</el-button>
          </div>
        </div>
        <div class="btnbox tl c-js-item">
          <div class="btns">
            <el-button @click="
              editfn({
                id: null,
                is_marked: undefined,
                is_modified: undefined,
                train_cate_id: null,
                input_data: '',
                output_data: '',
              })
              " type="primary">新增</el-button>
            <el-button @click="isShowChangeTree = true" plain>调整类目</el-button>
            <el-upload class="upload-demo" style="margin: 0 12px" ref="uploadRef"
              :headers="{ authorization: 'Bearer ' + store.state.token }" :before-upload="beforeAvatarUpload"
              :show-file-list="false" :on-error="errfn" :on-success="sucfn" :limit="1" action="/api/train/case/import">
              <el-button plain>批量导入</el-button>
            </el-upload>
            <el-button @click="exportfn()" plain>导出</el-button>

            <el-upload class="upload-demo" style="margin: 0 12px 0 12px" ref="uploadRef"
              :headers="{ authorization: 'Bearer ' + store.state.token }" :before-upload="beforeAvatarUpload"
              :show-file-list="false" :on-error="errfn" :on-success="sucfn" :limit="1"
              action="/api/train/case/import_update">
              <el-button plain>批量修改</el-button>
              <!-- <el-tooltip
              effect="light"
              content="先导出数据后，修改完使用批量修改"
              placement="top"
            >
              <span class="iconfont icon-bangzhu c-danger"></span>
            </el-tooltip> -->
            </el-upload>
          </div>
          <el-link @click="download('/api/train/download/case_template')"><span
              class="iconfont icon-anniu-xiazai"></span>下载导入模板</el-link>
        </div>
        <div class="bodybox c-js-body">
          <div class="contain">
            <el-table ref="tableRef" tooltip-effect="light" :max-height="store.getters.innerHeight - 292 - searchheight"
              border :data="pagelist" style="width: 100%">
              <el-table-column width="100" prop="id" label="id">
                <template #default="scope">
                  <el-popover v-if="scope.row.test_cates && scope.row.test_cates.length > 0" placement="top-start"
                    :width="200" trigger="hover">
                    <template #reference>
                      <div class="dotbox">
                        <span v-for="(item, index) in scope.row.test_cates" class="dot" :class="{ on: item.xl }" :style="'background-color: ' +
                          item.case_cate_color +
                          '; left: ' +
                          index * 5 +
                          'px'
                          "></span>
                      </div>
                    </template>
                    <div class="dotcontentbox c-scroll-contain">
                      <div v-if="
                        scope.row.test_cates && scope.row.test_cates.length > 0
                      " class="title">
                        单元测试
                      </div>
                      <div v-if="
                        scope.row.test_cates && scope.row.test_cates.length > 0
                      " class="items">
                        <div v-for="item in scope.row.test_cates" class="item ellipsis">
                          <span class="c-color radius" :style="'background-color:' + item.case_cate_color"></span>
                          <span class="c-color-aaa c-pointer" v-copy="item.case_id">id: {{ item.case_id }}</span>
                          &nbsp;{{ item.case_cate_name }}
                        </div>
                      </div>
                    </div>
                  </el-popover>
                  {{ scope.row.id }}
                </template>
              </el-table-column>
              <el-table-column label="类型" width="160">
                <template #default="scope">
                  <div class="flex">
                    <span class="c-color" :style="'background-color: ' + scope.row.train_cate_color"></span>{{
                      scope.row.train_cate_name }}
                  </div>
                </template>
              </el-table-column>

              <el-table-column min-width="160" label="输入">

                <template #default="scope">
                  <ininput :input="scope.row.input_data" :output="scope.row.output_data"></ininput>
                </template>
              </el-table-column>

              <el-table-column width="160" label="输出">
                <template #default="scope">
                  <ininput :isShowOutput="true" :input="scope.row.input_data" :output="scope.row.output_data"></ininput>
                </template>
              </el-table-column>


              <el-table-column min-width="160" label="特征概要">
                <template #default="scope">
                  <el-popover v-if="scope.row.feature" placement="top-start" :width="500" trigger="hover">
                    <template #reference>
                      <div class="ellipsis2">
                        {{ scope.row.feature }}
                      </div>
                    </template>
                    <div style="margin: 0 -20px;">
                      <el-scrollbar max-height="400">
                        <div v-html="scope.row.feature.replace(/\n/g, '<br>')" style="margin:0 20px;">
                        </div>
                      </el-scrollbar>
                    </div>

                  </el-popover>
                </template>
              </el-table-column>

              <el-table-column width="100" label="是否审核">
                <template #default="scope">
                  <span v-if="scope.row.is_marked" class="c-success-btn">已审核</span>
                  <span v-else class="c-plain-btn">未审核</span>
                </template>
              </el-table-column>
              <el-table-column width="100" label="是否更正">
                <template #default="scope">
                  <span v-if="scope.row.is_modified" class="c-success-btn">已更正</span>
                  <span v-else class="c-plain-btn">未更正</span>
                </template>
              </el-table-column>

              <el-table-column width="160" label="创建时间">
                <template #default="scope">
                  {{ getTime(scope.row.created_at) }}
                </template>
              </el-table-column>
              <el-table-column width="160" align="center" label="修改时间">
                <template #default="scope">
                  {{ getTime(scope.row.updated_at) }}
                </template>
              </el-table-column>

              <el-table-column width="180" fixed="right" align="right" label="操作">
                <template #default="scope">

                  <div @click="editfn(scope.row)" class="c-table-ibtn">
                    <span class="iconfont icon-xiugai"></span>
                    修改
                  </div>

                  <div v-if="scope.row.workflow_log_id" @click="
                    curnodeId = scope.row.workflow_node_log_id;
                  workflowrunfn(scope.row.workflow_log_id);
                  " class="c-table-ibtn">
                    <span class="iconfont icon-liebiao-xiangqing"></span>
                    用例详情
                  </div>


                 
                  <div @click="delfn(scope.row)" class="c-table-ibtn c-btn-del">
                    <span class="iconfont icon-shuzhuang-shanchu"></span>
                    删除
                  </div>
                </template>
              </el-table-column>
              <template #empty="scope">
                <div class="c-emptybox">
                  <icon type="empzwssjg" width="100" height="100"></icon>暂无数据~~
                </div>
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
                    tableRef && tableRef.scrollTo(0, 0);
                    search();
                  }
                " :page-sizes="[30, 50, 100, 900]" layout="total,sizes,jumper,prev, pager, next" :total="total" />
            </div>
          </div>
        </div>


      </div>
    </div>
  </div>
  <el-dialog align-center v-model="isShowAdd" :title="addparam.id ? '修改分类' : '新增分类'" width="500">
    <el-form ref="formRef" :model="addparam" label-width="auto" label-position="top" class="demo-dynamic tl">
      <el-form-item prop="name" label="分类名称" :rules="[
        {
          required: true,
          message: '请输入分类名称',
          trigger: 'blur',
        },
      ]">
        <el-input v-model="addparam.name" ref="inputRef" style="width: calc(100% - 42px); margin-right: 10px"
          placeholder="分类名称" />
        <el-color-picker v-model="addparam.color" />
      </el-form-item>
    </el-form>
    <template #footer>
      <div class="dialog-footer">
        <el-button plain @click="isShowAdd = false"> 取消 </el-button>
        <el-button type="primary" @click="subaddfn()"> 确定 </el-button>
      </div>
    </template>
  </el-dialog>

  <addxlDialog v-model="isShowAddDialog" :item="editparam" :curResult="editparam" :title="editparam.id ? '修改语料数据' : '新增语料数据'"
    @subfn="subeditfn">
  </addxlDialog>

  <result v-model="showTest" :nodeid="curnodeId" :data="runresult"></result>

  <ChangeTree :dataSource="dataSource" v-model="isShowChangeTree" @subfn="subChangeTree"></ChangeTree>
</template>

<style scoped>
.btnbox {
  padding: 0 24px 20px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.dotbox {
  position: relative;
  padding: 10px 0 0 0;
  cursor: pointer;
}

.dotbox .dot {
  display: block;
  position: absolute;
  width: 10px;
  height: 10px;
  top: 0px;
  border-radius: 5px;
  z-index: 10;
}

.dotbox .dot.on {
  border-radius: 0;
}

.dotcontentbox {
  display: block;
  width: 100%;
  font-size: 12px;
  max-height: 300px;
  overflow-y: auto;
}

.dotcontentbox .title {
  color: #aaa;
  margin-bottom: 10px;
}

.dotcontentbox .items {
  margin-bottom: 10px;
}

.dotcontentbox .items .item {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  flex-wrap: wrap;
}

.dotcontentbox .items .item.unit {
  color: var(--el-color-primary);
}


.flex {
  display: flex;
  align-items: center;
}


.nav {
  display: block;
  position: relative;
  box-sizing: border-box;
  height: 100%;
  width: 300px;
  flex-shrink: 0;
  border-right: 2px solid var(--chakra-colors-gray-100);
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

.catebox .tip {
  font-size: 12px;
  color: #ccc;
}

.icon-wuguan {
  color: var(--el-color-success);
}

.icon-geren {
  color: var(--el-color-primary);
}

.searchbox {
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  padding: 20px 0px 0 0px;
  box-sizing: border-box;
  text-align: left;
}

.searchbox .rbox {
  padding-top: 4px;
  flex-shrink: 0;
}

.times {
  color: #999;
  font-size: 12px;
}

.icon-canshu {
  font-size: 36px;
  font-weight: bold;
  color: #1948e7;
}



.tableboxContain .btnbox {
  text-align: left;
  padding-bottom: 20px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.tableboxContain .btnbox .btns {
  display: flex;
  align-items: center;
}

.tableboxContain .bodybox {
  height: calc(100% - 170px);
}

.pagelistbox {

  width: 100%;
  box-sizing: border-box;
  height: 100%;
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

.icon-shugui {
  color: var(--chakra-colors-primary-600);
  font-size: 20px;
}
</style>
