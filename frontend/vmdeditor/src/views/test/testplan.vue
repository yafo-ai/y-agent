<script setup>
import { ref, nextTick, shallowRef, onActivated, reactive, watch } from "vue";
import {
  testplanpagination,
  testplanbatch_execute,
  testplanrelation_case,
  testplanrelation_cate,
  testcatedelete,
  testplandelete,
  testplanadd,
  testcate,
  testcaseresult,
  testplanrelation_cate_case,
  model_configall,
  workflow,
} from "@/api/api";
import { cloneDeep } from "lodash"; // 引入lodash库的cloneDeep方法进行深拷贝
import { transferString, copyData } from "@/assets/utils/util";
import { formatDate } from "@/assets/utils/timefn";

import { useStore } from "vuex";
import { onBeforeRouteLeave, useRoute, useRouter } from "vue-router";
import { goback, getTime } from "@/components/comp.js";
import CompTest from "@/views/test/list.vue";
import CompUnitTest from "@/views/test/unittest.vue";

import CompApp from "@/views/app/list.vue";
import icon from "@/components/icon.vue"
const route = useRoute();
const router = useRouter();
const store = useStore();

const drawer = ref(false);

let searchParams = reactive({
  page: 1,
  pagesize: 30,
  plan_name: "",
  plan_state: 0,
});
const total = ref(0);

const reset = () => {
  searchParams.plan_state = 0;
  searchParams.plan_name = "";
};

copyData(searchParams, route.query);

let pagelist = ref([]);

const search = (type) => {
  if (type == "init") {
    searchParams.page = 1;
  }
  testplanpagination(searchParams).then((res) => {
    let arr = res.rows || [];
    pagelist.value = arr;
    total.value = res.total_records;
  });
  if (type != "noquery") {
    let query = { ...route.query, ...searchParams };
    router.replace({ path: route.path, query: query });
  }
};

search();

const meslist = ref([]);

const scrollbarRef = ref(null);

const dataSource = ref([]);
const dataSourceS = ref([]);

// 使用函数
const testparamRef1 = ref();
const formRef1 = ref();
const subeditfn = async (formEl) => {
  if (!formEl) return;
  formEl.validate((valid, fields) => {
    if (valid) {
      // 添加到语料

      if (!editparam.unit_llm_id && editparam.tag == "S") {
        _this.$message("请选择执行大模型", "error");
        return false;
      }

      if (!editparam.evaluation_llm_id) {
        _this.$message("请选择评测大模型", "error");
        return false;
      }

      if (!editparam.evaluation_prompt_id) {
        _this.$message("请选择提示词", "error");
        return false;
      }
      testplanadd({
        id: editparam.id,
        name: editparam.name,
        caption: editparam.caption,
        tag: editparam.tag || "W",
        note: editparam.note,
        workflow_id: editparam.workflow_id || undefined,
        unit_llm_id: editparam.unit_llm_id || undefined,
        evaluation_llm_id: editparam.evaluation_llm_id || undefined,
        evaluation_prompt_id: editparam.evaluation_prompt_id || undefined,
        app_id: editparam.app_id || undefined,
        is_forced: editparam.is_forced,
      })
        .then((res) => {
          if (res) {
            _this.$message("操作成功");
            isShowAddDialog.value = false;
            search();
          }
        })
        .catch((err) => { });
    }
  });
};
const curDatasource = ref([]);
const get_cateslist = async (fn) => {
  if (currowitem.value && currowitem.value.tag == "S") {
    if (dataSourceS.value.length < 1) {
      dataSourceS.value = await testcate({}, "S");
    }
    curDatasource.value = [
      { id: 0, name: "未分类", color: "#ff0000", pid: null, children: [] },
    ].concat(dataSourceS.value);
  } else {
    if (dataSource.value.length < 1) {
      dataSource.value = await testcate({}, "W");
    }
    curDatasource.value = [
      { id: 0, name: "未分类", color: "#ff0000", pid: null, children: [] },
    ].concat(dataSource.value);
  }

  fn && fn()
};
const isShowAddDialog = ref(false);
const editparam = reactive({
  id: 0,
  name: "",
  caption: "",
  note: "",
  app_id: "",
  workflow_id: "",
  is_forced: false,
  evaluation_llm_id: "",
  evaluation_prompt_id: "",
  evaluation_prompt_name: "",
  tag: "W",
  // curTestType:1,
});
const checkList = ref([]);
const appsubfn = (itemlist) => {
  drawer.value = false;
  checkList.value = [];
  editparam.evaluation_prompt_id = itemlist[0].id;
  editparam.evaluation_prompt_name = itemlist[0].name;
  testparam.value.evaluation_prompt_id = itemlist[0].id;
  testparam.value.evaluation_prompt_name = itemlist[0].name;
};

