<script setup>
import { ref, reactive } from "vue";
import { workflowlogs_pagination, testcate, testcaseadd, workflowall } from "@/api/api";
import { useStore } from "vuex";
import { onBeforeRouteLeave, useRoute, useRouter } from "vue-router";
import { getTime } from "@/components/comp.js";
import icon from "@/components/icon.vue"
import { cloneDeep, uniqBy } from "lodash"; // 引入lodash库的cloneDeep方法进行深拷贝

import { ClickOutside as vClickOutside } from "element-plus";
import result from "@/views/flow/components/result.vue";
import ininput from "@/components/ioinput.vue";
const route = useRoute();
const router = useRouter();
const store = useStore();
const curType = ref("");
const isShowTest = ref(false);
const times = ref([]);
const total = ref(0);


let searchParams = reactive({
  page: 1,
  pagesize: 30,
  flow_id: undefined,
  testname: "",
  origin: undefined,
  test_cate_id: undefined,
});

const reset = () => {
  curType.value = "";

  searchParams.flow_log_id = undefined;
  searchParams.flow_id = undefined;
  searchParams.flow_name = "";
  searchParams.source_name = "";
  searchParams.source_id = undefined;
  searchParams.user_id = "";
  searchParams.testname = "";
  searchParams.test_cate_id = undefined;
  searchParams.flow_name = "";
  searchParams.conversation_id = "";
  searchParams.question = "";
  searchParams.origin = undefined;
  searchParams.created_at_start = "";
  searchParams.created_at_end = "";

  times.value = [];
};
reset()


if (route.query.flow_log_id) {
  searchParams.flow_log_id = parseInt(route.query.flow_log_id);
}


if (route.query.created_at_start) {
  times.value = [route.query.created_at_start, route.query.created_at_end];
}

for (let key in route.query) {
  if (route.query[key]) {
    if (isNaN(route.query[key])) {
      searchParams[key] = route.query[key];
    } else {
      searchParams[key] = parseInt(route.query[key]);
    }
  }
}

let pagelist = ref([]);

const search = (type) => {
  if (type == "init") {
    searchParams.page = 1;
  }
  if (times.value && times.value.length) {
    searchParams.created_at_start = times.value[0];
    searchParams.created_at_end = times.value[1];
  } else {
    searchParams.created_at_start = "";
    searchParams.created_at_end = "";
  }
  let params = { ...searchParams };
  params.flow_log_id = params.flow_log_id || 0;
  workflowlogs_pagination(params).then((res) => {
    let arr = res.rows || [];
    arr.forEach((item) => {
      initCateList(item);
    });
    pagelist.value = arr;
    total.value = res.total_records;
  });
  if (type != "noquery") {
    let query = { ...route.query, ...searchParams };
    router.replace({ path: route.path, query: query });
  }
};

const resultChange = (item) => {
  let tindex = -1;
  pagelist.value.forEach((titem, index) => {
    if (titem.id == item.id) {
      tindex = index;
    }
  });
  if (tindex > -1) {
    initCateList(item);
    pagelist.value.splice(tindex, 1, item);
  }
};

const initCateList = (item) => {
  if (!item.test_cates) {
    item.test_cates = [];
  }
  if (!item.train_cates) {
    item.train_cates = [];
  }
  // 遍历子节点查询语料分类
  let arr1 = item.train_cates || [];
  let testarr = item.test_cates || [];
  if (item.node_log && item.node_log.length > 0) {
    item.node_log.forEach((citem) => {
      arr1 = arr1.concat(citem.cate);
      testarr = testarr.concat(citem.unit_cate);
    });
  }
  arr1 = uniqBy(arr1, "cate_id");
  testarr = uniqBy(testarr, "cate_id");
  arr1.forEach((titem) => {
    titem.xl = true;
  });
  testarr.forEach((titem) => {
    titem.tag = titem.tag || "S";
  });
  item.test_cates = testarr;
  item.train_cates = arr1;
};

search();

const runresult = ref({});
const showTest = ref(false);
const workflowrunfn = async (item) => {
  runresult.value = item;
  showTest.value = true;
};

const scrollbarRef = ref(null);

