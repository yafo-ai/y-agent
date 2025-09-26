<script setup>
import { ref, nextTick, reactive } from "vue";
import {
  testplanreportpagination,
  testplanreportId,
  testplanreports,
  testcasepagination,
} from "@/api/api";

import { transferString, copyData } from "@/assets/utils/util";
import { useStore } from "vuex";
import { onBeforeRouteLeave, useRoute, useRouter } from "vue-router";

import { goback, getTime } from "@/components/comp.js";
import result from "@/views/flow/components/result.vue";
import icon from "@/components/icon.vue"
import addtestDialog from "@/views/test/components/addtestDialog.vue";
const route = useRoute();
const router = useRouter();
const store = useStore();

let searchParams = reactive({
  id: 0,
  page: 1,
  pagesize: 30,
  test_result: 0,
});
const total = ref(0);




copyData(searchParams, route.query);

let pagelist = ref([]);

const search = (type) => {
  if (type == "init") {
    searchParams.page = 1;
  }
  searchParams.id = curid.value;
  testplanreportpagination(searchParams).then((res) => {
    let arr = res.rows || [];
    pagelist.value = arr;
    total.value = res.total_records;
  });
  if (type != "noquery") {
    let query = { ...route.query, ...searchParams };
    router.replace({ path: route.path, query: query });
  }
};

// search('noquery');

const curid = ref('')
const historylist = ref([])

const detail = ref(null);

const getDetail = (item) => {
  if (item) {
    // 历史版本
    curid.value = item.report_id;
  }
  detail.value = null;
  pagelist.value = [];
  testplanreportId({ id: curid.value }).then((res) => {
    detail.value = res;
    search("noquery");
  });
};

if (route.path == '/testplan/detail') {
  // 测试计划
  testplanreports({ id: route.query.id }).then((res) => {
    historylist.value = res || [];
    getDetail(historylist.value[0]);
  });
} else {
  // 测试报告
  curid.value = route.query.id;
  getDetail()
}



const tableRef = ref(null);

const handleClick = () => {
  search('init')
}
const runresult = ref({});
const showTest = ref(false);
const openCompDetail = (id, type) => {
  if (!id) return false;
  runresult.value = { id: id }
  showTest.value = true;
}

const isShowAddDialog = ref(false);
const editparam = ref({});

const editfn = async (item) => {
  let id = item.test_case_id;
  testcasepagination({ id: id }).then((res) => {
    if (res.rows.length === 1) {
      editparam.value = res.rows[0];
      isShowAddDialog.value = true;
    }
  })

};

const subDialogfn = (res) => {
  _this.$message("操作成功");
  search();
  isShowAddDialog.value = false;
};

</script>