const treeSelect1 = ref(null);
const editfn = async (item) => {
  if (formRef1.value) {
    formRef1.value.clearValidate();
  }
  editparam.tag = item.tag || "W";
  editparam.id = item.id;
  editparam.name = item.name;
  editparam.is_forced = item.is_forced === undefined ? false : item.is_forced;
  editparam.caption = item.caption;
  editparam.note = item.note;
  editparam.unit_llm_id = item.unit_llm_id ? parseInt(item.unit_llm_id) : "";

  editparam.app_id = item.app_id ? parseInt(item.app_id) : "";
  editparam.workflow_id = item.workflow_id ? parseInt(item.workflow_id) : "";
  editparam.evaluation_llm_id = item.evaluation_llm_id
    ? parseInt(item.evaluation_llm_id)
    : "";
  editparam.evaluation_prompt_id = item.evaluation_prompt_id
    ? parseInt(item.evaluation_prompt_id)
    : "";
  editparam.evaluation_prompt_name = item.evaluation_prompt_name || "";

  // editparam.curTestType = editparam.app_id?1:2;
  isShowAddDialog.value = true;
};

// 参数配置

const multipleSelection = ref([]);
const handleSelectionChange = (val) => {
  multipleSelection.value = val;
};
const testfn = async (id, formEl) => {
  if (!formEl) return;
  formEl.validate((valid, fields) => {
    if (valid) {
      let params = { ...testparam.value };
      params.id = id;
      params.tag = undefined;
      testplanbatch_execute(params,curTestItem.value.is_continue).then((res) => {
        if (res) {
          isShowTestDialog.value = false;
          _this.$message("执行成功");
          search();
        }
      });
    }
  });
};

const curTestItem = ref(null);
const isShowTestDialog = ref(false);
const testparam = ref({
  plan_name: "",
  unit_llm_id: undefined,
  evaluation_llm_id: undefined,
  workflow_id: undefined,
  evaluation_prompt_id: "",
  evaluation_prompt_name: "",
  tag: "W",
});
const showTest = (item) => {
  curTestItem.value = item;
  testparam.value.tag = item.tag || 'W';
  testparam.value.unit_llm_id = undefined;

  testparam.value.workflow_id = undefined;
  testparam.value.evaluation_llm_id = item.evaluation_llm_id
    ? parseInt(item.evaluation_llm_id)
    : "";
  testparam.value.evaluation_prompt_id = item.evaluation_prompt_id
    ? parseInt(item.evaluation_prompt_id)
    : "";
  testparam.value.evaluation_prompt_name = item.evaluation_prompt_name;

  testparam.value.plan_name =
    item.name + " (" + formatDate(Date.now()) + ") " + "测试报告";
  isShowTestDialog.value = true;
};

