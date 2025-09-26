<script setup>
import { ref, reactive } from "vue";
import {
  tools,
  toolsdelete,
  toolsadd,
  set_disabled,
  gettools,
  mcp_provider,
  mcp_providerid,
  mcp_providercreate,
  mcp_providerdelete,
  mcp_providerreconnect,
  select_tools,
} from "@/api/api";

import { copyData } from "@/assets/utils/util";
import { isValidVariableName,isValidateName } from "@/assets/utils/validator.js";
import { useStore } from "vuex";
import { useRoute, useRouter } from "vue-router";
import icon from "@/components/icon.vue";
import { cloneDeep } from "lodash"; // 引入lodash库的cloneDeep方法进行深拷贝
import { goback, getTime } from "@/components/comp.js";
const route = useRoute();
const router = useRouter();
const store = useStore();

let searchParams = reactive({
  page: 1,
  pagesize: 30,
  keyword: '',
  active: '1',
});
const total = ref(0);

copyData(searchParams, route.query);

let pagelist = ref([]);

const search = async (type) => {
  if (type == "init") {
    searchParams.page = 1;
  }
  let res = null;
  let params = cloneDeep(searchParams);
  delete params.active;
  if (searchParams.active == '1') {
    res = await tools(params);
  } else {
    res = await mcp_provider(params);
  }

  if (res) {
    let arr = res.rows || [];
    pagelist.value = arr;
    total.value = res.total_records;
  }

  if (type != "noquery") {
    let query = { ...route.query, ...searchParams };
    router.replace({ path: route.path, query: query });
  }
};

search("noquery");

const tableRef = ref(null);

const delfn = (item) => {
  _this.$confirm("确定要删除所选数据?").then((res) => {
    toolsdelete({ id: item.id }).then((res) => {
      _this.$message("删除成功");
      search();
    })
  });
};




const isShowCompDetail = ref(false);

const initializeForm = () => {
  return {
    id: undefined,  // 主键ID
    func_name: "",  // 函数名
    name: "",  // 插件名称
    tool: "",
    caption: "",  // 插件描述
    api_url: "",  // 工具路径
    // api_key: "https://",  // 工具路径
    api_method: "POST",  // 请求方法
    is_enable: false,  // 是否启用
    out_params: [],  // 输出参数
    in_params: [],  // 输入参数
  };
};


const form = ref(initializeForm());
const addfn = async (item) => {

  if (searchParams.active == '1') {


    if (item) {
      let res = await gettools({ id: item.id });
      if (!res) return false;
      form.value = res;
    } else {
      form.value = initializeForm()
    }

    isShowCompDetail.value = true;

    if (ruleFormRef.value) {
      ruleFormRef.value.clearValidate()
    }
  } else if (searchParams.active == '2') {
    // 添加MCP
    if (item) {
      MCPform.value.id = item.id;
      MCPform.value.name = item.name;
      MCPform.value.headers = item.headers ? JSON.stringify(item.headers) : undefined;
      MCPform.value.server_url = item.server_url;
      MCPform.value.server_identifier = item.server_identifier;
    } else {
      MCPform.value = {
        name: '',
        headers: '',
        server_url: '',
        server_identifier: '',
      }
    }

    isShowMCPDetail.value = true;

    if (MCPformRef.value) {
      MCPformRef.value.clearValidate()
    }
  }
};
const MCPformRef = ref(null);

const ruleFormRef = ref(null);
const sub = (formEl) => {
  if (!formEl) return
  formEl.validate((valid) => {
    if (valid) {
      toolsadd(form.value).then((res) => {
        _this.$message("保存成功");
        search();
        isShowCompDetail.value = false;
      });
    }
  })
};


const MCPDetailname = ref('');
const isShowMCPDetail1 = ref(false);

const addInput = (type, data) => {
  const baseData = {
    id: Date.now(),
    name: "",
    data_type: "String",
  };

  const adddata = type === "out_params"
    ? { ...baseData, caption: "" }
    : { ...baseData, param_way: "Body", caption: "", is_required: true, default_value: "" };

  if (data) {
    if (!data.children) {
      data.children = [];
    }
    adddata.param_way = "";
    data.children.push(adddata);
    form.value[`${type}`] = [...form.value[`${type}`]];
  } else {
    form.value[`${type}`].push(adddata);
  }
};

