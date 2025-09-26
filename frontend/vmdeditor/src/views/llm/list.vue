<script setup>
import {
  ref,
  nextTick,
  shallowRef,
  getCurrentInstance,
  onActivated,
  reactive,
  watch,
} from "vue";
import { onBeforeRouteLeave, useRoute, useRouter } from "vue-router";
import { useStore } from "vuex";
import {
  model_configdelete,
  model_configall,
  model_configadd,
} from "@/api/api";
import { goback, getTime } from "@/components/comp.js";
const route = useRoute();
const router = useRouter();

const props = defineProps({
  proType: {
    type: [String, Number],
    default: () => '',
  },
  isCheck: {
    type: [Boolean],
    default: () => false,
  },
  checkList: {
    type: [Array],
    default: () => [],
  }
});



const store = useStore();
let { proxy } = getCurrentInstance();
const dialogFormVisible1 = ref(false);

// 创建文件夹

let pagelist = ref([]);

const total = ref(0);

const page = ref(1);
const pagesize = ref(36);

if (route.query.page) {
  page.value = parseInt(route.query.page);
}
if (route.query.pagesize) {
  pagesize.value = parseInt(route.query.pagesize);
}
const search = (type) => {
  let params = {}
  model_configall(params).then((res) => {
    let arr = res || [];
    pagelist.value = arr;
  });

};

search("noquery");

const emits = defineEmits(['subfn'])


const hislist = ref([]);
const openDialog = async (item) => {
  setFormValues({});
  if (item) {
    setFormValues(item);
  }
  ruleFormRef1.value?.clearValidate();
  dialogFormVisible1.value = true;
};



const setFormValues = (item) => {
  form1.id = item.id || 0;
  form1.name = item.name || "";
  form1.note = item.note || "";
  form1.type = item.type || "LLM";
  form1.base_name = item.base_name || "";
  form1.api_url = item.api_url || "";
  form1.api_key = item.api_key || "";
  form1.max_token = item.max_token ? item.max_token : item.max_token === 0 ? 0 : undefined;
  form1.temprature = item.temprature !== undefined ? item.temprature : 0.5;
  form1.provider = item.provider || "";
  form1.timeout = item.timeout === undefined ? undefined : item.timeout;
};






const del = (id) => {
  _this.$confirm("此操作将永久删除该模型, 是否继续?").then((res) => {
    model_configdelete({ id }).then((res) => {
      _this.$message("删除成功");
      search();
    });
  });
};

// 创建知识库
const form1 = reactive({
  id: 0,
  name: "",
  base_name: "",
  type: "LLM",
  api_url: "",
  api_key: "",
  provider: "",
  timeout: undefined,
  temprature: 0.5,
});
const ruleFormRef1 = ref();

const saveZsk = async (formEl) => {
  if (!formEl) return;
  formEl.validate((valid) => {
    if (valid) {
      model_configadd(form1).then((res) => {
        if (res) {
          _this.$message("提交成功");
          dialogFormVisible1.value = false;
          search();
        }
      });
    } else {
      return false;
    }
  });
};

const tableRef = ref(null);
const llmmap = ref({
  LLM: "文本模型",
  VLM: "视觉模型",
});
</script>

