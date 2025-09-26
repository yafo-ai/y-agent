<script setup>
import { ref, nextTick, shallowRef, onActivated, reactive } from "vue";
import {
  testplanreport,
  testplanreportdelete,
} from "@/api/api";

import { transferString,copyData } from "@/assets/utils/util";
import { useStore } from "vuex";
import { onBeforeRouteLeave, useRoute, useRouter } from "vue-router";
import { goback, getTime } from "@/components/comp.js";
import icon from "@/components/icon.vue"
const route = useRoute();
const router = useRouter();
const store = useStore();

let searchParams = reactive({
  page: 1,
  pagesize: 30,
  plan_id: 0,
});
const total = ref(0);




copyData(searchParams, route.query);

let pagelist = ref([]);

const search = (type) => {
  if (type == "init") {
    searchParams.page = 1;
  }
  testplanreport(searchParams).then((res) => {
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






const tableRef = ref(null);





const delfn = (item) => {
  _this.$confirm("确定要删除所选数据?").then((res) => {
    testplanreportdelete({id:item.id}).then((res)=>{
      _this.$message("删除成功");
      search();
    })
  });
};

const openCompDetail = (item) => {
  router.push({ path: '/testreport/detail', query: { id: item.id,fpath:route.fullPath } });
  
};
</script>

<template>
  <div class="pagelistbox">
    <div class="c-titlebox">
      <span class="title">测试报告</span>
    </div>
    <div class="c-tablebox tableboxContain c-tooltip">
      
      <div class="bodybox">
          <el-table
            tooltip-effect="light"
            ref="tableRef"
            border
            :data="pagelist"
             :max-height="store.getters.innerHeight - 138"
            style="width: 100%"
          >
            <el-table-column prop="id" width="70" label="id" />

            <el-table-column label="报告名称">
              <template #default="scope">
                 <div class="c-scroll-contain">
                {{ scope.row.name }}
                 </div>
              </template>
            </el-table-column>

            <el-table-column label="计划名称">
              <template #default="scope">
                <div class="c-scroll-contain">
                {{ scope.row.plan_name }}
                </div>
              </template>
            </el-table-column>
            <el-table-column align="right" label="通过数 / 失败数 / 执行用例数">
              <template #default="scope">
                 <div class="c-scroll-contain">
                {{ scope.row.test_pass_count }} /
                {{ scope.row.test_fail_count }} /
                {{ scope.row.execute_count }}
                 </div>
              </template>
            </el-table-column>

            <el-table-column align="right" width="90" label="通过率">
              <template #default="scope">
                 <div class="c-scroll-contain">
                
                {{scope.row.execute_count? ((scope.row.test_pass_count / scope.row.execute_count)*100).toFixed(2) + '%' : '' }}

                 </div>
              </template>
            </el-table-column>

        

          
       

            <el-table-column width="160" align="center" label="用例时间">
              <template #default="scope">
                {{
                  getTime(scope.row.updated_at) || getTime(scope.row.create_at)
                }}
              </template>
            </el-table-column>

            <el-table-column width="200" align="center" label="操作">
              <template #default="scope">
               
                <div @click="openCompDetail(scope.row)" class="c-table-ibtn">
                  <span class="iconfont icon-liebiao-baogao"></span>
                  查看报告
                </div>
                <div @click="delfn(scope.row)" class="c-table-ibtn c-btn-del">
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
            <el-pagination
              :hide-on-single-page="false"
              background
              :page-size="searchParams.pagesize"
              :current-page="searchParams.page"
              @size-change="
                (val) => {
                  searchParams.pagesize = val;
                  searchParams.page = Math.min(
                    Math.ceil(total / searchParams.pagesize),
                    searchParams.page
                  );

                  search();
                }
              "
              @current-change="
                (val) => {
                  searchParams.page = val;
                  tableRef && tableRef.scrollTo(0,0);
                  search();
                }
              "
              :page-sizes="[30, 50, 100, 900]"
              layout="total,sizes,jumper,prev, pager, next"
              :total="total"
            />
          </div>
      </div>
    </div>
  </div>
</template>
<style scoped>

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
.listbox {
  display: block;
  text-align: center;
}

.listbox .icon-canshu {
  font-size: 20px;
}
.tableboxContain {
  width: 100%;
  height: calc(100% - 0px);
  box-sizing: border-box;
}
.tableboxContain .btnbox {
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
}
.tableboxContain .bodybox {
  height: auto;
}
.pagelistbox {

  width: 100%;
  box-sizing: border-box;
  height: 100%;
}

</style>