const changeStatus = (item) => {
  set_disabled({ id: item.id }).then((res) => {
    _this.$message("修改成功");
    search();
  });
};


function isrepeat(name, arr) {
  let flag = 0;
  arr.forEach((item) => {
    if ((item.data && item.data.name == name) || item.name == name) {
      flag += 1;
    }
  });
  return flag > 1;
}

const isValidVariableNamefn = (item, list, type) => {
  if (!isValidVariableName(item.name)) {
    item.errtip = "参数名只能包含字母、数字和下划线，且不能以数字开头";
  } else if (isrepeat(item.name, list.parent ? list.parent.childNodes : list)) {
    item.errtip = "参数名不能重复";
  } else {
    item.errtip = "";
  }
  form.value.in_params = [...form.value.in_params];
  form.value.out_params = [...form.value.out_params];
};

const isValidVariableNamefn1 = (item, list, type) => {
  if (!item[type]) {
    item.errtip = "参数不能为空";
  } else {
    item.errtip = "";
  }
  form.value.in_params = [...form.value.in_params];
  form.value.out_params = [...form.value.out_params];
};

const isDisabled = (node, val) => {
  return node.level > 3 && (val == "Object" || val == "Array<Object>");
};

const remove = (node, data, type) => {
  const parent = node.parent;
  const children = parent.data.children || parent.data;
  const index = children.findIndex((d) => d.id === data.id);
  children.splice(index, 1);
  form.value.in_params = [...form.value.in_params];
  form.value.out_params = [...form.value.out_params];
};


const MCPform = ref({
  name: '',
  server_url: '',
  server_identifier: '',
  headers: ''
});
const isShowMCPDetail = ref(false);
const del2fn = (item) => {
  _this.$confirm("确定要删除所选数据?").then((res) => {
    mcp_providerdelete({ id: item.id }).then((res) => {
      _this.$message("删除成功");
      search();
    })
  });
};

const add2fn = (formEl) => {
  if (!formEl) return
  formEl.validate((valid) => {
    if (valid) {
      if (MCPform.value.headers) {
        try {
          let json = JSON.parse(MCPform.value.headers);
        } catch (e) {
          _this.$message("请输入正确的json格式");
          return;
        }
      }
      let params = cloneDeep(MCPform.value);
      params.headers = MCPform.value.headers ? JSON.parse(MCPform.value.headers) : undefined;

      mcp_providercreate(params).then((res) => {
        _this.$message("保存成功");
        search();
        isShowMCPDetail.value = false;
      });
    }
  })
};
const curDetail = ref(null);
const show2fn = (item) => {
  MCPDetailname.value = item.name;
  mcp_providerid({ id: item.id }).then((res) => {
    if (res) {
      curDetail.value = res;
      isShowMCPDetail1.value = true;
    }
  });

}
const handleClick = (tab, event) => {
  pagelist.value = []
  total.value = 0;
  search("init");
};


const validatePass = (rule, value, callback) => {
  if (value === "") {
    callback(new Error("唯一标识名称不能为空"));
  }
  else if (!isValidVariableName(value)) {
    callback(new Error("唯一标识名称只能包含字母、数字和下划线，且不能以数字开头"));
  } else {
    callback();
  }
};

const validateName = (rule, value, callback) => {
  if (value === "") {
    callback(new Error("函数名称不能为空"));
  }
  else if (!isValidateName(value)) {
    callback(new Error("函数名称只能包含小写字母和下划线"));
  } else {
    callback();
  }
};

const checkItem = (item) => {
  let curindex = -1;
  curDetail.value.selected_tools.forEach((citem, cindex) => {
    if (citem == item.name) {
      curindex = cindex;
    }
  })
  if (curindex === -1) {
    // 没找到 添加
    curDetail.value.selected_tools.push(item.name);
  } else {
    // 找到了 删除
    curDetail.value.selected_tools.splice(curindex, 1);
  }
}

const isChecked = (item) => {
  let curindex = -1;
  if (curDetail.value.selected_tools && curDetail.value.selected_tools.length > 0) {


    curDetail.value.selected_tools.forEach((citem, cindex) => {
      if (citem == item.name) {
        curindex = cindex;
      }
    })
    return curindex !== -1;
  }
  return false;

}


