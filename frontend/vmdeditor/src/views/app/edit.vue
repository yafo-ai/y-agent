<script setup>
import { ref, nextTick, onMounted, reactive, watch } from "vue";
import { useStore } from "vuex";
import { useRoute, useRouter } from "vue-router";

import { goback, getTime } from "@/components/comp.js";
import { promptsAdd, promptsversions, promptsversionsDetail, promptstree, node_prompt_debug } from "@/api/api";
import Editor from "@/components/editor.vue";
const props = defineProps({
  id: {
    type: [String, Number],
    default: () => 0,
  },
  curflowid: {
    type: [String, Number],
    default: "",
  },
  curdataid: {
    type: [String, Number],
    default: "",
  },
  title: {
    type: [String, Number],
    default: "",
  },
  nodes: {
    type: [Array],
    default: () => [],
  },
  edges: {
    type: [Array],
    default: () => [],
  },
  nodeid: {
    type: String,
    default: "",
  },
  item: {
    type: Object,
    default: {
      name: "",
      content: "",
      id: undefined,
      prompt_type_id: null,
    },
  },
  modelValue: { type: Boolean, default: false },
});
const emits = defineEmits(["subfn", "update:modelValue", "errfn"]);
const route = useRoute();
const router = useRouter();
const store = useStore();

const dialogFormVisible = ref(false);
const dataSource = ref([]);
watch(
  () => props.modelValue,
  async (n, old) => {
    curshowPrompt.value = "";
    if (n !== old && n) {
      let res = await promptstree();
      dataSource.value = res || [];
    }

    if (props.item) {
      setFormValues(props.item);
    }

    if (props.item && props.item.id && n && !old) {
      promptsversions(props.item.id)
        .then((res) => {
          hislist.value = res || [];
          if (res && res.length > 0) {
            getDetail(res[0]);
          }
        })
        .catch((err) => {
          emits("errfn", err.response && err.response.data);
          close();
        });
    } else {
      dialogFormVisible.value = n;
      // focusOnInput();
    }
  }
);

const close = () => {
  dialogFormVisible.value = false;
  emits("update:modelValue", false);
};

const curver = ref(0);
const getDetail = (item) => {
  curver.value = item.ver;
  promptsversionsDetail({ ver: item.ver, id: item.id }).then((res) => {
    if (res) {
      res.id = item.id;
      setFormValues(res);
      dialogFormVisible.value = true;
      // focusOnInput();
    }
  });
};
const form1 = reactive({
  name: "",
  content: "",
  id: undefined,
  prompt_type_id: null,
});
const hislist = ref([]);

const clone_form = ref("");

const setFormValues = (item) => {
  form1.id = item.id;
  form1.name = item.name;
  form1.content = item.content;
  form1.prompt_type_id = item.prompt_type_id ? parseInt(item.prompt_type_id, 10) : null;

  clone_form.value = item.name + item.content + item.prompt_type_id;
  if (editor.value) {
    editor.value.setValue(form1.content);
  }
};


const ruleFormRef1 = ref();
const rules1 = reactive({
  name: [{ required: true, message: "请输入提示词名称" }],
});
const saveZsk = async (formEl) => {
  if (!formEl) return;

  formEl.validate((valid) => {
    if (valid) {
      // if(clone_form.value === form1.name + form1.content + form1.prompt_type_id) {
      //   _this.$message("无修改内容，无需提交","error");
      //   return false;
      // }
      promptsAdd(form1).then((res) => {
        if (res) {
          if (res.id) {
            form1.id = res.id;
          }
          _this.$message("提交成功");
          emits("subfn", form1);
        }
      });
    } else {
      // focusOnInput();
      return false;
    }
  });
};

const editHeight = ref(window.innerHeight - 290);

const testSize = ref("1600px");
if (window.innerWidth > 2200) {
  testSize.value = "2000px";
}

if (window.innerWidth < 1400) {
  testSize.value = "100%";
}

const editor = ref(null);
const curshowPrompt = ref("");
const node_run_debugfn = () => {
  node_prompt_debug({
    "flow_id": props.curflowid,
    "runner_id": props.curdataid + '',
    prompt_temp: form1.content
  }).then((res) => {
    // 调试提示词
    curshowPrompt.value = res.prompt_str;

  })
}

