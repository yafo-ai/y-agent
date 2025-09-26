<script setup>
import { ref, nextTick, shallowRef, onActivated, reactive,watch } from "vue";
import {
  testcaseresult,
} from "@/api/api";

import { transferString, copyData } from "@/assets/utils/util";
import { useStore } from "vuex";
import { onBeforeRouteLeave, useRoute, useRouter } from "vue-router";

import { goback, getTime } from "@/components/comp.js";
import result from "@/views/flow/components/result.vue";
import icon from "@/components/icon.vue"
const route = useRoute();
const router = useRouter();
const store = useStore();
const props = defineProps({
  id: {
    type: [String, Number],
    default: () => 0,
  },
});
let searchParams = reactive({
  id: props.id || 0,
});
const total = ref(0);

watch(
  () => props.id,
  async (n, old) => {
    console.log(n)
    if (n !== old && n) {
      search("init");
    }
  }
);


let pagelist = ref([]);

const search = (type) => {
  if (type == "init") {
    searchParams.page = 1;
  }
  testcaseresult({ id: props.id }).then((res) => {
    pagelist.value = res || [];
  });
  
};

search('noquery');






const scrollbarRef = ref(null);
const runresult = ref({});
const showTest = ref(false);
const openCompDetail = (id, type) => {
  if (!id) return false;
  runresult.value = { id: id }
  showTest.value = true;
}

</script>

<template>
  <div class="pagelistbox">
    <!-- <div class="c-titlebox">
      <span class="title">
        <span class="c-pointer" style="color: #909BA5;;margin-right: 5px;"
          @click="goback(null, router, route.query.fpath || '/test')">
          {{ route.query.fpath.indexOf('/test?') !== -1 ? '流程测试' : '单元测试' }}
          <span class="iconfont icon-xiangyoujiantou"></span>
        </span>运行记录
      </span>
    </div> -->

    <div class="c-tablebox tableboxContain c-tooltip">


      <div class="bodybox">
        <el-scrollbar ref="scrollbarRef">
          <el-table tooltip-effect="light" border :data="pagelist" style="width: 100%">
            <el-table-column prop="id" width="70" label="id" />



            <el-table-column label="参考答案">
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
            <el-table-column label="最终回答">
              <template #default="scope">
                <el-popover v-if="scope.row.test_answer" placement="top-start" :width="500" trigger="hover">
                  <template #reference>
                    <div class="ellipsis2">
                      <span class="c-warn-btn c-mini">终</span>
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
            <el-table-column width="160" align="center" show-overflow-tooltip label="结果">
              <template #default="scope">
                <span :class="{
                  'c-success-btn': scope.row.test_result_name == '成功',
                  'c-danger-btn': scope.row.test_result_name != '成功',
                }">{{ scope.row.test_result_name }}</span>
              </template>
            </el-table-column>

            <el-table-column width="260" v-if="route.query.tag == 'S'" label="模型名称">
              <template #default="scope">
                {{ scope.row.execute_llm_name }}
              </template>
            </el-table-column>

            <el-table-column width="180" align="right" v-if="route.query.tag != 'S'" label="流程名称">
              <template #default="scope">
                {{ scope.row.execute_workflow_name }}
              </template>
            </el-table-column>


            <el-table-column width="80" align="right" label="评分">
              <template #default="scope">
                {{ scope.row.score }}
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


                <div v-if="scope.row.test_workflow_log_id" @click="openCompDetail(scope.row.test_workflow_log_id, 1)"
                  class="c-table-ibtn">
                  <span class="iconfont icon-liebiao-ceshi"></span>
                  测试详情
                </div>
                <div v-if="scope.row.workflow_log_id" @click="openCompDetail(scope.row.workflow_log_id, 2)"
                  class="c-table-ibtn">
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

                  search();
                }
              " :page-sizes="[30, 50, 100, 900]" layout="total,sizes,jumper,prev, pager, next" :total="total" />
          </div>
        </el-scrollbar>
      </div>
    </div>
  </div>
  <result v-model="showTest" :data="runresult"></result>
</template>
<style scoped>
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


.icon-jietouzhongpai {
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
  height: calc(100% - 20px);
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
  height: 100%;
}

.tableboxContain .bodybox.on {

  width: calc(100% - 300px);
}

.pagelistbox {
  width: 100%;
  height: 100%;
  box-sizing: border-box;
}
</style>