const select_toolsfn = () => {
  select_tools({ selected_tools: [...curDetail.value.selected_tools], id: curDetail.value.id }).then((res) => {
    _this.$message("保存成功");
    isShowMCPDetail1.value = false;
    search();
  })
}

const mcp_providerreconnectfn = () => {
  mcp_providerreconnect({ id: curDetail.value.id }).then((res) => {
    show2fn(curDetail.value)
  })
}

</script>

<template>
  <div class="pagelistbox">
    <div class="c-titlebox">
      <div class="title">工具插件</div>
      <div class="btns"><el-button type="primary" size="small" @click="addfn()">新增</el-button></div>
    </div>
    <div style="margin-bottom: 0;" class="tabbox">
      <el-tabs v-model="searchParams.active" @tab-change="handleClick" class="demo-tabs">
        <el-tab-pane name="1">
          <template #label> API插件 </template>
        </el-tab-pane>
        <el-tab-pane name="2">
          <template #label> MCP插件 </template>
        </el-tab-pane>

      </el-tabs>
    </div>

    <div class="c-tablebox tableboxContain c-tooltip">
      <div class="bodybox">

        <el-table v-if="searchParams.active == 1" tooltip-effect="light" border :data="pagelist"
          :max-height="store.getters.innerHeight - 186" style="width: 100%">
          <el-table-column prop="id" width="70" label="工具id" />

          <el-table-column label="函数名称">
            <template #default="scope">
              <div class="c-scroll-contain">
                {{ scope.row.func_name }}
              </div>
            </template>
          </el-table-column>

          <el-table-column label="工具名称">
            <template #default="scope">
              <div class="c-scroll-contain">
                {{ scope.row.name }}
              </div>
            </template>
          </el-table-column>
          <el-table-column label="工具描述">
            <template #default="scope">
              <div class="c-scroll-contain">
                {{ scope.row.caption }}
              </div>
            </template>
          </el-table-column>

          <el-table-column width="120" align="center" label="工具状态">
            <template #default="scope">
              <el-switch v-model="scope.row.is_enable" inline-prompt @change="() => {
                changeStatus(scope.row)
              }" style="--el-switch-on-color: #13ce66; --el-switch-off-color: #ccc" active-text="启用"
                inactive-text="禁用" />
            </template>
          </el-table-column>

          <el-table-column width="200" align="center" label="操作">
            <template #default="scope">
              <div @click="addfn(scope.row)" class="c-table-ibtn">
                <span class="iconfont icon-xiugai"></span>
                修改
              </div>
              <div @click="delfn(scope.row)" class="c-table-ibtn c-btn-del">
                <span class="iconfont icon-shuzhuang-shanchu"></span>
                删除
              </div>

            </template>
          </el-table-column>
          <template #empty="scope">
            <div class="c-emptybox">
              <icon type="empzwssjg" width="100" height="100"></icon>暂无数据~~
            </div>
          </template>
        </el-table>
        <div style="height: auto;">
          <el-scrollbar v-if="searchParams.active == 2" ref="tableRef" :max-height="store.getters.innerHeight - 186">
            <div class="c-cardbox">
              <div v-for="ritem in pagelist" @click.stop="show2fn(ritem)" class="item">
                <el-popover :width="160">
                  <template #reference>
                    <span class="iconfont icon-gengduo c-cardbtn-icon"></span>
                  </template>
                  <template #default>
                    <div class="c-cardbtn-btns">

                      <div @click.stop="show2fn(ritem)" class="item">
                        <span class="name">查看</span>
                      </div>
                      <div @click.stop="addfn(ritem)" class="item">
                        <span class="name">修改</span>
                      </div>
                      <div @click.stop="del2fn(ritem)" class="item">
                        <span class="name">删除</span>
                      </div>
                    </div>
                  </template>
                </el-popover>
                <div class="top ellipsis">
                  # {{ ritem.id }}
                </div>
                <div class="title ellipsis">
                  {{ ritem.name }}
                </div>
                <div class="intro">
                  <div :title="ritem.server_url" class="server_identifier ellipsis">{{ ritem.server_url }}</div>
                  <div class="numbox"></div>
                  <div v-if="ritem.tools" class="time">
                    共{{ ritem.tools.length }}个工具，已选{{ ritem.selected_tools.length }}个工具集成到系统
                  </div>
                </div>
              </div>
            </div>
          </el-scrollbar>
        </div>

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
                tableRef && tableRef.scollTo(0, 0)
                search();
              }
            " :page-sizes="[30, 50, 100, 900]" layout="total,sizes,jumper,prev, pager, next" :total="total" />
        </div>



      </div>
    </div>
  </div>

  <el-drawer v-model="isShowMCPDetail1" @closed="isShowMCPDetail1 = false" title="选择工具" size="800" direction="rtl">
    <div v-if="curDetail" style="position: relative;" class="dformbox">
      <div class="formtopbox">
        <div class="namebox">
          <div class="titlename ellipsis">{{ MCPDetailname }}</div>
          <div class="url ellipsis">{{ curDetail.server_url }}</div>

          <div class="numbox ellipsis">共{{ curDetail.tools.length }}个工具，已选{{ curDetail.selected_tools.length }}个工具集成到系统
          </div>
        </div>
        <el-button @click="mcp_providerreconnectfn()" size="small" type="primary">刷新工具</el-button>
      </div>
      <div class="mcpcardbox utilbox">
        <el-scrollbar>
          <div style="margin: 0 20px;">
            <div v-for="item in curDetail.tools" class="item" @click="checkItem(item)" :class="{ on: isChecked(item) }">
              <el-popover :show-after="300" placement="right"
                :popper-style="{ width: 'auto', padding: '10px', minWidth: '80px', maxWidth: '500px' }" trigger="hover">
                <template #reference>
                  <div>
                  <div class="name">{{ item.name }}</div>
                  <div class="desc">{{ item.description }}</div>
                  <span v-if="isChecked(item)" class="iconfont icon-xuanzhong"></span>
                </div>
                </template>
                <div style="margin: 0 -10px;" class="jsonbox">
                  <el-scrollbar :max-height="600">
                  <json-viewer :show-array-index="true" sort :expand-depth="4" :value="item.inputSchema"></json-viewer>
                </el-scrollbar>
                </div>
              </el-popover>
            </div>
          </div>
        </el-scrollbar>
      </div>
    </div>
    <div class="dialog-footer">

      <el-button type="primary" @click="select_toolsfn()">
        重新保存选择结果
      </el-button>

      <el-button plain @click="isShowMCPDetail1 = false">
        取消
      </el-button>
    </div>

  </el-drawer>



  <el-drawer v-model="isShowMCPDetail" @closed="isShowMCPDetail = false" :title="MCPform.id ? '修改MCP' : '新增MCP'"
    size="800" direction="rtl">
    <div class="dformbox">
      <el-scrollbar>
        <el-form class="mg20" @submit.native.prevent ref="MCPformRef" label-position="top" inline :model="MCPform">
          <el-form-item label="名称" style="width:100%;margin-right: 0;" :rules="[
            {
              required: true,
              message: '请输入名称',
              trigger: 'blur',
            },
          ]" prop="name">
            <el-input v-model="MCPform.name" autocomplete="off" />
          </el-form-item>
          <el-form-item label="服务器URL" style="width:100%;margin-right: 0;" :rules="[
            {
              required: true,
              message: '请输入服务器URL',
              trigger: 'blur',
            },
          ]" prop="server_url">
            <el-input v-model="MCPform.server_url" autocomplete="off" />
          </el-form-item>

          <el-form-item label="唯一标识名称" :rules="[
            {
              required: true,
              trigger: 'blur',
              validator: validatePass,
            },
          ]" style="width:100%;margin-right: 0;" prop="server_identifier">
            <template #label>
              唯一标识名称
              <el-tooltip popper-class="c-flowtip" class="item" effect="dark" content="只能包含字母数字下划线，且数字不可以作为开"
                placement="top">
                <span style="position: relative;top: 1px;" class="iconfont icon-bangzhu"></span>
              </el-tooltip>
            </template>
            <el-input v-model="MCPform.server_identifier" autocomplete="off" />
          </el-form-item>

          <el-form-item label="请求头" style="width:100%;margin-right: 0;" :rules="[
            {
              message: '请输入请求头',
              trigger: 'blur',
            },
          ]" prop="headers">
            <template #label>
              请求头
              <el-tooltip popper-class="c-flowtip" class="item" effect="dark"
                content='{ "Authorization": "按照MCP提供商要求填写"}' placement="top">
                <span style="position: relative;top: 1px;" class="iconfont icon-bangzhu"></span>
              </el-tooltip>
            </template>
            <el-input v-model="MCPform.headers" type="textarea" :autosize="{ minRows: 4, maxRows: 12 }"
              autocomplete="off" />
          </el-form-item>


        </el-form>
      </el-scrollbar>
    </div>
    <div class="dialog-footer">

      <el-button type="primary" @click="add2fn(MCPformRef)">
        保存并链接服务
      </el-button>

      <el-button plain @click="isShowMCPDetail = false">
        取消
      </el-button>
    </div>

  </el-drawer>

  <el-drawer v-model="isShowCompDetail" @closed="isShowCompDetail = false" :title="form.id ? '修改工具' : '新增工具'"
    size="1400" direction="rtl">
    <div class="dformbox">
      <el-scrollbar>
        <el-form class="mg20" @submit.native.prevent ref="ruleFormRef" label-position="top" inline :model="form">
          <el-form-item label="" style="width:calc(50% - 8px);" :rules="[
            {
              required: true,
              trigger: 'blur',
              validator: validateName,
            },
          ]" prop="func_name">
          <template #label>
            函数名称
              <el-tooltip popper-class="c-flowtip" class="item" effect="dark"
                content='为该插件起一个名称，方便大模型调用时使用，请使用小写字母' placement="top">
                <span style="position: relative;top: 1px;" class="iconfont icon-bangzhu"></span>
              </el-tooltip>
            </template>
            <el-input v-model="form.func_name" autocomplete="off" />
          </el-form-item>
          <el-form-item label="" style="width:calc(50% - 8px);margin-right:0" :rules="[
            {
              required: true,
              message: '请输入工具名称',
              trigger: 'blur',
            },
          ]" prop="name">
          <template #label>
            工具名称
              <el-tooltip popper-class="c-flowtip" class="item" effect="dark"
                content='给您自己看的名称，可以自行描述' placement="top">
                <span style="position: relative;top: 1px;" class="iconfont icon-bangzhu"></span>
              </el-tooltip>
            </template>
            <el-input v-model="form.name" autocomplete="off" />
          </el-form-item>


          <el-form-item label="" style="width:100%;margin-right:0" :rules="[
            {
              required: true,
              message: '请输入工具描述',
              trigger: 'blur',
            },
          ]" prop="caption">
          <template #label>
            工具描述
              <el-tooltip popper-class="c-flowtip" class="item" effect="dark"
                content='给大模型看的描述信息，需要认真填写，方便大模型准确使用' placement="top">
                <span style="position: relative;top: 1px;" class="iconfont icon-bangzhu"></span>
              </el-tooltip>
            </template>
            <el-input v-model="form.caption" autocomplete="off" />
          </el-form-item>
          <br>

          <el-form-item label="" style="width:calc(50% - 16px);" :rules="[
            {
              required: true,
              message: '请输入工具路径',
              trigger: 'blur',
            },
          ]" prop="api_url">
          <template #label>
            工具路径URL
              <el-tooltip popper-class="c-flowtip" class="item" effect="dark"
                content='工具路径就是你需要调用的外部 API的 URL' placement="top">
                <span style="position: relative;top: 1px;" class="iconfont icon-bangzhu"></span>
              </el-tooltip>
            </template>
            <el-input v-model="form.api_url" placeholder=" " class="input-with-select">


            </el-input>
          </el-form-item>

          <el-form-item label="" style="width:calc(25% - 8px);margin-right: 16px;" :rules="[
            {
              required: true,
              message: '请输入请求方法',
              trigger: 'change',
            },
          ]" prop="api_method">
          <template #label>
            请求方法
              <el-tooltip popper-class="c-flowtip" class="item" effect="dark"
                content='按照实际情况根据远程api的要求设置' placement="top">
                <span style="position: relative;top: 1px;" class="iconfont icon-bangzhu"></span>
              </el-tooltip>
            </template>
            <el-select v-model="form.api_method" placeholder=" ">
              <el-option label="POST" value="POST" />
              <el-option label="GET" value="GET" />
            </el-select>
          </el-form-item>

          <el-form-item class="c-switchbox-label" label="工具状态" style="width:calc(25% - 8px);margin-right:0;"
            prop="is_enable">
            <div class="c-switchbox">
              <div class="label"></div>
              <div class="switch">
                <el-switch v-model="form.is_enable" inline-prompt active-text="启用工具" inactive-text="禁用工具" />
              </div>
            </div>
          </el-form-item>

          <div class="c-title-l2">
            <icon width="32" height="32" type="shuru"></icon>
            输入参数
          </div>

          <div class="c-tree-tablebox">
            <div class="header">
              <div class="citem" style="width: calc(50% - 420px);">参数名称
                <el-tooltip popper-class="c-flowtip" class="item" effect="dark"
                content='根据远程api设置' placement="top">
                <span style="position: relative;top: 0px;" class="iconfont icon-bangzhu"></span>
              </el-tooltip>
              </div>
              <div class="citem" style="width: calc(50% - 420px);">参数描述
                <el-tooltip popper-class="c-flowtip" class="item" effect="dark"
                content='参数描述性信息，方便大模型使用' placement="top">
                <span style="position: relative;top: 0px;" class="iconfont icon-bangzhu"></span>
              </el-tooltip>
              </div>
              <div class="citem" style="width: 200px;">参数类型
                <el-tooltip popper-class="c-flowtip" class="item" effect="dark"
                content='根据远程api设置' placement="top">
                <span style="position: relative;top: 0px;" class="iconfont icon-bangzhu"></span>
              </el-tooltip>
              </div>
              <div class="citem" style="width: 200px;">传入方法
                <el-tooltip popper-class="c-flowtip" class="item" effect="dark"
                content='根据远程api设置' placement="top">
                <span style="position: relative;top: 0px;" class="iconfont icon-bangzhu"></span>
              </el-tooltip>
              </div>
              <div class="citem center" style="width: 120px;">是否必须
                <el-tooltip popper-class="c-flowtip" class="item" effect="dark"
                content='根据远程api设置' placement="top">
                <span style="position: relative;top: 0px;" class="iconfont icon-bangzhu"></span>
              </el-tooltip>
              </div>
              <div class="citem" style="width: 200px;">默认值
                <el-tooltip popper-class="c-flowtip" class="item" effect="dark"
                raw-content
                content='在此处可填写API要求输入的参数，这些参数将作为默认值，例如API密钥、APIToken等信息。<br /> 若填写此项，模型将不会看到和填写该参数。' placement="top">
                <span style="position: relative;top: 0px;" class="iconfont icon-bangzhu"></span>
              </el-tooltip>
              </div>
              <div class="citem end" style="width: 120px;">操作</div>
            </div>
            <el-tree style="width: 100%" :data="form.in_params" node-key="id" default-expand-all empty-text="暂无数据"
              :expand-on-click-node="false">
              <template #default="{ node, data }">
                <div class="items">
                  <div class="citem pd0" :class="{ 'c-errorinp': data.errtip && !data.name }"
                    :style="'width: calc(50% - 420px);margin-right:-' + 10 * (node.level - 1) + 'px'">
                    <el-input @blur="isValidVariableNamefn(data, node)" placeholder="输入参数名" v-model="data.name"
                      :style="'width:calc(' + ('100%  - ' + (10 * (node.level - 1))) + 'px'"></el-input>
                  </div>
                  <div :style="'width: calc(50% - ' + (420 - (10 * (node.level - 1))) + 'px);'" class="citem"
                    :class="{ 'c-errorinp': data.errtip && !data.caption }">
                    <el-input @blur="isValidVariableNamefn1(data, node, 'caption')" @click.stop.prevent @mousedown.stop
                      v-model="data.caption" placeholder="请描述变量的用途"></el-input>
                  </div>
                  <div style="width: 200px;" class="citem">
                    <el-select v-model="data.data_type" :disabled="data.disabled" placeholder="选择类型">
                      <el-option v-for="(val, key) in store.getters.keyTypes" :value="key" :label="val"
                        :disabled="isDisabled(node, val)"></el-option>
                    </el-select>
                  </div>

                  <div style="width: 200px;" class="citem">
                    <el-select v-model="data.param_way" :disabled="node.level > 1" placeholder="传入方法">
                      <el-option label="Body" value="Body" />
                      <el-option label="Path" value="Path" />
                      <el-option label="Query" value="Query" />
                      <el-option label="Header" value="Header" />
                    </el-select>
                  </div>

                  <div style="width: 120px;" class="citem center">
                    <el-switch v-model="data.is_required" inline-prompt active-text="是" inactive-text="否" />
                  </div>
                  <div style="width: 200px;" class="citem">
                    <el-input @click.stop.prevent @mousedown.stop v-model="data.default_value"
                      placeholder="请输入默认值"></el-input>
                  </div>
                  <div style="width: 120px;" class="citem end">
                    <span title="新增子项" style="margin-right: 12px;" v-show="node.level < 4 &&
                      (data.data_type == 'Object' ||
                        data.data_type == 'Array<Object>')
                      " @click="addInput('in_params', data)" class="iconfont icon-liebiao-zengjia"></span>

                    <span title="删除当前项" v-if="!data.disabled" @click="remove(node, data, 'in_params')"
                      class="iconfont icon-liebiao-shanchu"></span>
                  </div>

                  <div v-if="data.errtip" style="width: 100%" class="errtip">
                    {{ data.errtip }}
                  </div>
                </div>
              </template>
            </el-tree>


            <div class="footer">
              <div @click="addInput('in_params')" class="btns">
                <span class="iconfont icon-xinzengcanshu"></span> 新增参数
              </div>
            </div>
          </div>



          <div class="c-title-l2">
            <icon width="32" height="32" type="shuchu"></icon>
            输出参数
          </div>


          <div class="c-tree-tablebox">
            <div class="header">
              <div class="citem" style="width: calc(50% - 160px);">参数名称
                <el-tooltip popper-class="c-flowtip" class="item" effect="dark"
                content='根据远程api设置' placement="top">
                <span style="position: relative;top: 0px;" class="iconfont icon-bangzhu"></span>
              </el-tooltip>
              </div>
              <div class="citem" style="width: calc(50% - 160px);">参数描述
                <el-tooltip popper-class="c-flowtip" class="item" effect="dark"
                content='参数描述性信息，方便大模型使用' placement="top">
                <span style="position: relative;top: 0px;" class="iconfont icon-bangzhu"></span>
              </el-tooltip>
              </div>
              <div class="citem" style="width: 200px;">参数类型
                <el-tooltip popper-class="c-flowtip" class="item" effect="dark"
                content='根据远程api设置' placement="top">
                <span style="position: relative;top: 0px;" class="iconfont icon-bangzhu"></span>
              </el-tooltip>
              </div>
              <div class="citem end" style="width: 120px;">操作</div>
            </div>
            <el-tree style="width: 100%" :data="form.out_params" node-key="id" default-expand-all empty-text="暂无数据"
              :expand-on-click-node="false">
              <template #default="{ node, data }">
                <div class="items">
                  <div class="citem pd0" :class="{ 'c-errorinp': data.errtip && !data.name }"
                    :style="'width: calc(50% - 160px);margin-right:-' + 10 * (node.level - 1) + 'px'">
                    <el-input @blur="isValidVariableNamefn(data, node)" placeholder="输入参数名" v-model="data.name"
                      :style="'width:calc(' + ('100%  - ' + (10 * (node.level - 1))) + 'px'"></el-input>
                  </div>
                  <div :style="'width: calc(50% - ' + (160 - (10 * (node.level - 1))) + 'px);'" class="citem"
                    :class="{ 'c-errorinp': data.errtip && !data.caption }">
                    <el-input @blur="isValidVariableNamefn1(data, node, 'caption')" @click.stop.prevent @mousedown.stop
                      v-model="data.caption" placeholder="请描述变量的用途"></el-input>
                  </div>
                  <div style="width: 200px;" class="citem">
                    <el-select v-model="data.data_type" :disabled="data.disabled" placeholder="选择类型">
                      <el-option v-for="(val, key) in store.getters.keyTypes" :value="key" :label="val"
                        :disabled="isDisabled(node, val)"></el-option>
                    </el-select>
                  </div>

                  <div style="width: 120px;" class="citem end">
                    <span title="新增子项" style="margin-right: 12px;" v-show="node.level < 4 &&
                      (data.data_type == 'Object' ||
                        data.data_type == 'Array<Object>')
                      " @click="addInput('out_params', data)" class="iconfont icon-liebiao-zengjia"></span>

                    <span title="删除当前项" v-if="!data.disabled" @click="remove(node, data, 'out_params')"
                      class="iconfont icon-liebiao-shanchu"></span>
                  </div>

                  <div v-if="data.errtip" style="width: 100%" class="errtip">
                    {{ data.errtip }}
                  </div>
                </div>
              </template>
            </el-tree>


            <div class="footer">
              <div @click="addInput('out_params')" class="btns">
                <span class="iconfont icon-xinzengcanshu"></span> 新增参数
              </div>
            </div>
          </div>


        </el-form>
      </el-scrollbar>
    </div>
    <div class="dialog-footer">

      <el-button type="primary" @click="sub(ruleFormRef)">
        保存
      </el-button>

      <el-button plain @click="isShowCompDetail = false">
        取消
      </el-button>
    </div>

  </el-drawer>