const delfn = (item) => {
  _this.$confirm("确定要删除所选数据?").then((res) => {
    testplandelete({ id: item.id }).then((res) => {
      _this.$message("删除成功");
      search();
    });
  });
};
let timer = null;
const ylkDialog = ref(false);
const defaultCheckedKeys = ref([]);
const ylkDialogList = ref([]);
const currowitem = ref(null);
const openylkDialog = async (item) => {
  ylkDialogList.value = [];
  let res = await testplanrelation_cate_case({ id: item.id });
  if (res) {
    defaultCheckedKeys.value = res.relation_cate_ids;
    ylkDialogList.value = res.relation_cate_ids;
  }
  currowitem.value = item;
  get_cateslist(() => {
    initCheckList(defaultCheckedKeys.value)
  });
  ylkDialog.value = true;
};
const handleCheckChange = (data, isCheck) => {
  let cindex = -1;
  ylkDialogList.value.forEach((item, index) => {
    if (item == data.id) {
      cindex = index;
    }
  });

  if (isCheck) {
    // 选中
    if (cindex == -1) {
      ylkDialogList.value.push(data.id);
    }
  } else {
    // 取消选中
    if (cindex != -1) {
      ylkDialogList.value.splice(cindex, 1);
    }
  }

  clearTimeout(timer)
  timer = setTimeout(() => {
    let arr = []
    if (treeSelect1.value) {
      arr = treeSelect1.value.getCheckedKeys();
    }
    initCheckList(arr)
  }, 70)
};


const curCheckList = ref([])

const initCheckList = (ids = []) => {
  console.log(ids)
  if (!Array.isArray(ids) || !curDatasource.value) return;
  ylkDialogList.value = ids;
  const arr = cloneDeep(curDatasource.value);

  const processNode = (node) => {
    const isChecked = ids.includes(node.id);
    node.checked = isChecked;
    node.isshow = isChecked;

    if (node.children?.length) {
      let hasCheckedChild = false;
      node.children.forEach(child => {
        processNode(child);
        if (child.checked) hasCheckedChild = true;
      });

      if (!isChecked) {
        node.isshow = hasCheckedChild;
      }
    }
  };

  arr.forEach(processNode);
  curCheckList.value = arr;
};

const filterText = ref('')
watch(filterText, (val) => {
  treeSelect1.value?.filter(val)
})

const filterNode = (value, data) => {
  if (!value) return true
  return data.name.includes(value)
}

const subylkDialog = () => {
  // if (ylkDialogList.value.length == 0) {
  //   return false;
  // }
  testplanrelation_cate({ cates: ylkDialogList.value, id: currowitem.value.id })
    .then((res) => {
      ylkDialog.value = false;
      search();
    })
    .catch((err) => { });
};

const drawer1 = ref(false);
const CompTestref = ref();
const CompUnitTestref = ref();
const opendrawer = () => {
  drawer1.value = true;
};

const glDialog = ref(false);

const openglkDialog = async (item) => {
  CompTestrefList.value = [];
  let res = await testplanrelation_cate_case({ id: item.id });
  if (res) {
    CompTestrefList.value = res.case_models;
  }
  currowitem.value = item;
  glDialog.value = true;
};
const CompTestrefList = ref([]);
const initCompTestrefList = (list) => {
  if (CompTestrefList.value.length == 0) {
    CompTestrefList.value = list;
  } else {
    list.forEach((item) => {
      let index = -1;
      CompTestrefList.value.forEach((item2, index2) => {
        if (item2.id == item.id) {
          index = index2;
        }
      });
      if (index == -1) {
        // 不存在
        CompTestrefList.value.push(item);
      }
    });
  }
};
const subglkDialog = () => {
  if (currowitem.value.tag == "S") {
    initCompTestrefList(CompUnitTestref.value.getCheckList());
  } else {
    initCompTestrefList(CompTestref.value.getCheckList());
  }

  drawer1.value = false;
};

const subglkfn = (item) => {
  let list = CompTestrefList.value;
  // if (list.length == 0) {
  //   return false;
  // }
  let ids = [];
  list.forEach((item) => {
    ids.push(item.id);
  });
  testplanrelation_case({ cates: ids, id: currowitem.value.id })
    .then((res) => {
      glDialog.value = false;
      search();
    })
    .catch((err) => { });
};

const applist = ref([]);

const openCompDetail = (item) => {
  router.push({
    path: "/testplan/detail",
    query: { id: item.id, fpath: route.fullPath },
  });
};

const llmlist = ref([]);
//  获取大模型配置
model_configall({ page: 1, pagesize: 10000 }).then((res) => {
  llmlist.value = res || [];
});
const workflowlist = ref([]);
workflow({ page: 1, pagesize: 10000 }).then((res) => {
  let arr = res.rows || [];
  workflowlist.value = arr;
});

