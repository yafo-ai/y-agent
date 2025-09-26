<script setup>
import { ref, nextTick, shallowRef, onActivated, reactive } from "vue";
import {
  testcasepagination,
  testcasebatch_execute,
  testcatedelete,
  testcasedelete,
  testcateadd,
  testcate,
  model_configall,
  workflowlogs_pagination,
  workflow,
  move_cate,
} from "@/api/api";
import result from "@/views/flow/components/result.vue";
import { transferString, copyData } from "@/assets/utils/util";
import { useStore } from "vuex";
import { onBeforeRouteLeave, useRoute, useRouter } from "vue-router";
import content from "@/components/content.vue";
import { goback, getTime } from "@/components/comp.js";
import CompApp from "@/views/app/list.vue";
import addtestDialog from "@/views/test/components/addtestDialog.vue";
import logdetail from "@/views/test/logdetail.vue";
import ChangeTree from "@/components/changeTree.vue"
import icon from "@/components/icon.vue"

const props = defineProps({
  TEST_TYPE: {
    type: [String, Number],
    default: "",
  },
});
const route = useRoute();
const router = useRouter();
const store = useStore();
// S单元测试 W流程测试
const TEST_TYPE = props.TEST_TYPE || (route.path === "/unittest" ? "S" : "W");
let searchParams = reactive({
  page: 1,
  pagesize: 30,
  question: "",
  answer: "",
  cate_id: undefined,
  case_state: 0,
  case_result: 0,
});
const total = ref(0);

const reset = () => {
  searchParams.case_result = 0;
  searchParams.question = "";
  searchParams.answer = "";
  searchParams.cate_id = undefined;
  searchParams.case_state = 0;
};

copyData(searchParams, route.query, "cate_id");

let pagelist = ref([]);

const search = (type) => {
  if (type == "init") {
    searchParams.page = 1;
  }
  testcasepagination(searchParams, TEST_TYPE).then((res) => {
    let arr = res.rows || [];
    pagelist.value = arr;
    total.value = res.total_records;
  });
  if (type != "noquery" && route.path == "/test") {
    let query = { ...route.query, ...searchParams };
    router.replace({ path: route.path, query: query });
  }
};

search();




const scrollbarRef = ref(null);




const dataSource = ref([]);
const treeSelect = ref(null);
const checkType = async (item) => {
  searchParams.cate_id = item.id;
  search("init");
};

const searchCate = () => {
  testcate({}, TEST_TYPE)
    .then(async (res) => {
      dataSource.value = res || [];
      await nextTick();
      treeSelect.value.setCurrentKey(parseInt(searchParams.category_id));
    })
    .catch((err) => {
      // if (err.response.data && err.response.data.detail == "知识库类目不存在") {
      //   dataSource.value = [];
      // }
    });
};
searchCate();
const isShowAdd = ref(false);
const addparam = reactive({ name: "", color: "", id: 0 });
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
  addparam.cate_name = item.name || "";
  addparam.color = item.color || generateRandomColor();
  if (type == "child") {
    // 添加子节点
    addparam.pid = item.id;
    addparam.cate_name = "";
    addparam.id = undefined;
    addparam.color = generateRandomColor();
  }
  isShowAdd.value = true;
  setTimeout(() => {
    inputRef.value.focus();
  }, 400);
};
const subaddfn = () => {
  if (!addparam.color) {
    _this.$message("请选择分类颜色", "error");
    return false;
  }
  if (!addparam.cate_name) {
    inputRef.value.focus();
    return false;
  }
  testcateadd(addparam, TEST_TYPE)
    .then((res) => {
      _this.$message("操作成功");
      isShowAdd.value = false;
      searchCate();
    })
    .catch((err) => { });
};

const delTypefn = (item) => {
  _this.$confirm("确定要删除所选数据?").then((res) => {
    testcatedelete({ id: item.id }, TEST_TYPE).then((res) => {
      _this.$message("删除成功");
      searchCate();
    });
  });
};

const isShowAddDialog = ref(false);
const editparam = ref({});
const editfn = (item) => {
  editparam.value = item;
  isShowAddDialog.value = true;
};

// 参数配置
const isShowOptDialog = ref(false);
const optformparam = reactive({
  id: "",
  id1: "",
  curTestType: 2,
  llm_id: "",
  workflow_id: "",
  prompt_id: "",
  prompt_name: "",
  is_forced: false,
});
const optformparamSave = ref({});
const applist = ref([]);