</template>
<style scoped>
.utilbox {
  text-align: left;
  height: calc(100% - 114px);
  margin: 10px 0px;
}

.utilbox .item {
  display: inline-block;
  text-align: left;
  border: 1px solid var(--el-border-color);
  border-radius: 5px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s;
  margin: 0 0 12px 0;
  width: 100%;
  box-sizing: border-box;
  position: relative;
}

.utilbox .item .iconfont.icon-xuanzhong {
  position: absolute;
  right: 10px;
  top: 10px;
  color: #16b13e;
  font-size: 18px;
}

.utilbox .item .name {
  font-weight: bold;
  font-size: 16px;
}

.utilbox .item .desc {
  font-size: 12px;
  color: #999;
}

.utilbox .item.on,
.utilbox .item:hover {
  border-color: var(--el-color-primary);

  background: var(--c-bg-linear);

}

.formtopbox {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin: 0 20px 10px 20px;
  border: 1px solid var(--el-border-color);
  border-radius: 5px;
  padding: 16px;
}

.formtopbox .namebox {
  width: calc(100% - 110px);
}

.formtopbox .titlename {
  font-weight: bold;
  font-size: 16px;
}

.formtopbox .url {
  font-size: 12px;
  color: #999;
  margin: 5px 0;
}

.c-cardbox .time {
  color: #999;
}