const validatorfn = (rule, value, callback) => {
  if (rule.field == "workflow_id" && !value) {
    if (editparam.app_id) {
      callback();
      return true;
    } else {
      callback(new Error("请选择流程"));
      return false;
    }
  }

  callback();
};
const tableRef = ref(null);
</script>

<template>
  <div class="pagelistbox">
    <div class="c-titlebox">
      <div class="title">测试计划</div>
      <div class="btns">
        <el-button @click="
          editfn({
            id: null,
            cate_id: null,
            message_history_id: null,
            question: '',
            message_history: '',
            right_answer: '',
            tag: 'W',
          })
          " plain size="small">新增流程测试计划</el-button>
        <el-button @click="
          editfn({
            id: null,
            cate_id: null,
            message_history_id: null,
            question: '',
            message_history: '',
            right_answer: '',
            tag: 'S',
          })
          " plain size="small">新增单元测试计划</el-button>
      </div>
    </div>

    <div class="c-top-searchbox ">
      <el-form :model="searchParams" ref="searchFormRef" inline class="demo-form-inline">
        <el-form-item label="名称" prop="question">
          <el-input clearable v-model="searchParams.plan_name" type="text"></el-input>
        </el-form-item>

        <el-form-item label="状态" prop="case_state">
          <el-select style="width: 160px" clearable v-model="searchParams.plan_state" placeholder="">
            <el-option label="请选择" :value="0" />
            <el-option label="准备就绪" :value="1001" />
            <el-option label="测试中" :value="2001" />
            <el-option label="测试完成" :value="3001" />
          </el-select>
        </el-form-item>
      </el-form>
      <div class="rbox">
        <div class="el-form-item asterisk-left">
          <!--v-if-->
          <div class="el-form-item__content">
            <el-button @click="search('init')" type="primary">查询</el-button>
            <el-button @click="reset()" plain>重置</el-button>
          </div>
        </div>
      </div>
    </div>

    <div class="c-tablebox tableboxContain c-tooltip">

      <div class="bodybox">
        <el-table ref="tableRef" tooltip-effect="light" border :data="pagelist" style="width: 100%"
          :max-height="store.getters.innerHeight - 193" @selection-change="handleSelectionChange">
          <!-- <el-table-column type="selection" width="40" /> -->
          <el-table-column prop="id" width="70" label="id" />

          <el-table-column label="计划名称">
            <template #default="scope">
              <div class="c-scroll-contain">
                {{ scope.row.name }}
              </div>
            </template>
          </el-table-column>

          <el-table-column label="介绍">
            <template #default="scope">
              <el-popover v-if="scope.row.caption" placement="top-start" :width="500" trigger="hover">
                <template #reference>
                  <div class="ellipsis">
                    {{ scope.row.caption }}
                  </div>
                </template>

                <div style="margin: 0 -20px;">
                  <el-scrollbar max-height="400">
                    <div v-html="scope.row.caption.replace(/\n/g, '<br>')" style="margin:0 20px;">
                    </div>
                  </el-scrollbar>
                </div>
              </el-popover>
            </template>
          </el-table-column>

          <el-table-column align="left" label="关联的测试库">
            <template #default="scope">


              <span style="cursor: pointer;" @click="openylkDialog(scope.row)">
                <span :class="scope.row.tag == 'S' ? 'c-success' : 'c-primary'"
                  class="iconfont icon-liebiao-yongli"></span>关联用例库({{ scope.row.cate_count }})
              </span>
            </template>
          </el-table-column>

          <el-table-column align="left" label="选择的用例">
            <template #default="scope">

              <span style="cursor: pointer;" @click="openglkDialog(scope.row)">
                <span :class="scope.row.tag == 'S' ? 'c-success' : 'c-primary'"
                  class="iconfont icon-liebiao-yongli"></span>关联用例({{ scope.row.case_count }})
              </span>

            </template>
          </el-table-column>

          <el-table-column width="100" label="状态">
            <template #default="scope">
              <div style="display: flex;">
              <span
                :class="{ 'c-plain-btn': scope.row.state == '准备就绪', 'c-success-btn': scope.row.state == '测试完成', 'c-primary-btn': scope.row.state == '测试中' }">{{
                  scope.row.state }}</span>

              <el-tooltip v-if="scope.row.error_msg" effect="light" placement="right"
                :content="'<div style=' + 'display:block;max-width:600px;' + ' class=' + 'c-danger' + '>' + scope.row.error_msg + '</div>'"
                raw-content>
                <span class="c-danger iconfont icon-gantanhao1"></span>
              </el-tooltip>
            </div>
            </template>
          </el-table-column>

          <el-table-column width="160" align="center" label="添加时间">
            <template #default="scope">
              {{ getTime(scope.row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column width="160" align="center" label="最后执行时间">
            <template #default="scope">
              {{
                getTime(scope.row.updated_at) || getTime(scope.row.created_at)
              }}
            </template>
          </el-table-column>

          <el-table-column width="260" align="right" label="操作">
            <template #default="scope">
              <div v-if="scope.row.state != '准备就绪'" @click="openCompDetail(scope.row)" class="c-table-ibtn">
                <span class="iconfont icon-liebiao-baogao"></span>
                查看报告
              </div>

              <div v-if="scope.row.is_continue" @click="showTest(scope.row)" class="c-table-ibtn">
                <span class="iconfont icon-liebiao-zhihang"></span>
                继续执行
              </div>
              <div v-else @click="showTest(scope.row)" class="c-table-ibtn">
                <span class="iconfont icon-liebiao-zhihang"></span>
                执行
              </div>

              <div @click="editfn(scope.row)" class="c-table-ibtn">
                <span class="iconfont icon-xiugai"></span>
                修改
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

  <el-dialog align-center v-model="isShowAddDialog" :close-on-click-modal="false" title="测试计划" width="800">
    <div class="isShowAddDialogBox c-scroll-contain">
      <el-scrollbar max-height="800">
        <el-form ref="formRef1" :model="editparam" style="width: 100%;" label-width="auto" inline label-position="top"
          class="demo-dynamic tl">
          <el-form-item style="width: 100%;margin-right: 0;" v-if="editparam.tag == 'W'" prop="type" label="">
            <template #label>
              使用的流程
              <el-tooltip popper-class="c-flowtip" class="item" effect="dark"
                content='默认流程： 该测试按照 原流程执行。指定流程：按照人工指定的流程执行，注意输入参数要和原流程一致。' placement="top">
                <span style="position: relative;top: 1px;" class="iconfont icon-bangzhu"></span>
              </el-tooltip>
            </template>
            <el-radio-group v-model="editparam.is_forced">
              <el-radio :value="true">按指定的流程执行</el-radio>
              <el-radio :value="false">按默认流程执行</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item style="width:calc(50% - 8px);margin-right:16px;" v-if="editparam.tag == 'W'" prop="workflow_id"
            label="流程选择" :rules="{
              trigger: 'blur',
              required: true,
              validator: validatorfn,
            }">
            <el-select clearable v-model="editparam.workflow_id" class="val" filterable placeholder="请选择流程">
              <el-option v-for="item in workflowlist" :value="parseInt(item.id, 10)" :label="item.name"></el-option>
            </el-select>
          </el-form-item>

          <el-form-item style="width:calc(50% - 8px);margin-right:16px;" v-if="editparam.tag == 'S'" prop="unit_llm_id"
            label="执行大模型" :rules="[
              {
                required: true,
                message: '请选择执行大模型',
                trigger: 'change',
              },
            ]">
            <el-select v-model="editparam.unit_llm_id" clearable class="val" filterable placeholder="请选择执行大模型">
              <el-option v-for="item in llmlist" :value="parseInt(item.id, 10)" :label="item.name"></el-option>
            </el-select>
          </el-form-item>

          <el-form-item style="width:calc(50% - 8px);margin-right:0;" prop="evaluation_llm_id" label="" :rules="[
            {
              required: true,
              message: '请选择评测大模型',
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
            <el-select v-model="editparam.evaluation_llm_id" clearable class="val" filterable placeholder="请选择评测大模型">
              <el-option v-for="item in llmlist" :value="parseInt(item.id, 10)" :label="item.name"></el-option>
            </el-select>
          </el-form-item>

          <el-form-item style="width:100%;margin-right:0;" prop="evaluation_prompt_id" :rules="[
            {
              required: true,
              message: '请选择提示词',
            },
          ]" label="提示词">


            <div @click="drawer = true; checkList = [{ id: editparam.evaluation_prompt_id }];"
              class="c-switchbox pointer">
              <span v-if="editparam.evaluation_prompt_id">{{
                editparam.evaluation_prompt_name
              }}</span>
              <span class="placeholder" v-else>请选择提示词</span>
              <span style="position: absolute;top: -36px;right: 0;color:var(--el-color-primary)"
                class="c-pointer">选择</span>
            </div>
          </el-form-item>

          <el-form-item style="width:100%;margin-right:0;" prop="name" label="计划名称" :rules="[
            {
              required: true,
              message: '请填写计划名称',
              trigger: 'blur',
            },
          ]">
            <el-input v-model="editparam.name" style="width: 100%" :rows="4" type="textarea" placeholder="请填写计划名称" />
          </el-form-item>

          <el-form-item style="width:100%;margin-right:0;" prop="caption" label="计划介绍">
            <el-input v-model="editparam.caption" style="width: 100%" :rows="4" type="textarea" placeholder="请填写计划介绍" />
          </el-form-item>

          <el-form-item style="width:100%;margin-right:0;" prop="note" label="计划备注">
            <el-input v-model="editparam.note" style="width: 100%" :rows="4" type="textarea" placeholder="请填写计划备注" />
          </el-form-item>
        </el-form>
      </el-scrollbar>
    </div>
    <template #footer>
      <div class="dialog-footer">
        <el-button plain @click="isShowAddDialog = false"> 取消 </el-button>
        <el-button type="primary" @click="subeditfn(formRef1)">
          确定
        </el-button>
      </div>
    </template>
  </el-dialog>

  <el-dialog align-center v-model="isShowTestDialog" title="执行测试计划" width="600">
    <div class="isShowAddDialogBox c-scroll-contain">
      <el-form ref="testparamRef1" style="width: 100%;" :model="testparam" label-width="auto" inline
        label-position="top" class="demo-dynamic tl">
        <el-form-item style="width:calc(50% - 8px);margin-right:16px;" v-if="testparam.tag == 'W'" prop="workflow_id"
          label="流程选择" :rules="{
            trigger: 'blur',
            required: true,
            validator: validatorfn,
          }">
          <el-select clearable v-model="testparam.workflow_id" class="val" filterable placeholder="请选择流程">
            <el-option v-for="item in workflowlist" :value="parseInt(item.id, 10)" :label="item.name"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item style="width:calc(50% - 8px);margin-right:16px;" v-if="testparam.tag == 'S'" prop="unit_llm_id"
          label="执行大模型" :rules="[
            {
              required: true,
              message: '请选择执行大模型',
              trigger: 'change',
            },
          ]">
          <el-select v-model="testparam.unit_llm_id" clearable class="val" filterable placeholder="请选择执行大模型">
            <el-option v-for="item in llmlist" :value="parseInt(item.id, 10)" :label="item.name"></el-option>
          </el-select>
        </el-form-item>

        <el-form-item style="width:calc(50% - 8px);margin-right:0;" prop="evaluation_llm_id" label="评测大模型" :rules="[
          {
            required: true,
            message: '请选择评测大模型',
            trigger: 'change',
          },
        ]">
          <el-select v-model="testparam.evaluation_llm_id" clearable class="val" filterable placeholder="请选择评测大模型">
            <el-option v-for="item in llmlist" :value="parseInt(item.id, 10)" :label="item.name"></el-option>
          </el-select>
        </el-form-item>

        <el-form-item style="width:100%;margin-right:0;" prop="evaluation_prompt_id" :rules="[
          {
            required: true,
            message: '请选择提示词',
          },
        ]" label="提示词">

          <div @click="drawer = true; checkList = [{ id: testparam.evaluation_prompt_id }];"
            class="c-switchbox pointer">
            <span v-if="testparam.evaluation_prompt_id">{{
              testparam.evaluation_prompt_name
            }}</span>
            <span class="placeholder" v-else>请选择提示词</span>
            <span style="position: absolute;top: -36px;right: 0;color:var(--el-color-primary)"
              class="c-pointer">选择</span>
          </div>
        </el-form-item>

        <el-form-item style="width:100%;margin-right:0;" prop="plan_name" label="测试报告名称" :rules="[
          {
            required: true,
            message: '请填写测试报告名称',
            trigger: 'blur',
          },
        ]">
          <el-input v-model="testparam.plan_name" style="width: 100%" :rows="4" type="textarea" placeholder="请填写计划名称" />
        </el-form-item>
      </el-form>
    </div>
    <template #footer>
      <div class="dialog-footer">
        <el-button plain @click="isShowTestDialog = false"> 取消 </el-button>
        <el-button type="primary" @click="testfn(curTestItem.id, testparamRef1)">
          确定
        </el-button>
      </div>
    </template>
  </el-dialog>

  <el-dialog align-center v-model="ylkDialog" title="计划关联用例库" width="900">
    <div class="ylkDialogContent">
      <div class="lbox">
        <div style="margin: 0px 20px 20px 20px;" class="c-treeinpbox">
          <span class="iconfont icon-sousuo1"></span>
          <input v-model="filterText" type="text" placeholder="搜索菜单名称">
        </div>
        <div class="treecontian">
          <el-scrollbar>
            <el-tree ref="treeSelect1" :data="curDatasource" node-key="id" show-checkbox
              :filter-node-method="filterNode" @check-change="handleCheckChange"
              :default-checked-keys="defaultCheckedKeys" empty-text="暂无测试类目信息" highlight-current default-expand-all
              :expand-on-click-node="false">
              <template #default="{ node, data }">
                <div :title="data.name" class="custom-tree-node">
                  <div class="item">
                    <span class="c-color" :style="'background-color:' + data.color"></span>
                    <p class="ellipsis">{{ data.name }}</p>
                  </div>
                </div>
              </template>
            </el-tree>

          </el-scrollbar>
        </div>
      </div>
      <div class="rbox topbox">

        <div style="height: 33px;" class="totalbox">
          <span class="num">已选择：{{ ylkDialogList.length }}</span>
          <span @click="treeSelect1.setCheckedKeys([])" class="c-btn-text">清空选择</span>
        </div>

        <div style="height: calc(100% - 40px);" class="checklistbox">
          <el-scrollbar>
            <div v-for="item in curCheckList.filter((item) => item.isshow)" :key="item.id" class="item">
              <div class="citem">
                <div class="pname">{{ item.name }} </div>
                <span v-if="item.checked && item.isshow" @click="treeSelect1.setChecked(item.id, false, true)"
                  class="iconfont icon-guanbi"></span>
              </div>
              <div v-if="item.children" class="citem" v-for="(citem) in item.children.filter((item) => item.isshow)"
                :key="citem.id">
                <div class="name">{{ citem.name }}</div>
                <span @click="treeSelect1.setChecked(citem.id, false, true)" class="iconfont icon-guanbi"></span>
              </div>
            </div>
          </el-scrollbar>
        </div>

      </div>
      <!--    -->

    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button plain @click="ylkDialog = false"> 取消 </el-button>
        <el-button type="primary" @click="subylkDialog()"> 保存 </el-button>
      </div>
    </template>
  </el-dialog>

  <el-dialog align-center v-model="glDialog" title="计划关联用例" width="1100">
    <div class="glDialogboxContent re">
      <el-button style="position: absolute; right: 50px; top: 12px;" @click="opendrawer()" plain
        class="on">新增关联用例</el-button>
      <div class="glDialogbox">
        <el-scrollbar>
          <el-table tooltip-effect="light" border :data="CompTestrefList" style="width: 100%">
            <el-table-column prop="id" width="70" label="id" />

            <el-table-column label="问题">
              <template #default="scope">
                <el-popover v-if="scope.row.question" placement="top-start" :width="500" trigger="hover">
                  <template #reference>
                    <div class="ellipsis">
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
            <el-table-column label="参考答案">
              <template #default="scope">
                <el-popover v-if="scope.row.right_answer" placement="top-start" :width="500" trigger="hover">
                  <template #reference>
                    <div class="ellipsis">
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
            <el-table-column width="100" align="center" label="操作">
              <template #default="scope">

                <div @click="CompTestrefList.splice(scope.$index, 1)" class="c-table-ibtn c-btn-del">
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
        </el-scrollbar>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="glDialog = false" plain>取消</el-button>
        <el-button @click="subglkfn()" type="primary">保存</el-button>
      </div>
    </template>
  </el-dialog>

  <el-drawer v-model="drawer1" :with-header="false" :destroy-on-close="true" size="90%" title="选择测试用例" direction="rtl">
    <div class="testbox">
      <CompUnitTest v-if="currowitem.tag == 'S'" TEST_TYPE="S" ref="CompUnitTestref"></CompUnitTest>
      <CompTest TEST_TYPE="W" v-else ref="CompTestref"></CompTest>
    </div>
    <div class="drawerbtn">
      <el-button @click="drawer1 = false" plain>取消</el-button>
      <el-button @click="subglkDialog()" type="primary">保存</el-button>
    </div>
  </el-drawer>

  <el-drawer v-model="drawer" size="90%" title="" direction="rtl">
    <CompApp v-if="drawer" @subfn="appsubfn" :isCheck="true" :checkList="checkList"></CompApp>
  </el-drawer>
