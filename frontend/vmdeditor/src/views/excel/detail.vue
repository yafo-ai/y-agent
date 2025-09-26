<script setup>
import { ref, nextTick, onMounted, onUnmounted, reactive, watch } from "vue";
import { databaseDetailContents } from "@/api/api";
import { Search, UploadFilled } from "@element-plus/icons-vue";
import { goback, getTime } from "@/components/comp.js";
import { copyData } from "@/assets/utils/util";
import { onBeforeRouteLeave, useRoute, useRouter } from "vue-router";
import { useStore } from "vuex";
import icon from "@/components/icon.vue"
const route = useRoute();
const router = useRouter();
const store = useStore();

const total = ref(0);
const pagelist = ref([]);
const searchParams = reactive({
  page: 1,
  pagesize: 30,
  id: route.query.id,
  relation_index: undefined,
  code: "",
  title: "",
});
const reset = () => {
  searchParams.relation_index = undefined;
  searchParams.code = "";
  searchParams.title = "";
};
if (route.query.page) {
  searchParams.page = parseInt(route.query.page) || 1;
  searchParams.pagesize = parseInt(route.query.pagesize) || 30;
}
copyData(searchParams, route.query);
const search = (type) => {
  if (!searchParams.relation_index) {
    searchParams.relation_index = undefined;
  }
  databaseDetailContents(searchParams).then((res) => {
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
</script>
<template>
  <div class="page-wbsj">
    <div class="c-titlebox">
      <span @click="goback(null, $router, route.query.fpath || '/dataset/excel')" class="title">
        <span class="c-pointer c-flex-center" style="font-size: 14px;">
          <span class="iconfont icon-fuwenben-chexiao"></span>返回列表</span>
      </span>
    </div>

    <div class="c-top-searchbox">
      <el-form :model="searchParams" ref="searchFormRef" inline class="demo-form-inline">
        <el-form-item label="索引" prop="relation_index">
          <el-input clearable v-model="searchParams.relation_index" type="text"></el-input>
        </el-form-item>
        <el-form-item label="编码" prop="code">
          <el-input clearable v-model="searchParams.code" type="text"></el-input>
        </el-form-item>
        <el-form-item label="名称" prop="title">
          <el-input clearable v-model="searchParams.title" type="text"></el-input>
        </el-form-item>
      </el-form>

      <div class="rbox">
        <!--v-if-->
        <el-button @click="search('init')" type="primary">查询</el-button>
        <el-button @click="reset()" plain>重置</el-button>
      </div>
    </div>
    <div class="containbox c-tablebox">
        <el-table ref="tableRef" :data="pagelist" :max-height="store.getters.innerHeight - 198" style="width: 100%">
          <el-table-column width="200" label="索引">
            <template #default="scope">
              {{ scope.row.relation_index }}
            </template>
          </el-table-column>
          <el-table-column width="200" label="编码">
            <template #default="scope">
              {{ scope.row.code }}
            </template>
          </el-table-column>

          <el-table-column label="名称">
            <template #default="scope">
              {{ scope.row.title }}
            </template>
          </el-table-column>
          <el-table-column width="200" label="日期">
            <template #default="scope">
              {{ getTime(scope.row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column width="200" label="更新时间">
            <template #default="scope">
              {{ getTime(scope.row.updated_at) }}
            </template>
          </el-table-column>

          <el-table-column width="100" align="center" label="操作">
            <template #default="scope">


              <div @click="
                $router.push(
                  '/chat/detail?rid=' +
                  route.query.id +
                  '&type=excel_document&did=' +
                  scope.row.code
                )
                " class="c-table-ibtn">
                <span class="iconfont icon-liebiao-chakan"></span>
                查看
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
                tableRef && tableRef.scrollTo(0,0);
                search();
              }
            " :page-sizes="[30, 50, 100, 900]" layout="total,sizes,jumper,prev, pager, next" :total="total" />
        </div>
    </div>
  </div>
</template>
<style scoped>
.topbox {
  display: flex;
}

.searchbox {
  display: flex;
  align-items: center;
}

.containbox {
  height: auto;
  box-sizing: border-box;
}

.backbox .title {
  font-weight: bold;
  font-size: 16px;
}

.page-wbsj {
  display: block;
  width: 100%;
  height: 100%;
}

.backbox {
  font-size: 16px;
}

.icon-fanhui {
  font-size: 26px;
  margin-right: 5px;
}
</style>