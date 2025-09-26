<script setup>
import { ref, nextTick, onMounted, reactive, watch } from "vue";
import { useStore } from "vuex";
import { useRoute, useRouter } from "vue-router";
import { config, batch_update } from "@/api/api";
import { cloneDeep } from "lodash"; // 引入lodash库的cloneDeep方法进行深拷贝
const props = defineProps({
  curContext: {
    type: Array,
    default: [],
  },
  type: {
    type: String,
    default: "text",
  },
  title: {
    type: String,
    default: "系统配置",
  },
  modelValue: { type: Boolean, default: false },
});
const emits = defineEmits(["subfn", "update:modelValue"]);
const route = useRoute();
const router = useRouter();
const store = useStore();

const dialogFormVisible = ref(false);
const size = ref('1000px');
watch(
  () => props.modelValue,
  (n, o) => {
    dialogFormVisible.value = n;
    if (n && o !== n) {
      init()
    }
  }
);

const close = () => {
  emits("update:modelValue", false);
};

const sub = (formEl) => {
  if (!formEl) return;
  formEl.validate((valid) => {
    if (valid) {
      form1.value['sys_config.vector_provider']['config_value_obj']['selected']['connect_str'] = JSON.parse(connectstr.value)
      let params = cloneDeep(form1.value);
     
      Object.keys(params).forEach((key) => {
        if (params[key].config_value_obj) {
          params[key].config_value = JSON.stringify(params[key].config_value_obj); // 将对象转换为字符串
          delete params[key].config_value_obj; // 删除原始对象，避免发送多余数据
        }
      });
     

      console.log(params)
      batch_update(params).then((res) => {
        _this.$message('配置更新成功！','success');
        emits("subfn", params);
        close()
      })

    } else {
      return false;
    }
  });


};
const init = () => {
  config().then((res) => {
    if (res) {
      Object.keys(res).forEach(key => {
        res[key].config_value_obj = JSON.parse(res[key].config_value);
        form1.value[key] = res[key];
      });
      console.log(form1.value);
      connectstr.value = JSON.stringify(form1.value['sys_config.vector_provider']['config_value_obj']['selected']['connect_str'])
      changeType()
    }
  })
  ruleFormRef1.value?.clearValidate();
};
const ruleFormRef1 = ref();
const form1 = ref({});

const connectstr = ref('')

const curTypes = ref([]);
const changeType = (val) => {
  let name = form1.value['sys_config.vector_provider']['config_value_obj']['selected']['provider_name'];
  let arr = form1.value['sys_config.vector_provider']['config_value_obj']['providers'];

  console.log(name, arr)
  arr.forEach((item) => {
    if (item.provider_name === name) {
      curTypes.value = item.connect_type;
    }
  })
};



