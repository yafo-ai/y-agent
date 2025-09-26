<script setup>
import { ref, nextTick, onMounted, reactive, watch } from "vue";
import { useStore } from "vuex";
import { useRoute, useRouter } from "vue-router";
import { testcaseadd, testcate, model_configall, try_answer } from "@/api/api";
import { scrollToTop } from "@/assets/utils/util";
import { cloneDeep } from "lodash"; // 引入lodash库的cloneDeep方法进行深拷贝
const props = defineProps({
  id: {
    type: [String, Number],
    default: () => 0,
  },

  TEST_TYPE: {
    type: [String, Number],
    default: "W",
  },
  title: {
    type: [String, Number],
    default: () => '',
  },
  item: {
    type: Object,
    default: () => { return {} },
  },
  curResult: {
    type: Object,
    default: () => { return {} },
  },
  modelValue: { type: Boolean, default: false },
});
const emits = defineEmits(["subfn", "update:modelValue"]);
const route = useRoute();
const router = useRouter();
const store = useStore();

console.log(props, "props");


// S单元测试 W流程测试

const llmlist = ref([]);
//  获取大模型配置

const getllmlist = (flag) => {
  if (llmlist.value.length > 0) return;
  model_configall({ page: 1, pagesize: 10000 }, props.TEST_TYPE).then((res) => {
    llmlist.value = res || [];
  });
};
const dialogFormVisible = ref(false);
const editparam = reactive({
  id: 0,
  cate_id: 0,
  llm_id: undefined,
  workflow_log_id: "",
  message_history_id: 0,
  question: "",
  message_history: "",
  right_answer: "",
  note: "",
  test_standard: undefined,
  is_marked: false,
  is_modified: false,
});

const curtitle = ref('测试用例')
watch(
  () => props.TEST_TYPE,
  async (n, old) => {
    if (n !== old && n) {
      searchCate(true);
    }
    dialogFormVisible.value = n;
  }
);

watch(
  () => props.modelValue,
  async (n, old) => {
    if (n !== old && n) {
      if (formRef1.value) {
        formRef1.value.clearValidate();
      }

      if (!props.title) {
        curtitle.value = props.TEST_TYPE == "W" ? "流程测试用例" : '单元测试用例'
      } else {
        curtitle.value = props.title
      }
      searchCate();
      getllmlist();

      initEditparam(props.item);

      setLocalllm();
    }
    dialogFormVisible.value = n;
  }
);

const initEditparam = (item) => {
  checkids.value = []
  editparam.id = item.id || 0;
  editparam.workflow_node_log_id = item.workflow_node_log_id || undefined;
  editparam.cate_id = item.test_cate_id || 0;
  editparam.message_history_id = item.message_history_id || 0;
  editparam.message_history = item.message_history || "";
  editparam.workflow_log_id = item.workflow_log_id || 0;
  editparam.question = item.question || "";
  editparam.right_answer = item.right_answer || "";
  editparam.note = item.note || "";
  editparam.is_marked = item.is_marked || false;
  editparam.is_modified = item.is_modified || false;
  editparam.test_standard = item.test_standard || undefined;
};

const close = () => {
  emits("update:modelValue", false);
};

const get_cateslist = (item) => {
  return [
    { id: 0, name: "未分类", color: "#ff0000", pid: null, children: [] },
  ].concat(dataSource.value);
};

const dataSource = ref([]);

const searchCate = (flag) => {
  if (dataSource.value.length > 0 && !flag) return;
  testcate({}, props.TEST_TYPE).then(async (res) => {
    dataSource.value = res || [];
  });
};

// 递归查找添加类型
const findAndAddCategory = (categories, parentId, fn) => {
  categories.forEach((category) => {
    if (category.id === parentId) {
      fn && fn(category);
      return true;
    }

    if (category.children && category.children.length > 0) {
      findAndAddCategory(category.children, parentId, fn);
    }
  });
};

const formRef1 = ref();
const subeditfn = async (formEl) => {
  if (!formEl) return;
  await formEl.validate((valid, fields) => {
    if (valid) {
      // 添加到语料
      // editparam.llm_id = undefined;
      testcaseadd(editparam, props.TEST_TYPE).then((res) => {
        if (res) {
          let curitem = null;
          findAndAddCategory(
            get_cateslist(),
            editparam.cate_id,
            function (titem) {
              curitem = titem;
            }
          );
          emits("subfn", { res, item: curitem });
        }
      });
    }
  });
};