<template>
  <div class="pagelistbox c-page-testplain-detail">
    <template v-if="detail">
      <div class="c-titlebox">
        <span class="title">
          <span class="c-pointer" style="color: #909BA5;;margin-right: 5px;"
            @click="goback(null, router, route.query.fpath || (route.path == '/testplan/detail' ? '/testplan' : '/testreport'))">
            {{ route.path == '/testplan/detail' ? '测试计划' : '测试报告' }}
            <span class="iconfont icon-xiangyoujiantou"></span>
          </span>{{ detail.plan_name }}
        </span>
      </div>



    </template>
    <div class="c-tablebox c-bodybox tableboxContain c-tooltip">
      <div v-if="historylist.length > 0" class="mdbox">
        <div class="title">报告历史记录</div>
        <div class="historybox">
          <el-scrollbar>
            <div class="mg20">
              <div class="c-emptybox" v-if="historylist.length < 1">
                <icon type="empzwssjg" width="40" height="40"></icon>
                暂无历史记录
              </div>
              <div v-for="item in historylist" @click="getDetail(item)" :key="item.report_id"
                :class="{ on: item.report_id == curid }" class="item">
                <div :title="item.name" class="name ellipsis3">
                  {{ item.name }}
                </div>
                <div class="timebox">
                  <span class="time">{{ getTime(item.created_at) }}</span>
                </div>
              </div>
            </div>
          </el-scrollbar>
        </div>
      </div>

      <div class="bodybox" :class="{ on: historylist.length > 0 }">
        <div v-if="detail" class="tabbox">
          <el-tabs v-model="searchParams.test_result" class="demo-tabs" @tab-change="handleClick">
            <el-tab-pane :name="0">
              <template #label> 已运行用例
                <span class="c-primary-btn c-mini">{{ parseInt(detail.test_fail_count) +
                  parseInt(detail.test_pass_count) }}</span>
              </template>
            </el-tab-pane>
            <el-tab-pane :name="3001">
              <template #label> 未通过
                <span class="c-primary-btn c-mini">{{ detail.test_fail_count }}</span></template>
            </el-tab-pane>
            <el-tab-pane :name="2001">
              <template #label> 已通过<span class="c-primary-btn c-mini">{{ detail.test_pass_count }}</span> </template>
            </el-tab-pane>
          </el-tabs>
          <span style="position: absolute;top: 5px;right: 10px;z-index: 11;"
           @click="goback(null, router, route.query.fpath || (route.path == '/testplan/detail' ? '/testplan' : '/testreport'))" class="c-iconbackbox">
          <span class="iconfont icon-fuwenben-chexiao"></span> 返回
        </span>
        </div>
        <el-table ref="tableRef" :max-height="store.getters.innerHeight - 203" tooltip-effect="light" border
          :data="pagelist" style="width: 100%">
          <el-table-column prop="id" width="70" label="id" />

          <el-table-column label="问题">
            <template #default="scope">
              <el-popover v-if="scope.row.question" placement="top-start" :width="1000" trigger="hover">
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

          <el-table-column label="参考结果">
            <template #default="scope">
              <el-popover v-if="scope.row.right_answer" placement="top-start" :width="800" trigger="hover">
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


          <el-table-column label="测试结果">
            <template #default="scope">
              <el-popover v-if="scope.row.test_answer" placement="top-start" :width="600" trigger="hover">
                <template #reference>
                  <div class="ellipsis">
                    <span class="c-warn-btn c-mini">测</span>
                    {{ scope.row.test_answer }}
                  </div>
                </template>

                <div style="margin: 0 -20px;">
                  <el-scrollbar max-height="400">
                    <div v-html="scope.row.test_answer.replace(/\n/g, '<br>')" style="margin:0 20px;">
                    </div>
                  </el-scrollbar>
                </div>
              </el-popover>
            </template>
          </el-table-column>

          <el-table-column width="120" label="模型名称">
            <template #default="scope">
              {{ scope.row.execute_llm_name || scope.row.execute_workflow_name }}
            </template>
          </el-table-column>






          <el-table-column width="80" align="right" label="评分">
            <template #default="scope">
              {{ scope.row.score }}
            </template>
          </el-table-column>

          <el-table-column width="80" align="right" label="耗时">
            <template #default="scope">
              {{ scope.row.elapsed_time }}
            </template>
          </el-table-column>



          <el-table-column width="160" align="center" label="执行时间">
            <template #default="scope">
              {{
                getTime(scope.row.updated_at) || getTime(scope.row.created_at)
              }}
            </template>
          </el-table-column>

          <el-table-column width="160" align="right" label="操作">
            <template #default="scope">

              <!-- <div @click="editfn(scope.row)" class="c-table-ibtn">
                <span class="iconfont icon-xiugai"></span>
                修改
              </div> -->

              <div v-if="scope.row.workflow_log_id" @click="openCompDetail(scope.row.workflow_log_id, 1)"
                class="c-table-ibtn">
                <span class="iconfont icon-liebiao-ceshi"></span>
                测试详情
              </div>
              <div v-if="scope.row.testcase_workflow_log_id"
                @click="openCompDetail(scope.row.testcase_workflow_log_id, 2)" class="c-table-ibtn">
                <span class="iconfont icon-liebiao-xiangqing"></span>
                用例详情
              </div>

            </template>
          </el-table-column>
          <template #empty="scope">
            <div class="c-emptybox">
              <icon type="empzwssjg" width="100" height="100"></icon>暂无数据~~
            </div>
          </template>
        </el-table>

        <div v-if="total > 0" style="padding-right: 18px;" class="c-pagination">
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
  <result v-model="showTest" :data="runresult"></result>
  <addtestDialog v-model="isShowAddDialog" TEST_TYPE="S" :item="editparam" :title="editparam.id ? '修改单元测试' : '添加单元测试'"
    @subfn="subDialogfn"></addtestDialog>
</template>
<style scoped>
.c-page-testplain-detail .tabbox {
  margin-top: 8px;
  position: relative;
}

.c-page-testplain-detail .tabbox :deep(.el-tabs__nav-wrap) {
  padding-left: 16px;
}

.mdbox {
  flex-shrink: 0;
  height: 100%;
  width: 300px;
  box-sizing: border-box;
  border-right: 1px solid var(--el-border-color);
}

.mdbox .mg20 {
  margin: 0 16px;
}

.mdbox .title {
  font-size: 16px;
  font-weight: bold;
  text-align: left;
  padding: 24px 16px 16px 16px;
}

.mdbox .historybox {
  width: 100%;
  height: calc(100% - 60px);
  flex-shrink: 0;
  box-sizing: border-box;
}

.historybox .timebox {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  color: #999;
  margin-top: 8px;
}

.historybox .name {
  font-weight: bold;
  font-size: 12px;
  text-align: left;
}

.mdbox .historybox .item {
  display: block;
  padding: 16px;
  border: 1px solid var(--el-border-color);
  border-radius: 5px;
  cursor: pointer;
  margin-bottom: 10px;
  transition: all 0.3s;
  border-radius: 8px;
}

.mdbox .historybox .item.on,
.mdbox .historybox .item:hover {
  border-color: var(--el-color-primary);
  background: linear-gradient(180deg, #F0F3FF 0%, #FFFFFF 100%);
}

.mdbox .mdeditor {
  width: calc(100% - 200px);
  height: 100%;
}

.titlename {
  text-align: left;
  font-size: 16px;
  font-weight: bold;
  padding: 0px 0 10px 0;
  display: flex;
  align-items: center;

}

.titlename .icon-fanhui {
  font-size: 33px;
}


.flex {
  display: flex;
  align-items: center;
}


.icon-rizhi {
  font-size: 28px;
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
  height: calc(100% - 49px);
  padding: 0;
  box-sizing: border-box;
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
}

.tableboxContain .btnbox {
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
}

.tableboxContain .bodybox {
  display: block;
  width: 100%;
  height: auto;
}

.tableboxContain .bodybox.on {

  width: calc(100% - 300px);
}

.pagelistbox {
  width: 100%;
  box-sizing: border-box;
  height: 100%;
}
</style>