const getLocal = (data) => {
  let key = "testoptformparamSave";
  if (data) {
    // 设置
    localStorage.setItem(key, JSON.stringify(data));
  } else {
    if (localStorage.getItem(key)) {
      // 获取
      optformparamSave.value = JSON.parse(localStorage.getItem(key));
    }
  }
};

getLocal();

import { cloneDeep } from "lodash"; // 引入lodash库的cloneDeep方法进行深拷贝

const optform = ref();
const subopt = async (formEl) => {
  if (!formEl) return;
  await formEl.validate((valid, fields) => {
    if (valid) {
      if (optformparam.curTestType == 1) {
      } else {
        if (!optformparam.workflow_id) {
          _this.$message("请选择流程", "error");
          return false;
        }
      }
      if (!optformparam.llm_id) {
        _this.$message("请选择评测大模型", "error");
        return false;
      }
      if (!optformparam.prompt_id) {
        _this.$message("请选择提示词", "error");
        return false;
      }
      optformparamSave.value = cloneDeep(optformparam);
      getLocal(optformparamSave.value);
      // 使用深拷贝
      isShowOptDialog.value = false;
      if (waitids.value.length > 0) {
        testfn(waitids.value);
      }
    }
  });
};
const openOptDialog = async (ids) => {
  copyData(optformparam, optformparamSave.value);
  waitids.value = ids || [];
  isShowOptDialog.value = true;
};

const checkList = ref([]);
const drawer = ref(false);
const opendrawer = () => {
  if (isShowAddDialog.value) {
    checkList.value = [{ id: editparam.value.prompt_id }];
  } else {
    checkList.value = [{ id: optformparam.prompt_id }];
  }
  drawer.value = true;
};

const appsubfn = (itemlist) => {
  drawer.value = false;
  checkList.value = [];
  if (isShowAddDialog.value) {
    editparam.value.prompt_id = itemlist[0].id;
    editparam.value.prompt_name = itemlist[0].name;
  } else {
    optformparam.prompt_id = itemlist[0].id;
    optformparam.prompt_name = itemlist[0].name;
  }
};
const resetoptformparam = (type) => {
  optformparam.id = "";
  optformparam.is_forced = "";
  optformparam.id1 = "";
  optformparam.llm_id = "";
  optformparam.workflow_id = "";
  optformparam.curTestType = 2;
  optformparam.prompt_id = "";
  optformparam.prompt_name = "";
  if (type) {
    optformparamSave.value = {};
    getLocal(optformparamSave.value);
  }
};

const multipleSelection = ref([]);
const handleSelectionChange = (val) => {
  multipleSelection.value = val;
};

const waitids = ref([]);
const testfn = async (ids) => {
  if (!ids) {
    // 批量执行
    if (multipleSelection.value.length == 0) {
      _this.$message("请选择测试用例", "error");
      return false;
    }
    ids = [];
    multipleSelection.value.forEach((item) => {
      ids.push(item.id);
    });
  }
  if (!optformparamSave.value.curTestType) {
    _this.$message("请先配置参数，再执行测试", "error");

    openOptDialog(ids);
    return false;
  }

  waitids.value = [];

  let params = {
    ids: ids,
  };
  if (optformparamSave.value.curTestType == 1) {
    params.app_id = optformparamSave.value.id;
  } else {
    params.workflow_id = optformparamSave.value.workflow_id;
  }

  params.evaluation_llm_id = optformparamSave.value.llm_id;
  params.evaluation_prompt_id = optformparamSave.value.prompt_id;
  params.evaluation_prompt_name = optformparamSave.value.prompt_name;
  params.is_forced = optformparamSave.value.is_forced;

  testcasebatch_execute(params, TEST_TYPE)
    .then((res) => {
      if (res) {
        _this.$message("测试任务提交成功");
        search();
      }
    })
    .catch((err) => { });
};

// 运行记录

const testcaseresultfn = async (id) => {
  router.push({ path: "/logdetail", query: { id: id, fpath: route.fullPath } });
};