// 右键菜单
const menuVisible = ref(false);
const menuStyle = reactive({
  top: 0,
  left: 0,
});
const rkitem = ref(null);
const menuTop = ref(0);
const openContextMenu = (item, col, event) => {
  rkitem.value = item;
  addparam.id = rkitem.value.id;
  addparam.workflow_log_id = rkitem.value.id;
  addparam.answer = rkitem.value.output.join("\n");
  addparam.question = rkitem.value.user_input;
  addparam.message_history = [];
  visible.value = true;
  menuVisible.value = true;
  menuStyle.top = `${event.clientY}px`;
  menuStyle.left = `${event.clientX}px`;
  menuTop.value = event.clientY;
  // 防止默认右键菜单出现
  event.preventDefault();
};
const testTypelist = ref([
  {
    id: 0,
    name: "未分类",
    color: "#ff0000",
    pid: null,
    children: [],
    tag: "S",
  },
  {
    id: 0,
    name: "未分类",
    color: "#ff0000",
    pid: null,
    children: [],
    tag: "W",
  },
]);
const xlTypelist = ref([
  { id: 0, name: "未分类", color: "#ff0000", pid: null, children: [] },
]);

const getTypelist = () => {
  testcate()
    .then((res) => {
      testTypelist.value = [
        {
          id: 0,
          name: "未分类",
          color: "#ff0000",
          pid: null,
          children: [],
          tag: "S",
        },
        {
          id: 0,
          name: "未分类",
          color: "#ff0000",
          pid: null,
          children: [],
          tag: "W",
        },
      ].concat(res);
    })
    .catch((err) => { });
};
getTypelist();
const addparam = reactive({
  id: "",
  workflow_log_id: "",
  type: "",
  answer: "",
  question: "",
  message_history: "",
});
const curContextMenuType = ref(1);

const onClickOutside = (e) => {
  if (e.target.className != "custom-tree-node") {
    hideMenuList();
  }
};
const onClickOutside1 = (e) => {
  if (e.target.className != "custom-tree-node") {
    isShowTest.value = false;
  }
};

const visibletest = ref(false);
const visiblexl = ref(false);

const hideMenuList = () => {
  menuVisible.value = false;
  visibletest.value = false;
  visiblexl.value = false;
};

const findAndAddCategory = (categories, parentId, fn) => {
  categories.forEach((category) => {
    if (category.id == parentId) {
      fn && fn(category);
      return true;
    }

    if (category.children && category.children.length > 0) {
      findAndAddCategory(category.children, parentId, fn);
    }
  });
};
const initListCates = () => {
  pagelist.value.forEach((item) => {
    if (item.id == addparam.id) {
      if (curContextMenuType.value == 1) {
        console.log(testTypelist.value)
        findAndAddCategory(testTypelist.value.filter((titem) => titem.tag == 'W'), addparam.type, function (titem) {
          item.test_cates.push(titem);
        });
      } else if (curContextMenuType.value == 2) {
        // 添加到语料
        findAndAddCategory(xlTypelist.value, addparam.type, function (titem) {
          item.train_cates.push(titem);
        });
      }
    }
  });
};

const testcaseaddfn = (cate_id) => {
  if (cate_id === "" || cate_id === undefined || cate_id === null) {
    _this.$message("请选择分类", "error");
    return false;
  }
  testcaseadd({
    cate_id: cate_id,
    workflow_log_id: addparam.workflow_log_id,
    question: addparam.question,
    right_answer: addparam.answer,
  })
    .then((res) => {
      if (res) {
        _this.$message("添加成功");
        hideMenuList();
        initListCates();
      }
    })
    .catch((err) => { });
};

const visible = ref(false);

const getCateList = (item) => {
  return item.test_cates.concat(item.train_cates);
};

const nodeClickfn = (data) => {
  addparam.type = data.id;
  curContextMenuType.value = 1;
  testcaseaddfn(data.id, data);
};


const scrindex = ref(1);
const changescr = () => {
  searchheight.value === 0 ? searchheight.value = 67 : searchheight.value = 0;

}
const searchheight = ref(0);
const tableRef = ref(null);
const flowvisible = ref(false);
const flowvisible1 = ref(false);

const flow_nameref = ref(null);
const flow_nameref1 = ref(null);
const workflowalllist = ref([]);
const sourcealllist = ref([]);
const clonesoucelist = ref([]);

const checkflow = (item) => {
  flowvisible.value = false;
  searchParams.source_id = undefined;
  searchParams.source_name = '';
  sourcealllist.value = item.sources;
  clonesoucelist.value = cloneDeep(item.sources);
  searchParams.flow_id = item.flow_id;
  searchParams.flow_name = item.flow_name;
  flow_nameref.value && flow_nameref.value.blur()
}
const cloneAlllist = ref([])
workflowall().then((res) => {
  workflowalllist.value = res.rows;
  cloneAlllist.value = cloneDeep(res.rows);
})