const checkids = ref([]);
const try_answerfn = () => {
  // 本地缓存大模型
  setLocalllm(editparam.llm_id);
  let ids = [];
  checkids.value = [];
  if (Array.isArray(editparam.llm_id)) {
    // 是数组
    ids = editparam.llm_id;
  } else {
    ids = [editparam.llm_id];
  }
  ids.forEach((id) => {
    llmlist.value.forEach(async (item) => {
      if (item.id == id) {
        checkids.value.push(cloneDeep(item));
      }
    });
  });

  getAns();
};

const starttimer = ref(0)
const getAns = async () => {
  starttimer.value = Date.now();
  const promises = checkids.value.map((item, index) => {
    checkids.value[index].loading = true;
    return try_answer({
      llm_id: item.id,
      input: editparam.question,
      vision_file_str:props.curResult.vision_file_str
    }).then((res) => {
      checkids.value[index].right_answer = res.answer || "";
      checkids.value[index].loading = false;
      checkids.value[index].time = Date.now();
    }).catch((err) => {
      console.error('Error in try_answer:', err);
      checkids.value[index].loading = false;
      checkids.value[index].time = Date.now();
    });
  });

  await Promise.all(promises);
};

const setLocalllm = (val) => {
  let localKey = props.TEST_TYPE + "local_llm";
  if (val) {
    window.localStorage.setItem(localKey, val.join(","));
  } else {
    // 如果不是  设置本地模型
    let llmid = window.localStorage.getItem(localKey);
    if (llmid) {
      let ids = [];
      llmid.split(",").forEach((clid) => {
        ids.push(parseInt(clid));
      });
      editparam.llm_id = ids;
    }
  }
};

</script>
<template>
  <el-drawer v-model="dialogFormVisible" :title="curtitle" @closed="close" direction="rtl" :close-on-click-modal="true"
    size="90%">
    <div class="isShowAddDialogBox c-scroll-contain c-addtestdialog dformbox">
      <el-form ref="formRef1" :model="editparam" label-position="top" label-width="auto" inline class="demo-dynamic">
        <div class="formbox">
          <div class="flbox">
            <el-scrollbar>
              <div style="margin: 20px;height: calc(100vh - 184px);" class="mg20">
                <el-form-item class="fulltextarea" style="margin: 0;" prop="question" label="问题" :rules="[
                  {
                    required: true,
                    message: '请填写问题',
                    trigger: 'blur',
                  },
                ]">
                  <el-input v-model="editparam.question" style="width: 100%" :rows="33" type="textarea"
                    placeholder="请填写问题" />
                </el-form-item>
              </div>
            </el-scrollbar>
          </div>
          <div class="frbox">
            <el-scrollbar>
              <div style="margin: 20px;display: flex;flex-wrap: wrap;" class="mg20">
                <el-form-item style="width: calc(33% - 16px);" prop="type" label="测试类别">
                  <div style="width: 100%" class="typelist">
                    <!-- :default-checked-keys="defaultCheckedKeys" show-checkbox @check-change="handleCheckChange" -->
                    <el-tree-select v-model="editparam.cate_id" filterable check-strictly :props="{
                      children: 'children',
                      label: 'name',
                      value: 'id',
                    }" node-key="id" popper-class="c-treebox" :default-expand-all="true" :check-on-click-node="true"
                      :data="get_cateslist()">
                      <template #default="{ node, data }">
                        <div :title="data.name" class="custom-tree-node">
                          <div class="item">
                            <span class="c-color radius" :style="'background-color:' + data.color"></span>{{ data.name
                            }}
                          </div>
                        </div>
                      </template>
                    </el-tree-select>
                  </div>
                </el-form-item>

                <el-form-item class="c-switchbox-label" style="width: calc(33% - 16px);margin-right: 16px;" prop="is_marked" label="是否审核">
                  <div class="c-switchbox">
                    <div class="label"></div>
                    <div class="switch">
                      <el-switch v-model="editparam.is_marked" inline-prompt active-text="审核" inactive-text="未审核" />
                    </div>
                  </div>
                </el-form-item>
                <el-form-item class="c-switchbox-label" style="width: 34%;margin-right: 0;" prop="is_modified" label="是否更正">
                  <div class="c-switchbox">
                    <div class="label"></div>
                    <div class="switch">
                      <el-switch v-model="editparam.is_modified" inline-prompt active-text="更正" inactive-text="未更正" />
                    </div>
                  </div>
                </el-form-item>

                <el-form-item style="width: 100%;margin-right: 0;" prop="right_answer" class="js-answer" label="参考答案" :rules="[
                  {
                    required: true,
                    message: '请填写参考答案',
                    trigger: 'blur',
                  },
                ]">
                  <el-input v-model="editparam.right_answer" style="width: 100%" :rows="8" type="textarea"
                    placeholder="请填写参考答案" />
                </el-form-item>

                <el-form-item style="width: 100%;margin-right: 0;" prop="note" label="备注">
                  <el-input v-model="editparam.note" style="width: 100%" :rows="4" type="textarea"
                    placeholder="请填写备注" />
                </el-form-item>

                <el-form-item style="width: 100%;margin-right: 0;" v-if="props.TEST_TYPE == 'S'" prop="test_standard" label="测试标准">
                  <el-input v-model="editparam.test_standard" style="width: 100%" :rows="4" type="textarea"
                    placeholder="请填写测试标准" />
                </el-form-item>

                <el-form-item style="width: 100%;margin-right: 0;" prop="" class="js-answer" label="视觉文件">
                    <div>{{ props.curResult && props.curResult.vision_file_str || '无' }}</div>
                  </el-form-item>

                <el-form-item style="width: 100%;margin-right: 0;" prop="llm_id" label="选择大模型">
                    <el-select style="width: 100%" v-model="editparam.llm_id" class="val" filterable
                      placeholder="" multiple collapse-tags collapse-tags-tooltip :max-collapse-tags="3">
                      <el-option v-for="item in llmlist" :value="parseInt(item.id, 10)" :label="item.name"></el-option>
                    </el-select>

                    <div class="llmbox">
                      <span class="c-tips">* 通过大模型辅助生成参考答案</span>
                      <el-button type="primary" @click="try_answerfn()"
                      :disabled="!(editparam.llm_id && editparam.question)">生成参考答案</el-button>
                    </div>
                    
                </el-form-item>
                <div v-if="checkids && checkids.length>0" class="anslist">
                  <div class="title"><span class="el-form-item__label">生成结果</span><span class="c-primary-btn">{{ checkids.length }}</span></div>
                  <div class="item" v-for="(item, index) in checkids" v-loading="item.loading" :key="index">
                    <div class="title"><span>{{ item.name }}<span v-if="item.time" class="time c-warn-btn">{{ ((item.time -
                      starttimer) / 1000).toFixed(2) }} s</span></span> 
                     
                        <span @click="editparam.right_answer = item.right_answer; scrollToTop('.js-answer')" class="c-pointer c-flex-center">
                          <span class="iconfont icon-xuanzedaan"></span>
                          选择答案
                        </span>
                      </div>
                    <el-input v-model="item.right_answer" style="width: 100%" :autosize="{ minRows: 4, maxRows: 20 }" type="textarea"
                      placeholder="请填写参考答案" />
                  </div>
                </div>
              </div>
            </el-scrollbar>
          </div>
        </div>
      </el-form>
    </div>
    <div class="dialog-footer">
      <el-button type="primary" @click="subeditfn(formRef1)"> 确定 </el-button>
      <el-button @click="close()" plain>取消</el-button>
    </div>
  </el-drawer>
