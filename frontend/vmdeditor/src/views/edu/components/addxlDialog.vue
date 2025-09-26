<script setup>
import { ref, nextTick, onMounted, reactive, watch } from "vue";
import { useStore } from "vuex";
import { useRoute, useRouter } from "vue-router";
import { cloneDeep } from "lodash"; // 引入lodash库的cloneDeep方法进行深拷贝
import {
  train_case_add,
  get_cates,
  try_answer,
  model_configall,
} from "@/api/api";
import { scrollToTop } from "@/assets/utils/util";
const props = defineProps({
  id: {
    type: [String, Number],
    default: () => 0,
  },
  title: {
    type: [String, Number],
    default: "测试用例",
  },
  TEST_TYPE: {
    type: [String, Number],
    default: "W",
  },
  item: {
    type: Object,
    default: () => {return {}; },
  },
  curResult: {
    type: Object,
    default: () => { return {};  },
  },
  modelValue: { type: Boolean, default: false },
});
const emits = defineEmits(["subfn", "update:modelValue"]);
const route = useRoute();
const router = useRouter();
const store = useStore();

// S单元测试 W流程测试

const dialogFormVisible = ref(false);
const editparam = reactive({
  id: 0,
  train_cate_id: 0,
  input_data: "",
  output_data: "",
});
watch(
  () => props.modelValue,
  async (n, old) => {
    if (n !== old && n) {
      if (formRef1.value) {
        formRef1.value.clearValidate();
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
  editparam.llm_id = undefined;
  editparam.node_id = item.node_id || undefined;
  editparam.is_marked = !!item.is_marked;
  editparam.is_modified = !!item.is_modified;
  editparam.input_data = item.input_data || "";
  editparam.output_data = item.output_data || "";
  editparam.train_cate_id = item.train_cate_id || 0;
  editparam.feature = item.feature || undefined;
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

const searchCate = (params) => {
  if (dataSource.value.length < 1) {
    get_cates({}).then(async (res) => {
      dataSource.value = res || [];
    });
  }
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
      train_case_add(editparam).then((res) => {
        if (res) {
          let curitem = null;
          findAndAddCategory(
            get_cateslist(),
            editparam.train_cate_id,
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
      input: editparam.input_data,
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


const llmlist = ref([]);
//  获取大模型配置

const getllmlist = () => {
  if (llmlist.value.length > 0) return;
  model_configall({ page: 1, pagesize: 10000 }, props.TEST_TYPE).then((res) => {
    llmlist.value = res || [];
  });
};

const setLocalllm = (val) => {
  let localKey = "edulocal_llm";
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
  <el-drawer v-model="dialogFormVisible" :title="title" @closed="close" direction="rtl" :close-on-click-modal="true"
    size="90%">
    <div class="isShowAddDialogBox c-scroll-contain c-addtestdialog dformbox">
      
        <el-form ref="formRef1" :model="editparam" label-position="top" label-width="auto" inline class="demo-dynamic">
          <div class="formbox">
            <div class="flbox">
              <el-scrollbar>
                <div style="margin: 20px;height: calc(100vh - 184px);" class="mg20">
                  <el-form-item class="fulltextarea" style="margin: 0;" prop="input_data" label="输入数据" :rules="[
                    {
                      required: false,
                      message: '请填写输入数据',
                      trigger: 'blur',
                    },
                  ]">
                    <el-input v-model="editparam.input_data" style="width: 100%" :rows="36" type="textarea"
                      placeholder="请填写输入数据" />
                  </el-form-item>
                </div>
              </el-scrollbar>
            </div>
            <div class="frbox">
              <el-scrollbar>
                <div style="margin: 20px;display: flex;flex-wrap: wrap;" class="mg20">
                  <template v-if="!(props.item && props.item.__isTs__)">
                  <el-form-item style="width: calc(33% - 16px);" prop="type" label="语料类别">
                    <div style="width: 100%" class="typelist">
                      <el-tree-select v-model="editparam.train_cate_id" filterable check-strictly :props="{
                        children: 'children',
                        label: 'name',
                        value: 'id',
                      }" node-key="id" popper-class="c-treebox" :default-expand-all="true" :check-on-click-node="true"
                        :data="get_cateslist()">
                        <template #default="{ node, data }">
                          <div :title="data.name" class="custom-tree-node">
                            <div class="item">
                              <span class="c-color" :style="'background-color:' + data.color"></span>
                              <p class="ellipsis">{{ data.name }}</p>
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
                      <el-switch v-model="editparam.is_marked" inline-prompt active-text="是" inactive-text="否" />
                    </div>
                  </div>
                  </el-form-item>
                  <el-form-item class="c-switchbox-label" style="width: 34%;margin-right: 0;" prop="is_modified" label="是否更正">
                    <div class="c-switchbox">
                    <div class="label"></div>
                    <div class="switch">
                      <el-switch v-model="editparam.is_modified" inline-prompt active-text="是" inactive-text="否" />
                    </div>
                  </div>
                  </el-form-item>

                  <el-form-item style="width: 100%;margin-right: 0;" prop="output_data" class="js-answer" label="输出数据" :rules="[
                    {
                      required: false,
                      message: '请填写输出数据',
                      trigger: 'blur',
                    },
                  ]">
                    <el-input v-model="editparam.output_data" style="width: 100%" :rows="10" type="textarea"
                      placeholder="请填写输出数据" />
                  </el-form-item>

                  <el-form-item style="width: 100%;margin-right: 0;" :rules="[
                    {
                      required: true,
                      message: '请填写特征概要',
                      trigger: 'blur',
                    },
                  ]" prop="feature" label="特征概要">
                    <el-input v-model="editparam.feature" style="width: 100%" :rows="5" type="textarea"
                      placeholder="请填写特征概要" />
                  </el-form-item>

                </template>

                  <el-form-item style="width: 100%;margin-right: 0;" prop="" class="js-answer" label="视觉文件">
                    <div>{{ props.curResult && props.curResult.vision_file_str || '无' }}</div>
                  </el-form-item>

                  <el-form-item style="width: 100%;margin-right: 0;" prop="llm_id" label="选择大模型">
                      <el-select style="width: 100%" v-model="editparam.llm_id" class="val" filterable
                        placeholder="" multiple collapse-tags collapse-tags-tooltip :max-collapse-tags="3">
                        <el-option v-for="item in llmlist" :value="parseInt(item.id, 10)"
                          :label="item.name"></el-option>
                      </el-select>
                      <div class="llmbox">
                      <span class="c-tips">* 通过选择的大模型生成参考输出</span>
                      <el-button type="primary" @click="try_answerfn()"
                        :disabled="!(editparam.llm_id && editparam.input_data)" size="small">生成参考输出</el-button>
                    </div>
                  </el-form-item>

                  <div v-if="checkids && checkids.length>0" class="anslist">
                    <div class="title"><span class="el-form-item__label">生成结果</span><span class="c-primary-btn">{{ checkids.length }}</span></div>
                    <div class="item" v-for="(item, index) in checkids" :key="index" v-loading="item.loading">
                      <div class="title">
                        <span>{{ item.name }}<span v-if="item.time" class="time">({{ ((item.time -
                          starttimer) / 1000).toFixed(2) }} s)</span></span>
                        
                          <span @click="editparam.output_data = item.right_answer; scrollToTop('.js-answer')" class="c-pointer c-flex-center">
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
      <el-button plain @click="close()">取消</el-button>
      <el-button v-if="!(props.item && props.item.__isTs__)" type="primary" @click="subeditfn(formRef1)"> 确定 </el-button>
    </div>
  </el-drawer>
</template>
<style scoped>
.anslist {
  display: block;
  width: 100%;
  text-align: left;
}

.llmbox {
  display: flex;
  width: 100%;
  align-items: center;
  justify-content: space-between;
  margin-top: 20px;
}

.c-addtestdialog .fulltextarea :deep(.el-form-item__content) {
  height: calc(100% - 30px);
}

.c-addtestdialog .anslist :deep(.el-textarea__inner) {
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