const filterList = () => {
  // 流程输入筛选
  flowvisible.value = true;
  searchParams.flow_id = undefined;
  let arr = []
  cloneAlllist.value.forEach((item) => {
    if (item.flow_name.indexOf(searchParams.flow_name) > -1) {
      arr.push(item)
    }
  })
  if(!searchParams.flow_name){
    arr = cloneAlllist.value;
  }
  workflowalllist.value = arr;
}

const filterList1 = () => {
  // 流程输入筛选
  flowvisible1.value = true;
  searchParams.source_id = undefined;
  let arr = []
  clonesoucelist.value.forEach((item) => {
    if (item.source_name.indexOf(searchParams.source_name) > -1) {
      arr.push(item)
    }
  })
  sourcealllist.value = arr;
}

const checkSource = (item) => {
  flowvisible1.value = false;
  searchParams.source_id = item.source_id;
  searchParams.source_name = item.source_name;
  flow_nameref1.value && flow_nameref1.value.blur()
}


</script>

<template>
  <div v-initTableHeight style="height: 100%;">
    <div class="c-titlebox">
      <span class="title">流程日志</span>
    </div>

    <div class="c-top-searchbox c-js-item">
      <el-form :model="searchParams" ref="searchFormRef" inline class="demo-form-inline">
        <el-form-item label="id" prop="flow_log_id">
          <el-input clearable v-model="searchParams.flow_log_id" type="text"></el-input>
        </el-form-item>
        <el-form-item label="用户ID" prop="user_id">
          <el-input clearable v-model="searchParams.user_id" type="text"></el-input>
        </el-form-item>
        <el-form-item label="窗口id" prop="conversation_id">
          <el-input clearable v-model="searchParams.conversation_id" type="text"></el-input>
        </el-form-item>
        <el-form-item label="输入" prop="question">
          <el-input clearable v-model="searchParams.question" type="text"></el-input>
        </el-form-item>
        <el-form-item label="流程" prop="flow_name">
          <div class="s-origonbox">
            <div style="display: inline-flex;width: 200px;" v-click-outside="() => { flowvisible = false; }">
              <el-popover :visible="flowvisible" placement="bottom" :width="200">
                <template #reference>
                  <el-input @click.stop @focus="flowvisible = true;filterList()" ref="flow_nameref" @keyup="filterList"
                    placeholder="搜索流程" style="width: 200px;" v-model="searchParams.flow_name" type="text"></el-input>
                </template>
                <div class="flowlist">
                  <el-scrollbar :max-height="400">
                    <div style="margin: 0 16px;">
                      <div v-if="workflowalllist.length < 1" class="c-tips">暂无流程</div>
                      <div v-for="item in workflowalllist" @click.stop="checkflow(item)" class="item">
                        {{ item.flow_name }}
                      </div>
                    </div>
                  </el-scrollbar>
                </div>
              </el-popover>

            </div>
            <div style="display: inline-flex;width: 200px;" v-click-outside="() => { flowvisible1 = false; }">
              <el-popover :visible="flowvisible1" placement="bottom" :width="200">
                <template #reference>
                  <el-input placeholder="搜索来源" ref="flow_nameref1" style="width: 200px;" @click.stop
                    @focus="flowvisible1 = true;filterList1()" @blur="flowvisible1 = false;" @keyup="filterList1"
                    v-model="searchParams.source_name" type="text"></el-input>
                </template>
                <div class="flowlist">
                  <el-scrollbar :max-height="400">
                    <div style="margin: 0 16px;">
                      <div v-if="sourcealllist.length < 1" class="c-tips">暂无来源</div>
                      <div v-for="item in sourcealllist" @click.stop="checkSource(item)" class="item">
                        {{ item.source_name }}
                      </div>
                    </div>
                  </el-scrollbar>
                </div>
              </el-popover>
            </div>

          </div>
        </el-form-item>



        <el-form-item label="时间" prop="created_at_start">
          <el-date-picker style="width: 320px" clearable v-model="times" type="datetimerange"
            value-format="YYYY-MM-DD HH:mm:ss" range-separator=" - " start-placeholder="开始日期" end-placeholder="结束日期" />
        </el-form-item>

        <el-form-item label="测试" prop="test_cate_id">
          <div class="flex">
            <el-select @change="searchParams.test_cate_id = undefined" v-model="curType" placeholder="测试类型"
              style="display: inline-block; width: 120px">
              <el-option label="流程测试" value="W"></el-option>
              <el-option label="单元测试" value="S"></el-option>
            </el-select>

            <el-tree-select style="width: 240px" v-model="searchParams.test_cate_id" filterable check-strictly
              :props="{ children: 'children', label: 'name', value: 'id' }" node-key="id"
              :placeholder="curType ? '请选择' : '请先选择测试类型'" popper-class="c-treebox" :default-expand-all="true"
              :check-on-click-node="true" :data="testTypelist.filter((citem) => curType && citem.tag == curType)">
              <template #default="{ node, data }">
                <div :title="data.name" class="custom-tree-node">
                  <div class="item">
                    <span class="c-color radius" :style="'background-color:' + data.color"></span>{{ data.name }}
                  </div>
                </div>
              </template>
            </el-tree-select>
          </div>
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

    <div class="pagelistbox">
      <div class="c-tablebox tableboxContain c-tooltip">
        <!--  :max-height="store.getters.innerHeight - 246" -->
        <el-table ref="tableRef" @row-contextmenu="openContextMenu" tooltip-effect="light" border :data="pagelist"
          :max-height="store.getters.innerHeight - 198 - searchheight" style="width: 100%">
          <el-table-column width="100" prop="id" label="id">
            <template #default="scope">
              <el-popover v-if="
                (scope.row.train_cates && scope.row.train_cates.length > 0) ||
                (scope.row.test_cates && scope.row.test_cates.length > 0)
              " placement="top-end" :width="200" trigger="hover">
                <template #reference>
                  <div class="dotbox">
                    <span v-for="(item, index) in getCateList(scope.row)" class="dot" :class="{ on: item.xl }" :style="'background-color: ' +
                      item.color +
                      '; left: ' +
                      index * 5 +
                      'px'
                      "></span>
                  </div>
                </template>
                <div class="dotcontentbox c-scroll-contain">
                  <div v-if="
                    scope.row.test_cates && scope.row.test_cates.some((citem) => citem && citem.tag != 'S')
                  " class="title">
                    流程测试
                  </div>
                  <div v-if="scope.row.test_cates.length > 0" class="items">
                    <div v-for="item in scope.row.test_cates.filter(
                      (citem) => citem && citem.tag != 'S'
                    )" class="item ellipsis">
                      <span class="c-color radius" :style="'background-color:' + item.color"></span>
                      {{ item.name }}
                    </div>
                  </div>
                  <div v-if="
                    scope.row.test_cates.some((citem) => citem && citem.tag == 'S')
                  " class="title">
                    单元测试
                  </div>
                  <div v-if="scope.row.test_cates.length > 0" class="items">
                    <div v-for="item in scope.row.test_cates.filter(
                      (citem) => citem && citem.tag == 'S'
                    )" class="item ellipsis">
                      <span class="c-color radius" :style="'background-color:' + item.color"></span>
                      {{ item.name }}
                    </div>
                  </div>
                  <div v-if="scope.row.train_cates.length > 0" class="title">
                    语料类型
                  </div>
                  <div v-if="scope.row.train_cates.length > 0" class="items">
                    <div v-for="item in scope.row.train_cates" class="item ellipsis">
                      <span class="c-color" :style="'background-color:' + item.color"></span>
                      {{ item.name }}
                    </div>
                  </div>
                </div>
              </el-popover>
              <div style="display: inline-flex;align-items: center;">
                {{ scope.row.id }}
                
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="ai_run_id" width="160" label="用户id" />
          <el-table-column prop="conversation_id" width="160" label="窗口id" />

          <el-table-column label="输入">

            <template #default="scope">
              <ininput :input="scope.row.user_input" :output="scope.row.output.join('\n')"
                :messages="scope.row.human_messages"></ininput>
            </template>
          </el-table-column>

          <el-table-column width="180" label="输出">
            <template #default="scope">
              <div style="display: flex;">
              <el-tooltip v-if="scope.row.error_msg" effect="light" placement="right"
                  :content="'<div style=' + 'display:block;max-width:600px;' + ' class=' + 'c-danger' + '>' + scope.row.error_msg + '</div>'"
                  raw-content>
                  <span class="c-danger iconfont icon-gantanhao1"></span>
                </el-tooltip>
              <ininput v-if="scope.row.human_messages && scope.row.human_messages.length>0" :isShowOutput="true" :input="scope.row.user_input" :output="scope.row.output.join('\n')"
                :messages="scope.row.human_messages"></ininput>
              </div>
            </template>
          </el-table-column>





          <el-table-column width="180" prop="flow_name" label="流程">
            <template #default="scope">
              <div style="color: #409eff;">{{ scope.row.source_name }}</div>
              {{ scope.row.flow_name }}
            </template>
          </el-table-column>
          <el-table-column width="180" show-overflow-tooltip prop="use_tools" label="工具" />

          <el-table-column width="100" align="right" sortable prop="created_at" label="耗时/s">
            <template #default="scope">
              {{ scope.row.elapsed_time }}
            </template>
          </el-table-column>

          <el-table-column width="80" align="right" label="评分">
            <template #default="scope">
              {{ scope.row.score || "" }}
            </template>
          </el-table-column>

          <el-table-column width="160" align="center" label="时间">
            <template #default="scope">
              {{
                getTime(scope.row.updated_at) || getTime(scope.row.created_at)
              }}
            </template>
          </el-table-column>

          <el-table-column width="120" align="center" label="操作">
            <template #default="scope">

              <div @click="workflowrunfn(scope.row)" class="c-table-ibtn">
                <span class="iconfont icon-liebiao-xiangqing"></span>
                详情
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
                tableRef && tableRef.scrollTo(0, 0)
                search();
              }
            " :page-sizes="[30, 50, 100, 900]" layout="total,sizes,jumper,prev, pager, next" :total="total" />
        </div>
      </div>
    </div>

  </div>
  <result v-model="showTest" @change="resultChange" :data="runresult"></result>

  <div v-show="menuVisible" v-click-outside="onClickOutside" class="context-menu c-scroll-contain" :style="menuStyle">
    <div :class="{ on: menuTop > 600 }" class="contmenubox">
      <div @mouseenter="
        visiblexl = false;
      visibletest = true;
      " class="citem">
        添加到流程测试
        <div v-show="visibletest" class="treebox">
          <el-tree ref="ctreeSelecttest" :data="testTypelist.filter((citem) => citem.tag != 'S')" node-key="id"
            empty-text=" " highlight-current :current-node-key="parseInt(addparam.type)" default-expand-all
            @node-click="nodeClickfn" :expand-on-click-node="false">
            <template #default="{ node, data }">
              <div :title="data.name" class="custom-tree-node">
                <div :title="data.name" class="item ellipsis">
                  <span class="c-color radius" :style="'background-color:' + data.color"></span>{{ data.name }}
                </div>
              </div>
            </template>
          </el-tree>
        </div>
      </div>
    </div>
  </div>