</script>
<template>
  <el-drawer :title="title" @closed="close" v-model="dialogFormVisible" direction="rtl" :size="size">
    <div v-if="form1['sys_config.base']" class="dformbox c-form-alignleft">
      <el-scrollbar>
        <div style="margin: 0 20px;">
          <el-form ref="ruleFormRef1" label-position="top" inline label-width="auto" :model="form1">
            <div class="ftitle">基本设置
              <el-tooltip popper-class="c-flowtip" class="item" effect="dark"
                content="基本设置保存在本地配置文件中，如需修改请编辑server_config.py文件，修改后需重启服务端" placement="top">
                <span class="iconfont icon-bangzhu"></span>
              </el-tooltip>
            </div>
            <!-- <el-form-item style="width:100%;margin-right: 0;" label="项目名称" :rules="{
            trigger: 'blur',
            required: true,
            message: '请输入项目名称',
          }" prop="name">
            <el-input placeholder="" disabled v-model="form1.name" maxlength="50"
              autocomplete="off" />
          </el-form-item> -->

            <el-form-item style="width:calc(50% - 8px);margin-right: 16px;" prop="base_name">
              <template #label>
                主机
                <el-tooltip popper-class="c-flowtip" class="item" effect="dark" content="fastapi_host:项目启动时绑定的主机"
                  placement="top">
                  <span class="iconfont icon-bangzhu"></span>
                </el-tooltip>
              </template>
              <el-input placeholder="" disabled v-model="form1['sys_config.base']['config_value_obj']['fastapi_host']"
                autocomplete="off" />
            </el-form-item>

            <el-form-item style="width:calc(50% - 8px);margin-right: 0px;" prop="base_name">
              <template #label>
                端口
                <el-tooltip popper-class="c-flowtip" class="item" effect="dark"
                  content="fastapi_port:项目启动时绑定端口，必须为大于50小于65534的整数" placement="top">
                  <span class="iconfont icon-bangzhu"></span>
                </el-tooltip>
              </template>
              <el-input placeholder="" disabled v-model="form1['sys_config.base']['config_value_obj']['fastapi_port']"
                autocomplete="off" />
            </el-form-item>

            <el-form-item style="width:calc(50% - 8px);margin-right: 16px;" prop="base_name">
              <template #label>
                数据库
                <el-tooltip popper-class="c-flowtip" class="item" effect="dark" content="db_connect_str:数据库连接字符串"
                  placement="top">
                  <span class="iconfont icon-bangzhu"></span>
                </el-tooltip>
              </template>
              <el-input placeholder="" disabled v-model="form1['sys_config.base']['config_value_obj']['db_connect_str']"
                autocomplete="off" />
            </el-form-item>

            <el-form-item class="c-switchbox-label" style="width:calc(50% - 8px);margin-right: 0px;" prop="base_name">
              <template #label>
                系统日志
                <el-tooltip popper-class="c-flowtip" class="item" effect="dark"
                  content="is_record_operationlog:是否记录操作日志" placement="top">
                  <span class="iconfont icon-bangzhu"></span>
                </el-tooltip>
              </template>
              <div class="c-switchbox" disabled>
                <div class="label"></div>
                <div class="switch">
                  <el-switch disabled
                   inline-prompt active-text="是" inactive-text="否"
                    v-model="form1['sys_config.base']['config_value_obj']['is_record_operation_log']" />
                </div>
              </div>
            </el-form-item>

            <el-form-item style="width:100%;margin-right: 0;" prop="base_name">
              <template #label>
                项目名称
                <el-tooltip popper-class="c-flowtip" class="item" effect="dark" content="web_name:项目名称" placement="top">
                  <span class="iconfont icon-bangzhu"></span>
                </el-tooltip>
              </template>
              <el-input placeholder="" disabled v-model="form1['sys_config.base']['config_value_obj']['web_name']"
                autocomplete="off" />
            </el-form-item>

            <el-form-item style="width:100%;margin-right: 0px;" prop="base_name">
              <template #label>
                项目说明
                <el-tooltip popper-class="c-flowtip" class="item" effect="dark" content="web_desc:项目说明" placement="top">
                  <span class="iconfont icon-bangzhu"></span>
                </el-tooltip>
              </template>
              <el-input type="textarea" :autosize="{ minRows: 2, maxRows: 6 }" placeholder="" disabled
                v-model="form1['sys_config.base']['config_value_obj']['web_desc']" autocomplete="off" />
            </el-form-item>

            <div class="ftitle">知识库配置
              
            </div>

            <el-form-item style="width:calc(50% - 8px);margin-right: 16px;" prop="temprature">
              <template #label>
                切块大小
                <el-tooltip popper-class="c-flowtip" class="item" effect="dark" content="分割块大小，具体切分策略查看帮助文档，单位(字符)"
                  placement="top">
                  <span class="iconfont icon-bangzhu"></span>
                </el-tooltip>
              </template>
              <el-input-number style="width: 100%" @focus="$event.target.select();"
                v-model="form1['sys_config.knowledge']['config_value_obj']['chunk_size']" placeholder="" :min="0"
                :precision="0" :step="1" :controls="false" />
            </el-form-item>

            <el-form-item style="width:calc(50% - 8px);margin-right: 0px;" prop="temprature">
              <template #label>
                重叠大小
                <el-tooltip popper-class="c-flowtip" class="item" effect="dark"
                  content="两个相邻的分割块之间重叠的大小，具体切分策略查看帮助文档，单位(字符)" placement="top">
                  <span class="iconfont icon-bangzhu"></span>
                </el-tooltip>
              </template>
              <el-input-number style="width: 100%" @focus="$event.target.select();"
                v-model="form1['sys_config.knowledge']['config_value_obj']['chunk_size_overlap']" placeholder=""
                :min="0" :precision="0" :step="1" :controls="false" />
            </el-form-item>

            <div class="ftitle">安全配置
              <el-tooltip popper-class="c-flowtip" class="item" effect="dark" content="本系统使用JWVT加密算法，作为安全验证算法"
                placement="top">
                <span class="iconfont icon-bangzhu"></span>
              </el-tooltip>
            </div>

            <el-form-item style="width:calc(50% - 8px);margin-right: 16px;" prop="temprature">
              <template #label>
                令牌过期时间
                <el-tooltip popper-class="c-flowtip" class="item" effect="dark"
                  content="访问令牌过期时间(分钟)，指用户在登陆过后多长时间登陆状态(令牌)失效，建议48小时以上" placement="top">
                  <span class="iconfont icon-bangzhu"></span>
                </el-tooltip>
              </template>
              <el-input-number style="width: 100%" @focus="$event.target.select();"
                v-model="form1['sys_config.security']['config_value_obj']['access_token_expire_minutes']" placeholder=""
                :min="0" :precision="0" :step="1" :controls="false" />
            </el-form-item>

            <el-form-item style="width:calc(50% - 8px);margin-right: 0px;" prop="temprature">
              <template #label>
                令牌刷新时间
                <el-tooltip popper-class="c-flowtip" class="item" effect="dark"
                  content="自动刷新访问令牌时间(分钟)，指用户在登陆状态失效之前的多长时间，自动延长令牌失效时间，一般设置应超过24小时" placement="top">
                  <span class="iconfont icon-bangzhu"></span>
                </el-tooltip>
              </template>
              <el-input-number style="width: 100%" @focus="$event.target.select();"
                v-model="form1['sys_config.security']['config_value_obj']['refresh_token_expire_minutes']"
                placeholder="" :min="0" :precision="0" :step="1" :controls="false" />
            </el-form-item>

            <div class="ftitle">向量数据库配置

            </div>

            <el-form-item style="width:calc(50% - 8px);margin-right: 16px;" label="提供商" prop="provider">
              <el-select v-model="form1['sys_config.vector_provider']['config_value_obj']['selected']['provider_name']"
                @change="(val) => { form1['sys_config.vector_provider']['config_value_obj']['selected']['connect_type'] = ''; changeType(val) }"
                placeholder="请选择">
                <el-option v-for="item in form1['sys_config.vector_provider']['config_value_obj']['providers']"
                  :value="item.provider_name" :label="item.provider_name"></el-option>
              </el-select>

            </el-form-item>

            <el-form-item style="width:calc(50% - 8px);margin-right: 0;" label="配置项" prop="provider">
              <el-select v-model="form1['sys_config.vector_provider']['config_value_obj']['selected']['connect_type']"
                placeholder="请选择">
                <el-option v-for="item in curTypes" :value="item" :label="item"></el-option>
              </el-select>

            </el-form-item>


            <el-form-item style="width:100%;margin-right: 0;" label="连接字符串" prop="provider">

              <el-input type="textarea" :autosize="{ minRows: 2, maxRows: 6 }" placeholder="" v-model="connectstr"
                autocomplete="off" />

            </el-form-item>

            <div class="ftitle">向量模型配置
              <el-tooltip popper-class="c-flowtip" class="item" effect="dark" content="注意!修改向量模型后会造成已经生成的所有向量失效，请谨慎操作"
                placement="top">
                <span class="iconfont icon-bangzhu"></span>
              </el-tooltip>
            </div>

            <el-form-item style="width:calc(50% - 8px);margin-right: 16px;" label="模型接口格式" >
              <el-select
                v-model="form1['sys_config.embedding_provider']['config_value_obj']['selected']['provider_name']"
                
                placeholder="请选择">
                <el-option v-for="item in form1['sys_config.embedding_provider']['config_value_obj']['providers']"
                  :value="item" :label="item"></el-option>
              </el-select>

            </el-form-item>

            <el-form-item style="width:calc(50% - 8px);margin-right: 0;" label="模型名称">

              <el-input placeholder=""
                v-model="form1['sys_config.embedding_provider']['config_value_obj']['selected']['model_name']"
                autocomplete="off" />

            </el-form-item>
            <el-form-item style="width:calc(50% - 8px);margin-right: 16px;" label="API接口地址" >

              <el-input placeholder=""
                v-model="form1['sys_config.embedding_provider']['config_value_obj']['selected']['connect_url']"
                autocomplete="off" />

            </el-form-item>

            <el-form-item style="width:calc(50% - 8px);margin-right: 0;" label="APIKEY" >

              <el-input placeholder=""
                v-model="form1['sys_config.embedding_provider']['config_value_obj']['selected']['api_key']"
                autocomplete="off" />

            </el-form-item>




          </el-form>
        </div>
      </el-scrollbar>
    </div>

    <div class="dialog-footer">

      <el-button type="primary" @click="sub(ruleFormRef1)">
        确认提交
      </el-button>
      <el-button @click="close" plain>取消</el-button>
    </div>
  </el-drawer>
</template>
<style scoped>
.iconfont.icon-bangzhu{
  position: relative;
  top: 1px;
}
.dformbox {
  display: block;
  height: calc(100% - 70px);
  margin: 0 -20px;
}

.ftitle {
  display: block;
  font-size: 16px;
  color: #333;
  font-weight: bold;
  width: 100%;
  text-align: left;
  margin-bottom: 10px;
}
</style>