.c-cardbox .item {
  cursor: pointer;
}

.c-cardbox .server_identifier {
  font-weight: bold;
}

.c-cardbox .numbox {
  margin: 5px 0;
}

.icon-liebiao-shanchu {
  color: var(--el-color-danger);
}

.btnbox {
  padding: 10px 20px;
  text-align: left;
}

.outputbox .item {
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  flex-wrap: wrap;
  text-align: left;
}

.outputbox .item .citem {
  width: 120px;
  padding: 10px;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.outputbox .item.title .citem {
  justify-content: center;
  font-weight: bold;
}

.outputbox .item .citem.pd0 {
  padding: 10px 0px;

}

.outputbox .item .citem.w20 {
  width: 200px;
}

.outputbox .item .citem.center {
  justify-content: center;
}

.outputbox .item .citem.end {
  justify-content: flex-end;
}

.errtip {
  display: inline-block;
  text-align: left;
  color: var(--el-color-danger);
  padding: 0 0 5px 0px;
  font-size: 12px;
  font-weight: normal;
}

.itembox .item.title,
.outputbox .item.title {
  color: #aaa;
  font-size: 12px;
  background: #fcfcfc;
  text-align: center;
  padding-left: 24px;
}

.ltitlebox {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 10px;
}

.ltitlebox .ltitle {
  font-weight: bold;
  text-align: left;
  font-size: 12px;
}

.dialog-footer {
  text-align: center;
  padding-top: 10px;
}

.dtitle {
  padding: 0 0 30px 0px;
}

.dtitle .iconfont,
.dtitle {
  font-weight: bold;
  text-align: left;
  font-size: 26px;

}

.dtitle .iconfont {
  cursor: pointer;
}

.dformbox {
  display: block;
  height: calc(100% - 60px);
  text-align: left;
  margin: 0 -20px;
}

.dformbox .mg20 {
  margin: 0 20px;
}

.flex {
  display: flex;
  align-items: center;
}


.nav {
  display: block;
  position: relative;
  box-sizing: border-box;
  height: 100%;
  width: 300px;
  flex-shrink: 0;
  border-right: 2px solid var(--chakra-colors-gray-100);
}








.icon-moban {
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
  height: calc(100% - 0px);
  box-sizing: border-box;
}

.tableboxContain .btnbox {
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
}

.tableboxContain .bodybox {
  height: 100%;
}

.pagelistbox {
  display: block;
  padding: 0;
  width: 100%;
  box-sizing: border-box;
  height: 100%;
}
</style>