<template>


  <div class="c-titlebox">
    <div class="title">模型配置</div>
    <div class="btns"><el-button size="small" type="primary" @click="openDialog()">新增</el-button></div>
  </div>

  <div class="scrollbox">
    <el-scrollbar ref="tableRef">

      <div class="c-cardbox">
        <div v-for="item in pagelist" @click="openDialog(item)" class="item c-pointer">
          <el-popover :width="160">
            <template #reference>
              <span class="iconfont icon-gengduo c-cardbtn-icon"></span>
            </template>
            <template #default>
              <div @click.stop class="c-cardbtn-btns">


                <div @click="openDialog(item)" class="item">
                  <span class="name">修改</span>
                </div>
                <div @click="del(item.id)" class="item">
                  <span class="name">删除</span>
                </div>
              </div>
            </template>
          </el-popover>
          <div :style="{color: '#fff',background:item.type=='LLM'?'rgb(100,161,255)':'rgb(152,139,255)'}" class="top ellipsis">
            {{ llmmap[item.type] }}
          </div>
          <div class="title ellipsis">
            {{ item.name }}
          </div>
          <div class="intro ellipsis3">
            <span :title="item.base_name" class="base_name">{{ item.base_name }}<br></span>

            <span :title="item.note" class="note" v-if="item.note">
              {{ item.note }}
            </span>
          </div>
        </div>






      </div>
   
    </el-scrollbar>
  </div>


  <el-drawer v-model="dialogFormVisible1" @closed="dialogFormVisible1 = false" size="900"
    :title="form1.id ? '修改大模型' : '创建大模型'" direction="rtl">

    <div class="dformbox c-form-alignleft">
      <el-scrollbar>
        <el-form ref="ruleFormRef1" label-position="top" inline label-width="auto" :model="form1">
          <el-form-item style="width:100%;margin-right: 0;" label="模型类型" prop="provider">
            <el-select v-model="form1.type" filterable placeholder="请选择">
              <el-option value="LLM" label="文本模型"></el-option>
              <el-option value="VLM" label="视觉模型"></el-option>
            </el-select>

          </el-form-item>
          <el-form-item style="width:calc(50% - 8px);margin-right: 16px;" label="自定义名称" :rules="{
            trigger: 'blur',
            required: true,
            message: '请输入自定义的大模型名称',
          }" prop="name">
            <el-input class="autofocus inp2" placeholder="请输入自定义的大模型名称" v-model="form1.name" maxlength="50"
              autocomplete="off" />
          </el-form-item>

          <el-form-item style="width:calc(50% - 8px);margin-right: 0px;" label="基础模型" prop="base_name">
            <el-input placeholder="要使用基础模型的名称" v-model="form1.base_name" autocomplete="off" />
          </el-form-item>

          <el-form-item style="width:100%;margin-right: 0;" label="API接口地址" prop="api_url">
            <el-input placeholder="输入服务器API URL地址" v-model="form1.api_url" autocomplete="off" />
          </el-form-item>

          <el-form-item style="width:100%;margin-right: 0;" label="APIKEY" prop="api_key">
            <el-input type="password" show-password placeholder="请输入APIKEY" v-model="form1.api_key" autocomplete="off" />
          </el-form-item>

          <el-form-item style="width:calc(50% - 8px);margin-right: 16px;" label="模型接口格式" prop="provider">
            <el-select v-model="form1.provider" filterable placeholder="请选择">
              <el-option value="OpenAI" label="OpenAI"></el-option>
              <el-option value="ZhipuAI" label="ZhipuAI"></el-option>
              <el-option value="Ollama" label="Ollama"></el-option>
              <!-- <el-option value="Tongyi" label="Tongyi"></el-option> -->
            </el-select>

          </el-form-item>

          <el-form-item style="width:calc(50% - 8px);margin-right: 0px;" label="温度" prop="temprature">
            <el-slider style="width: calc(100% - 10px)" v-model="form1.temprature" :step="0.1" :min="0" :max="1" />
          </el-form-item>

          <el-form-item style="width:calc(50% - 8px);margin-right: 16px;" prop="temprature">
            <template #label>
              最大输出token
              <el-tooltip effect="light" raw-content
              content="此处留空的话则为推理框默认值 <span class='c-danger'>(注意:部分框架可能不支持 限制最大输出token)</span>" placement="right">
              <span style="margin-left: 3px;" class="iconfont icon-bangzhu c-danger"></span>
            </el-tooltip>
            </template>
            <el-input-number style="width: 100%" @focus="$event.target.select();" v-model="form1.max_token"
              placeholder="" :min="0" :precision="0" :step="1" :controls="false" />
            
          </el-form-item>

          <el-form-item style="width: calc(50% - 8px);margin-right: 0;" label="超时时间（秒）" prop="price">
            <el-input-number style="width: 100%;" @focus="$event.target.select();" :controls="false" :min="0"
              :precision="0" placeholder="请输入超时时间" v-model="form1.timeout"></el-input-number>
          </el-form-item>


          <el-form-item style="width:100%;margin-right: 0;" prop="note" label="备注">
            <el-input v-model="form1.note" style="width: 100%" :rows="5" type="textarea" placeholder="请填写备注" />
          </el-form-item>

        </el-form>
      </el-scrollbar>
    </div>

    <div class="dialog-footer">
      
      <el-button type="primary" @click="saveZsk(ruleFormRef1)">
        确认提交
      </el-button>
      <el-button @click="dialogFormVisible1 = false" plain>取消</el-button>
    </div>
  </el-drawer>

  <!-- 新建文件夹 -->

</template>

<style scoped>
.c-cardbox .item .top{
  
}
.scrollbox {
  height: calc(100% - 0px);
}
.dformbox {
  display: block;
  height: calc(100% - 70px);
}

.historybox .title1 {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 10px;
}

.icon-zhishiku {
  color: var(--el-color-primary);
}

.icon-zhishikuguanli {
  color: var(--el-color-success);
}

.icon-peizhi {
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

.listbox {
  display: block;
  text-align: center;
}

.listbox .icon-peizhi {
  font-size: 20px;
}

.pagelistbox {
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  flex-wrap: wrap;
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
  text-align: left;
}

.namebox .lbox .iconfont {
  flex-shrink: 0;
  font-size: 20px;
  margin-right: 5px;
}

.namebox .lbox .name {
  text-align: left;
  display: inline-block;
  width: 310px;
}

.name {
  word-break: break-all;
}

.introbox {
  word-break: break-all;
  text-align: left;
  color: #999;
  margin-top: 8px;
  font-size: 12px;
}

.botbox {
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: absolute;
  left: 20px;
  bottom: 10px;
  right: 20px;
  height: 30px;
  font-size: 14px;
}

.botbox .rbox .bitem {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  background: var(--chakra-colors-myGray-100);
  border: 1px solid var(--chakra-colors-myGray-200);
  border-radius: var(--chakra-radii-md);
  padding: 0px 10px;
}

.botbox .rbox .bitem .iconfont {
  color: #333;
}

.icon-shugui {
  color: var(--chakra-colors-primary-600);
  font-size: 20px;
}
</style>
