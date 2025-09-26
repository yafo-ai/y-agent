<script setup>
import { ref, nextTick, onMounted, reactive, watch } from "vue";
import { useStore } from "vuex";
import { useRoute, useRouter } from "vue-router";

import icon from "@/components/icon.vue"
import {
  testplanreportpagination,
  testplanreportId,
  testplanreports,
} from "@/api/api";
import { getTime } from "@/components/comp.js";
const props = defineProps({
  id: {
    type: [String, Number],
    default: () => 0,
  },
  type: {
    type: [String, Number],
    default: () => 0,
  },

  modelValue: { type: Boolean, default: false },
});
const emits = defineEmits(["subfn", "update:modelValue", "close"]);
const route = useRoute();
const router = useRouter();
const store = useStore();

const dialogFormVisible = ref(false);

watch(
  () => props.modelValue,
  (n) => {
    dialogFormVisible.value = n;
    if (props.modelValue) {
      if (props.type == 0) {
        historylist.value = [];
        curid.value = props.id;
        getDetail();
      } else {
        testplanreports({ id: props.id }).then((res) => {
          historylist.value = res || [];
          curid.value = historylist.value[0].report_id;
          getDetail();
        });
      }
    }
  
  }
);
const curid = ref("");
watch(
  () => props.id,
  (n) => {
    
  }
);

const close = () => {
  emits("update:modelValue", false);
  emits("close", false);
};

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
    search("init", 3001);
  });
};

const searchParams = reactive({
  id: 0,
  page: 1,
  pagesize: 30,
  test_result: 0,
});

const pagelist = ref([]);
const total = ref(0);
const search = (type, test_result) => {
  if (type == "init") {
    searchParams.page = 1;
  }
  searchParams.id = curid.value;
  searchParams.test_result = test_result || searchParams.test_result;
  testplanreportpagination(searchParams).then((res) => {
    let arr = res.rows || [];
    pagelist.value = arr;
    total.value = res.total_records;
  });
};


const scrollbarlog = ref(null);
const jsonObj = ref({});
const showJson = ref(false);
const showLog = (item) => {
  if (!item.log_content) return false;
  jsonObj.value = JSON.parse(item.log_content);
  showJson.value = true;

};
const scrollbarRef = ref(null);