</template>
<style scoped>
.anslist{
  display: block;
    width: 100%;
    text-align: left;
}
.llmbox{
  display: flex;
  width: 100%;
  align-items: center;
  justify-content: space-between;
  margin-top: 20px;
}
.c-addtestdialog .fulltextarea :deep(.el-form-item__content) {
  height: calc(100% - 30px);
}

.c-addtestdialog .anslist :deep(.el-textarea__inner){
  box-shadow: none;
}

.fulltextarea {
  height: 100%;
}

.c-addtestdialog .fulltextarea :deep(.el-textarea__inner),
.c-addtestdialog .fulltextarea :deep(.el-textarea) {
  height: 100%;
}



.anslist .item {
  margin-bottom: 10px;
  box-shadow: 0px 4px 6px 0px rgba(228, 228, 228, 0.5);
    border-radius: 16px;
    border: 1px solid #DBE2EA;
    overflow: hidden;
}

.anslist .item .time {
  font-size: 12px;
  font-weight: normal;
  margin-left: 5px;
}

.anslist .item .title {
  display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 14px;
    padding: 5px 16px;
    color: #333;
    background: #F7F9FA
}

.anslist .item .title .btn {
  flex-shrink: 0;
}

.demo-dynamic {
  height: 100%;
}

.formbox {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  height: 100%;
  width: 100%;
  box-sizing: border-box;
}

.formbox .flbox,
.formbox .frbox {
  height: 100%;
  width: 50%;
  box-sizing: border-box;
}

.formbox .flbox {
  border-right: 1px solid var(--el-border-color);
}

.formbox .flex {
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  line-height: 24px;
}

.isShowAddDialogBox {
  height: calc(100% - 25px);
  margin: -20px;
  box-sizing: border-box;
}


</style>