const delfn = (item) => {
  _this.$confirm("确定要删除所选数据?").then((res) => {
    testcasedelete({ id: item.id }, TEST_TYPE).then((res) => {
      _this.$message("删除成功");
      search();
    });
  });
};
const tableRef = ref(null);
const getCheckList = () => {
  return multipleSelection.value;
};
const setCehckList = (rows) => {
  if (rows) {
    rows.forEach((row) => {
      tableRef.value?.toggleRowSelection(row, undefined);
    });
  } else {
    tableRef.value?.clearSelection();
  }
};

const llmlist = ref([]);
//  获取大模型配置
model_configall({ page: 1, pagesize: 10000 }, TEST_TYPE).then((res) => {
  llmlist.value = res || [];
});
const workflowlist = ref([]);
workflow({ page: 1, pagesize: 10000 }, TEST_TYPE).then((res) => {
  let arr = res.rows || [];
  workflowlist.value = arr;
});

const runresult = ref({});
const showTest = ref(false);


const subDialogfn = (res) => {
  _this.$message("操作成功");
  search();
  isShowAddDialog.value = false;
};

const openCompDetail = (id, type) => {
  if (!id) return false;
  runresult.value = { id: id };
  showTest.value = true;
};

const isShowChangeTree = ref(false)
const subChangeTree = (data) => {
  move_cate({
    source_cate_id: data.curcateData.id,
    target_cate_id: data.curcateData1.id,
    tag: 'W'
  }).then((res) => {
    _this.$message("操作成功");
    isShowChangeTree.value = false;
    search();
  })
}

const showyxjl = ref(false)
const showyxjlid = ref(0)

defineExpose({ getCheckList, setCehckList });
</script>