</script>
<template>
  <el-drawer direction="rtl" v-model="dialogFormVisible" :title="form1.id ? '修改提示词' : '创建提示词'" @close="close"
    :destroy-on-close="true" size="90%">
    <div class="dialogFormVisible1box">
      <div v-if="hislist.length > 0 && form1.id" class="historybox c-history">
        <el-scrollbar>
          <div class="mg20">
            <div class="title1">历史记录</div>
            <div v-for="item in hislist" @click="getDetail(item)" :key="item.ver" :class="{ on: item.ver == curver }"
              class="item">
              <div :title="item.name" class="name ellipsis3">
                {{ item.name }} <span style="margin-left: 5px;" class="c-warn-btn c-mini radius">{{ item.ver }}</span> 
              </div>
              <div class="timebox">
                <span class="time">{{ getTime(item.created_at) }}</span>
              </div>
            </div>
          </div>
        </el-scrollbar>
      </div>
      <div class="formbox" :class="{ on: !(hislist.length > 0 && form1.id) }">
        <el-form ref="ruleFormRef1" :rules="rules1" label-width="auto" label-position="top" inline :model="form1">
          <el-form-item label="提示词名称" style="width: calc(100% - 316px);" prop="name">
            <el-input class="autofocus inp2" placeholder="请输入提示词名称" v-model="form1.name" maxlength="50"
              autocomplete="off" />
          </el-form-item>
          <el-form-item label="提示词分类" style="width: 300px;margin-right: 0;" prop="prompt_type_id">

            <el-tree-select v-model="form1.prompt_type_id" filterable check-strictly :node-key="'id'"
              :props="{ children: 'children', label: 'name', value: 'id' }" :default-expand-all="true"
              :check-on-click-node="true" :data="dataSource" style="width: 100%">
              <template #default="{ node, data }">
                <span>{{ data.name }}</span>
              </template>
            </el-tree-select>
          </el-form-item>

          <el-form-item style="width: 100%;margin-right: 0;position: relative;" label="提示词内容" prop="caption">
            <template #label>
              <span>提示词内容</span><span style="display: inline-flex;
    align-items: center;" class="c-tips"><span style="margin-right: 5px;"
                  class="iconfont icon-bangzhu1"></span>调用本系统内置函数可以使用：sys. role. [空格].
                触发提示下拉框。提示词模板使用jinja模板，更多语法参考jinja官方文档。</span>
              <el-button v-if="props.curdataid && props.curflowid" @click="node_run_debugfn"
                style="position: absolute;right: 10px;top: 0px;" type="primary" plain size="small">运行一次 <span class="iconfont icon-liebiao-zhihang"></span></el-button>
            </template>
            <div class="contentbox">
              <div :style="'height:' + editHeight + 'px;' + (props.curdataid && props.curflowid ? 'width:50%' : 'width:100%')">
                <Editor :lineNumbers="'on'" :fontSize="14" ref="editor" :nodes="nodes" :edges="edges" :nodeid="nodeid"
                  v-model="form1.content"></Editor>
              </div>
              <div class="previewbox" v-if="props.curdataid && props.curflowid"
                :style="'height:' + editHeight + 'px;width:calc(50% - 20px)'">
                <el-scrollbar>
                <v-md-preview :text="curshowPrompt"></v-md-preview>
              </el-scrollbar>
              </div>
            </div>

            <!-- <el-input
              v-model="form1.content"
              :rows="20"
              type="textarea"
              placeholder="这个提示词还没有内容~"
            /> -->
          </el-form-item>
        </el-form>
      </div>
    </div>
    <div class="dialog-footer">

      <el-button type="primary" @click="saveZsk(ruleFormRef1)">
        确定
      </el-button>
      <el-button @click="close()" plain>取消</el-button>
    </div>
  </el-drawer>
</template>
<style scoped>
.previewbox{
  background: #fbfbfb;
    border-radius: 6px;
}
.contentbox {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  width: 100%;
}

.dialogFormVisible1box {
  display: flex;
  width: 100%;
  height: calc(100% - 46px);
  text-align: left;
}

.dialogFormVisible1box .formbox {
  width: calc(100% - 300px);
  padding-left: 20px;
}

.dialogFormVisible1box .formbox.on {
  width: 100%;
}

.historybox .title1 {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 10px;
}

.dialogFormVisible1box .historybox {
  width: 300px;
  flex-shrink: 0;
  box-sizing: border-box;
  padding: 20px 0;
  text-align: left;
  border-right: 1px solid var(--el-border-color);
  margin: -20px 0;
}

.dialogFormVisible1box .historybox .mg20 {
  margin: 0 20px 0 0;
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
  font-size: 16px;
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  line-height: 20px;
}


.icon-zhishiku {
  color: var(--el-color-primary);
}

.icon-zhishikuguanli {
  color: var(--el-color-success);
}
</style>