const historylist = ref([]);
</script>
<template>
  <el-dialog
    align-center
    destroy-on-close
    v-model="dialogFormVisible"
    title="测试报告"
    @closed="close"
    width="1000"
  >
    <div class="testdetail" :class="{ full: historylist.length < 1 }">
      <div v-if="historylist.length > 0" class="mdbox">
        <div class="historybox">
          <div class="title">报告历史记录</div>
          <el-scrollbar>
            <div class="c-emptybox" v-if="historylist.length < 1">
              <icon type="empzwssjg" width="40" height="40"></icon>
              暂无历史记录</div>
            <div
              v-for="item in historylist"
              @click="getDetail(item)"
              :key="item.report_id"
              :class="{ on: item.report_id == curid }"
              class="item"
            >
              <div :title="item.name" class="name ellipsis3">
                {{ item.name }}
              </div>
              <div class="timebox">
                <span class="time">{{ getTime(item.created_at) }}</span>
              </div>
            </div>
          </el-scrollbar>
        </div>
      </div>

      <div class="pagebox">
        <el-scrollbar ref="scrollbarRef">
          <template v-if="detail">
            <div class="name">{{ detail.plan_name }}</div>
            <div class="countbox">
              用例总数：{{ detail.case_count }}
              <div style="float: right" class="time">
                {{ getTime(detail.create_at) }}
              </div>
            </div>

            <div class="navbtn">
              <el-button
                @click="search('init', 3001)"
                size="small"
                :type="searchParams.test_result == 3001 ? 'primary' : ''"
                plain
                >未通过用例({{ detail.test_fail_count }})</el-button
              >
              <el-button
                @click="search('init', 2001)"
                size="small"
                :type="searchParams.test_result == 2001 ? 'primary' : ''"
                plain
                >已通过用例({{ detail.test_pass_count }})</el-button
              >
            </div>

            <div class="pagelist">
              <div v-if="pagelist.length < 1" class="c-empty">暂无数据</div>
              <div v-for="item in pagelist" class="item">
                <div class="qus qusbox">
                  <span class="qusitem">用户问题：{{ item.question }}</span>
                  <el-button
                    type="primary"
                    size="small"
                    @click="showLog({ log_content: item.citations })"
                    >查看上下文</el-button
                  >
                </div>
                <div class="qus">AI回答：{{ item.test_answer }}</div>
                <div class="qus">参考答案：{{ item.right_answer }}</div>
                <div class="btnbox">
                  <div>
                    <span class="time"
                      >评测大模型：{{
                        item.evaluation_llm_name
                      }}
                      &nbsp;&nbsp;</span
                    >
                    <span class="time"
                      >评测提示词：{{ item.evaluation_prompt_name }}
                    </span>
                  </div>
                </div>
                <div class="btnbox">
                  <div>
                    <span class="c-primary">评分：{{ item.score }} </span>
                    <span class="time"> 耗时：{{ item.elapsed_time }}s </span>
                  </div>
                  <div>
                    <span class="time">{{ getTime(item.created_at) }} </span>
                  </div>
                </div>
              </div>
            </div>

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

                    search();
                  }
                "
                :page-sizes="[30, 50, 100, 900]"
                layout="total,sizes,jumper,prev, pager, next"
                :total="total"
              />
            </div>
          </template>
        </el-scrollbar>
      </div>
    </div>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="close()" type="primary">关闭</el-button>
      </div>
    </template>
  </el-dialog>

  <el-dialog align-center v-model="showJson" title="查看上下文" width="1000">
    <div class="log_content">
      <el-scrollbar ref="scrollbarlog">
        <json-viewer
          :show-array-index="true"
          sort
          :expand-depth="5"
          :copyable="{ copyText: '复制代码', copiedText: '复制成功' }"
          :value="jsonObj"
        ></json-viewer>
      </el-scrollbar>
    </div>
    <template #footer>
      <div class="dialog-footer">
        <el-button type="primary" @click="showJson = false"> 关闭 </el-button>
      </div>
    </template>
  </el-dialog>
</template>
<style scoped>
.qusbox {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}
.qusbox .qusitem {
  width: calc(100% - 100px);
}
.mdbox {
  height: 700px;
  text-align: left;
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  width: 220px;
  position: relative;
}
.pagebox {
  height: 700px;
  width: calc(100% - 220px);
}
.testdetail.full .pagebox {
  width: 100%;
}
.historybox .title {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 10px;
}
.mdbox .historybox {
  width: 200px;
  height: 100%;
  flex-shrink: 0;
  box-sizing: border-box;
  padding-right: 10px;
}
.historybox .timebox {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  color: #aaa;
}
.historybox .name {
  font-weight: bold;
  font-size: 12px;
}
.mdbox .historybox .item {
  display: block;
  padding: 10px;
  border: 1px solid var(--el-border-color);
  border-radius: 5px;
  cursor: pointer;
  margin-bottom: 10px;
  transition: all 0.3s;
}
.mdbox .historybox .item.on,
.mdbox .historybox .item:hover {
  border-color: var(--el-color-primary);
}
.mdbox .mdeditor {
  width: calc(100% - 200px);
  height: 100%;
}
.mdcontain {
  height: calc(100% - 40px);
}
.pagelist .item {
  border: 1px solid #ddd;
  border-radius: 5px;
  margin: 10px auto;
  padding: 20px;
}
.pagelist .item .btnbox {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.pagelist .item .qus {
  text-align: left;
  word-break: break-all;
  margin-bottom: 10px;
}
.navbtn {
  margin-top: 10px;
}
.countbox {
  line-height: 22px;
}
.time {
  color: #999;
}
.log_content {
  width: 100%;
  height: 700px;
  text-align: left;
}
.testdetail {
  width: 100%;
  text-align: left;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}
.name {
  font-weight: bold;
  font-size: 16px;
  margin-bottom: 10px;
}
</style>