<template>
  <div class="pagelistbox">
    <div class="c-titlebox">
      <span class="title">流程测试</span>
    </div>
    <div class="c-bodybox">
      <div class="catebox leftbox">
        <div class="topbtns">
          <span class="title">用例库</span>
          <el-button @click="checkType({ id: undefined })" class="on noradius" plain>
            <span class="iconfont icon-anniu-zhankai"></span>
            查看全部
          </el-button>

        </div>

        <div class="treebox contain">
          <el-scrollbar>
            <div class="el-tree el-tree--highlight-current" role="tree" style="width: 100%">
              <div class="el-tree-node" :class="{ 'is-current': searchParams.cate_id == 0 }">
                <div class="el-tree-node__content" style="padding-left: 0px">
                  <div @click="checkType({ id: 0 })" style="padding-left: 35px" class="custom-tree-node">
                    <div class="item">
                      <span class="c-color radius" :style="'background-color:#ff0000'"></span>未分类
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <el-tree ref="treeSelect" style="width: 100%" :data="dataSource" node-key="id" empty-text="暂无测试类目信息"
              highlight-current :current-node-key="searchParams.cate_id ? parseInt(searchParams.cate_id) : undefined"
              default-expand-all @node-click="checkType" :expand-on-click-node="false">
              <template #default="{ node, data }">
                <div :title="data.name" class="custom-tree-node">
                  <div class="item">
                    <span class="c-color radius" :style="'background-color:' + data.color"></span>
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
            @click="addTypefn({ name: '', color: '', id: 0 })"><span class="iconfont icon-liebiao-xinzeng"></span>
            新增用例库</el-button>
        </div>

      </div>

      <div v-initTableHeight class="c-tablebox tableboxContain c-tooltip rightbox">
        <div style="margin-left: 24px;margin-right: 24px;" class="c-top-searchbox c-js-item">
          <el-form :model="searchParams" ref="searchFormRef" inline class="demo-form-inline">
            <el-form-item label="问题" prop="question">
              <el-input clearable v-model="searchParams.question" type="text"></el-input>
            </el-form-item>
            <el-form-item label="结果" prop="case_result">
              <el-select style="width: 160px" clearable v-model="searchParams.case_result" placeholder="">
                <el-option label="请选择" :value="0" />
                <el-option label="未测试" :value="1001" />
                <el-option label="成功" :value="2001" />
                <el-option label="失败" :value="3001" />
              </el-select>
            </el-form-item>

            <el-form-item label="状态" prop="case_state">
              <el-select style="width: 160px" clearable v-model="searchParams.case_state" placeholder="">
                <el-option label="请选择" :value="0" />
                <el-option label="准备就绪" :value="1001" />
                <el-option label="测试中" :value="2001" />
                <el-option label="测试完成" :value="3001" />
              </el-select>
            </el-form-item>
            <el-form-item label="回答" prop="answer">
              <el-input clearable v-model="searchParams.answer" type="text"></el-input>
            </el-form-item>
          </el-form>
          <div class="rbox">

            <el-button @click="search('init')" type="primary">查询</el-button>
            <el-button @click="reset()" plain>重置</el-button>

          </div>
        </div>
        <div class="topbtns tl c-js-item">
          <el-button @click="
            editfn({
              id: null,
              cate_id: null,
              message_history_id: null,
              workflow_log_id: null,
              question: '',
              message_history: '',
              right_answer: '',
              note: '',
            })
            " type="primary">新增</el-button>
          <el-button @click="isShowChangeTree = true" plain>调整类目</el-button>
          <el-button @click="testfn()" type="primary" plain>批量测试</el-button>
          <el-button @click="openOptDialog()" style="background: rgba(22,93,255,0.1);color:var(--el-color-primary)"
            plain>参数配置
            <span v-if="optformparamSave.curTestType" style="color:var(--el-text-color-regular)" title="删除已配置参数"
              @click.stop="resetoptformparam(true)" class="iconfont icon-guanbi"></span>
          </el-button>

        </div>
        <div class="bodybox c-js-body">

          <div class="contain">
            <el-table tooltip-effect="light" border :data="pagelist" style="width: 100%"
              :max-height="store.getters.innerHeight - 293" @selection-change="handleSelectionChange" ref="tableRef">
              <el-table-column fixed="left" type="selection" width="40" />
              <el-table-column prop="id" width="70" label="id" />

              <el-table-column min-width="160" label="问题">
                <template #default="scope">
                  <el-popover v-if="scope.row.question" placement="top-start" :width="500" trigger="hover">
                    <template #reference>
                      <div class="ellipsis2">
                        <span class="c-primary-btn c-mini">问</span>
                        {{ scope.row.question }}
                      </div>
                    </template>

                    <div style="margin: 0 -20px;">
                      <el-scrollbar max-height="400">
                        <div v-html="scope.row.question.replace(/\n/g, '<br>')" style="margin:0 20px;">
                        </div>
                      </el-scrollbar>
                    </div>
                  </el-popover>
                </template>
              </el-table-column>

              <el-table-column min-width="160" label="参考答案">
                <template #default="scope">
                  <el-popover v-if="scope.row.right_answer" placement="top-start" :width="500" trigger="hover">
                    <template #reference>
                      <div class="ellipsis2">
                        <span class="c-success-btn c-mini">参</span>
                        {{ scope.row.right_answer }}
                      </div>
                    </template>

                    <div style="margin: 0 -20px;">
                      <el-scrollbar max-height="400">
                        <div v-html="scope.row.right_answer.replace(/\n/g, '<br>')" style="margin:0 20px;">
                        </div>
                      </el-scrollbar>
                    </div>
                  </el-popover>
                </template>
              </el-table-column>

              <el-table-column min-width="160" label="最终回答">
                <template #default="scope">
                  <div v-if="scope.row.test_result_answer"
                    @click="openCompDetail(scope.row.last_test_workflow_log_id, 1)">
                    <el-popover v-if="scope.row.test_result_answer" placement="top-start" :width="500" trigger="hover">
                      <template #reference>
                        <div class="ellipsis2">
                          <span class="c-warn-btn c-mini">终</span>
                          {{ scope.row.test_result_answer }}
                        </div>
                      </template>

                      <div style="margin: 0 -20px;">
                        <el-scrollbar max-height="400">
                          <div v-html="scope.row.test_result_answer.replace(/\n/g, '<br>')" style="margin:0 20px;">
                          </div>
                        </el-scrollbar>
                      </div>
                    </el-popover>
                  </div>
                </template>
              </el-table-column>

              <el-table-column min-width="160" label="备注">
                <template #default="scope">
                  <el-popover v-if="scope.row.note" placement="top-start" :width="500" trigger="hover">
                    <template #reference>
                      <div class="ellipsis">
                        {{ scope.row.note }}
                      </div>
                    </template>

                    <div style="margin: 0 -20px;">
                      <el-scrollbar max-height="400">
                        <div v-html="scope.row.note.replace(/\n/g, '<br>')" style="margin:0 20px;">
                        </div>
                      </el-scrollbar>
                    </div>
                  </el-popover>
                </template>
              </el-table-column>





              <el-table-column width="100" label="测试结果">
                <template #default="scope">
                  <span v-if="scope.row.test_result == 2001" class="c-success-btn">成功</span>
                  <span v-if="scope.row.test_result == 1001" class="c-plain-btn">未测试</span>
                  <span v-if="scope.row.test_result == 3001" class="c-danger-btn">失败</span>
                </template>
              </el-table-column>
              <el-table-column width="100" label="测试状态">
                <template #default="scope">
                  <span v-if="scope.row.test_state == 3001" class="c-success-btn">测试完成</span>
                  <span v-if="scope.row.test_state == 2001" class="c-primary-btn">测试中</span>
                  <span v-if="scope.row.test_state == 1001" class="c-plain-btn">准备就绪</span>
                </template>
              </el-table-column>
              <el-table-column width="160" label="运行记录">
                <template #default="scope">

                  <span @click="showyxjlid = scope.row.id;showyxjl=true;" class="c-pointer c-flex"
                    v-if="scope.row.test_result != 1001">
                    <span style="color: var(--el-color-primary);" class="iconfont icon-yunhangjilu"></span>运行记录({{
                      scope.row.test_count }})
                  </span>
                </template>
              </el-table-column>
              <el-table-column width="100" align="center" label="是否审核">
                <template #default="scope">
                  <span v-if="scope.row.is_marked" class="c-success-btn">已审核</span>
                  <span v-else class="c-plain-btn">未审核</span>
                </template>
              </el-table-column>
              <el-table-column width="100" align="center" label="是否更正">
                <template #default="scope">
                  <span v-if="scope.row.is_modified" class="c-success-btn">已更正</span>
                  <span v-else class="c-plain-btn">未更正</span>
                </template>
              </el-table-column>

              <el-table-column width="160" align="center" label="创建时间">
                <template #default="scope">
                  {{
                    getTime(scope.row.created_at)
                  }}
                </template>
              </el-table-column>
              <el-table-column width="160" align="center" label="最后测试时间">
                <template #default="scope">
                  {{
                    getTime(scope.row.last_test_time)
                  }}
                </template>
              </el-table-column>

              <el-table-column fixed="right" width="240" align="right" label="操作">
                <template #default="scope">

                  
                  <div @click="editfn(scope.row)" class="c-table-ibtn">
                    <span class="iconfont icon-xiugai"></span>
                    修改
                  </div>
                  <div @click="testfn([scope.row.id])" class="c-table-ibtn">
                    <span class="iconfont icon-liebiao-ceshi"></span>
                    测试
                  </div>
                  <div v-if="scope.row.workflow_log_id" @click="openCompDetail(scope.row.workflow_log_id, 1)"
                    class="c-table-ibtn">
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





  <el-dialog align-center v-model="isShowAdd" :title="addparam.id ? '修改用例库' : '新增用例库'" width="500">
    <el-form ref="formRef" style="text-align:left;" :model="addparam" label-width="auto" label-position="top"
      class="demo-dynamic">
      <el-form-item prop="cate_name" label="分类名称" :rules="[
        {
          required: true,
          message: '请输入分类名称',
          trigger: 'blur',
        },
      ]">
        <el-input v-model="addparam.cate_name" ref="inputRef" autofocus
          style="width: calc(100% - 42px); margin-right: 10px" placeholder="请输入分类名称" />
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

  <el-dialog align-center v-model="isShowOptDialog" title="配置参数" width="700">
    <el-form ref="optform" :model="optformparam" label-width="auto" inline label-position="top" class="demo-dynamic tl">
      <el-form-item style="width:calc(50% - 8px);margin-right:16px;" prop="type" label="测试分类">
        <el-input disabled value="流程测试" autocomplete="off" />
      </el-form-item>
      <el-form-item style="width:calc(50% - 8px);margin-right:0;" prop="type" label="">
        <template #label>
              使用的流程
              <el-tooltip popper-class="c-flowtip" class="item" effect="dark"
                content='默认流程： 该测试按照 原流程执行。指定流程：按照人工指定的流程执行，注意输入参数要和原流程一致。' placement="top">
                <span style="position: relative;top: 1px;" class="iconfont icon-bangzhu"></span>
              </el-tooltip>
            </template>
        <el-radio-group v-model="optformparam.is_forced">
          <el-radio :value="true">按指定的流程执行</el-radio>
          <el-radio :value="false">按默认流程执行</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item style="width:calc(50% - 8px);margin-right:16px;" prop="workflow_id" label="流程选择" :rules="[
        {
          required: true,
          message: '请选择流程',
          trigger: 'change',
        },
      ]">
        <el-select v-model="optformparam.workflow_id" class="val" filterable placeholder="请选择流程">
          <el-option v-for="item in workflowlist" :value="parseInt(item.id, 10)" :label="item.name"></el-option>
        </el-select>
      </el-form-item>

      <el-form-item style="width:calc(50% - 8px);margin-right:0px;" prop="llm_id" label="" :rules="[
        {
          required: true,
          message: '请选大模型',
          trigger: 'change',
        },
      ]">
      <template #label>
        评测大模型
              <el-tooltip popper-class="c-flowtip" class="item" effect="dark"
                content='用来对输出结果进行打分的大模型，按照提示词对输出和标准答案进行对比打分。' placement="top">
                <span style="position: relative;top: 1px;" class="iconfont icon-bangzhu"></span>
              </el-tooltip>
            </template>
        <el-select v-model="optformparam.llm_id" class="val" filterable placeholder="请选择大模型">
          <el-option v-for="item in llmlist" :value="parseInt(item.id, 10)" :label="item.name"></el-option>
        </el-select>
      </el-form-item>

      <el-form-item prop="prompt_id" style="width:100%;margin-right:0;" :rules="[
        {
          required: true,
          message: '请选提示词',
        },
      ]" label="提示词">
        <div @click="opendrawer()" class="c-switchbox pointer">
          <span v-if="optformparam.prompt_name">{{
            optformparam.prompt_name
          }}</span>
          <span class="placeholder" v-else>请选择提示词</span>
          <span style="position: absolute;top: -36px;right: 0;color:var(--el-color-primary)" class="c-pointer">选择</span>
        </div>
      </el-form-item>
    </el-form>
    <template #footer>
      <div class="dialog-footer">
        <el-button plain @click="isShowOptDialog = false"> 取消 </el-button>
        <el-button type="primary" @click="subopt(optform)"> 确定 </el-button>
      </div>
    </template>
  </el-dialog>

  <el-drawer v-model="drawer" size="90%" title="" direction="rtl">
    <CompApp v-if="drawer" @subfn="appsubfn" :isCheck="true" :checkList="checkList"></CompApp>
  </el-drawer>

  <addtestDialog v-model="isShowAddDialog" TEST_TYPE="W" :item="editparam" :curResult="editparam" :title="editparam.id ? '修改流程测试' : '添加流程测试'"
    @subfn="subDialogfn"></addtestDialog>

  <result v-model="showTest" :data="runresult"></result>


  <ChangeTree :dataSource="dataSource" v-model="isShowChangeTree" @subfn="subChangeTree"></ChangeTree>


  <el-drawer v-model="showyxjl" title="运行记录" direction="rtl" :close-on-click-modal="true"
  size="90%">
        <logdetail v-if="showyxjlid" :id="showyxjlid"></logdetail>
  </el-drawer>
</template>
<style scoped>
.isShowAddDialogBox {
  height: 660px;
}

.qusbox {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.qusbox .qusitem {
  width: calc(100% - 100px);
}

.typelist {
  width: 100%;
}

.testcaseresultbox {
  display: block;
  height: 600px;
}

.testcaseresultbox .item {
  display: block;
  border: 1px solid #f1f1f1;
  border-radius: 5px;
  margin-bottom: 10px;
  text-align: left;
}

.testcaseresultbox .scroebox {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 5px 10px;
  color: #aaa;
  font-size: 12px;
}

.testcaseresultbox .test_answer {
  padding: 10px;
  font-size: 14px;
}

.topbtns {
  padding: 0 24px 20px 24px;
  display: flex;
  align-items: center;
}

.topbtns .icon-shanchu {
  cursor: pointer;
  color: var(--el-color-danger);
}


.flex {
  display: flex;
  align-items: center;
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



.times {
  color: #999;
  font-size: 12px;
}


.icon-canshu {
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


.tableboxContain .btnbox {
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
}

.tableboxContain .bodybox {
  height: calc(100% - 120px);
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



.icon-shugui {
  color: var(--chakra-colors-primary-600);
  font-size: 20px;
}
</style>