</template>
<style scoped>
.isShowAddDialogBox {
  width: 100%;
}

.glDialogboxContent .btns {
  padding-bottom: 10px;
  text-align: left;
}

.glDialogbox {
  height: 600px;
}

.testbox {
  height: calc(100% - 45px);
}

.drawerbtn {
  text-align: right;
  padding-top: 10px;
}

.ylkDialogContent {
  height: 700px;
  display: flex;
  margin: -16px -24px;
}

.ylkDialogContent .rbox,
.ylkDialogContent .lbox {
  display: block;
  width: 50%;
  height: 100%;
  box-sizing: border-box;
  padding: 16px 0;
}

.ylkDialogContent .lbox {
  border-right: 1px solid var(--el-border-color);

}

.ylkDialogContent .treecontian {
  height: calc(100% - 40px);
}

.ylkDialogContent .rbox {
  padding: 16px 20px;
}

.topbtns {
  padding-bottom: 20px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.topbtns .icon-shanchu {
  cursor: pointer;
  color: var(--el-color-danger);
}

.flex {
  display: flex;
  align-items: center;
}






.searchbox {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  box-sizing: border-box;
  text-align: left;
  width: calc(100% - 100px);
  margin-bottom: -18px;
  margin-left: 60px;
}

.searchbox .rbox {
  padding-top: 4px;
  flex-shrink: 0;
}


.icon-gaojibianpai {
  font-size: 26px;
  font-weight: bold;
  color: #1948e7;
}


.topbox .totalbox {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  font-weight: 400;
  font-size: 16px;
  color: #999999;
  line-height: 22px;
  text-align: left;
  font-style: normal;
}

.topbox .checklistbox {
  margin-right: -10px;
}

.topbox .checklistbox .citem {
  display: flex;
  padding: 5px 0;
  align-items: center;
  justify-content: space-between;
  font-weight: 400;
  font-size: 14px;
  color: #333333;
  text-align: left;
  font-style: normal;
}

.topbox .checklistbox .citem .iconfont {
  cursor: pointer;
  position: relative;
  left: -10px;
}

.topbox .checklistbox .citem .iconfont:hover {
  color: var(--el-color-primary);
}

.topbox .checklistbox .citem .pname {
  color: var(--el-text-color-regular);
  font-size: 12px;
}


.tableboxContain {
  width: 100%;
  height: auto;
  box-sizing: border-box;
}



.pagelistbox {

  width: 100%;
  box-sizing: border-box;
  height: 100%;
}

.icon-shugui {
  color: var(--chakra-colors-primary-600);
  font-size: 20px;
}
</style>