</template>
<style scoped>
.flowlist {
  margin: 0 -16px;
}

.flowlist .item {
  cursor: pointer;
  padding: 10px;
}

.flowlist .item:hover {
  background: #f1f1f1;
}

.s-origonbox {}

.treebox .ellipsis {
  max-width: 220px;
}

.human_messagesitem {
  display: inline-block;
}

.human_messagesitem .name {
  font-weight: bold;
}

.human_messagesitem .text {
  padding-bottom: 10px;
}

.testidbox {
  position: relative;
}

.testidbox .treebox {
  position: absolute;
  left: 0;
  top: 40px;
  max-width: 400px;
  z-index: 10;
  max-height: 400px;
  overflow: auto;
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

.context-menu {
  position: fixed;
  background-color: #fff;
  border: 1px solid #f1f1f1;
  border-radius: 5px;
  z-index: 1000;
  transform: translate(0, -40px);
}

.context-menu .contmenubox {
  margin: 0;
  padding: 0;
  list-style: none;
}

.context-menu .citem {
  padding: 10px 20px;
  cursor: pointer;
  font-size: 14px;
  text-align: left;
  position: relative;
}

.context-menu .citem .treebox {
  position: absolute;
  width: 300px;
  min-height: 82px;
  max-height: 400px;
  overflow-y: auto;
  box-sizing: border-box;
  border: 1px solid #f1f1f1;
  left: 145px;
  top: 0;
  z-index: 10;
  background: #fff;
}

.context-menu .contmenubox.on .citem .treebox {
  top: inherit;
  bottom: 0;
}

.context-menu .citem:hover {
  background: #f5f7fa;
}

.searchbox {
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  padding: 0px;
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



.icon-shugui {
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

.tableboxContain {
  width: 100%;
  height: 100%;
}

.pagelistbox {
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  flex-wrap: wrap;
  padding: 0px;
  width: 100%;
  box-sizing: border-box;
  height: calc(100% - 54px);
}

.pagelistbox .item {
  width: 400px;
  height: 150px;
  background: #fff;
  border-radius: 10px;
  box-sizing: border-box;
  margin: 10px;
  cursor: pointer;
  border: 1px solid #eee;
  padding: 10px 10px 40px 20px;
  position: relative;
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

.name {
  word-break: break-all;
}
</style>
