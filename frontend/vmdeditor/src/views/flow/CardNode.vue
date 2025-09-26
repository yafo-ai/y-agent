<script setup>
import { Handle, Position, useVueFlow, MarkerType } from "@vue-flow/core";
import { colors } from "./presets.js";
import { ref, watch, onMounted } from "vue";
import { useStore } from "vuex";
import { isValidVariableName, validateString } from "@/assets/utils/validator.js";
import { ArrowDown, ArrowUp, Minus, Plus } from "@element-plus/icons-vue";
import Editor from "@/components/editor.vue";
import icon from "@/components/icon.vue";

import useDragAndDrop from "./useDnD";
import { cloneDeep, uniq } from "lodash"; // 引入lodash库的cloneDeep方法进行深拷贝
const props = defineProps({
  id: {
    type: String,
    required: true,
  },
  data: {
    type: Object,
    required: true,
  },
  nodes: {
    type: Array,
    required: true,
  },
  edges: {
    type: Array,
    required: true,
  },
  llmlist: {
    type: Array,
    default: () => [],
  },
  splist: {
    type: Array,
    default: () => [],
  },
  textlist: {
    type: Array,
    default: () => [],
  },
  excellist: {
    type: Array,
    default: () => [],
  },
  funclist: {
    type: Array,
    default: () => [],
  },
  navlist: {
    type: Array,
    default: () => [],
  },
  space_vars: {
    type: Array,
    default: () => [],
  },
});
const store = useStore();
const emits = defineEmits([
  "delfn",
  "copyfn",
  "initfn",
  "checktypefn",
  "opendrawerfn",
  "opentscfn",
  "changespace_varsname",
  "node_run_debug",
]);

const clicknode = () => {
  store.commit("flowdata", { curnodeid: props.id });
};

const {
  // onEdgeClick,
  // onEdgeDoubleClick,
  // onEdgeContextMenu,
  // onEdgeMouseMove,
  // onEdgeUpdateStart,
  // onEdgeUpdate,
  // onEdgeUpdateEnd,
  // onEdgeMouseEnter,
  // onEdgeMouseLeave,
  findNode,
  onPaneReady,
  onNodeDragStop,
  onConnect,
  addEdges,
  addNodes,
  toObject,
  removeEdges,
} = useVueFlow();
// 连接两个节点
onConnect((params) => {
  const sourceNode = findNode(params.source);
  const targetNode = findNode(params.target);
  params.type = "button";
  params.animated = true;
  params.markerEnd = MarkerType.Arrow;
  // 只有同一组的才能连接

  if (sourceNode.parentNode === targetNode.parentNode) {
    addEdges([params]);
  }
});

const delfn = async (id) => {
  let cfm = await _this.$confirm("确定删除该节点？");
  if (!cfm) {
    return;
  }
  emits("delfn", id);
};
const copyfn = () => {
  emits("copyfn", props.id);
};
import { Delete } from "@element-plus/icons-vue";


const addOutput = (level, data) => {
  const adddata = {
    id: Date.now(),
    name: "",
    data_type: "String",
    desc: "",
    space_vars_id: "",
    prefix: level > 0 ? "" : "role",
    is_required: false,
  };
  if (data) {
    if (!data.children) {
      data.children = [];
    }
    data.children.push(adddata);

    props.data.outputs = [...props.data.outputs];
  } else {
    props.data.outputs.push(adddata);
  }
};

const addInput = (level, data) => {
  const adddata = {
    id: Date.now(),
    name: "",
    data_type: "String",
    desc: "",
    fileoption: [],
    is_required: false,
  };
  if (data) {
    if (!data.children) {
      data.children = [];
    }
    data.children.push(adddata);

    props.data.inputs = [...props.data.inputs];
  } else {
    props.data.inputs.push(adddata);
  }
};

const remove = (node, data, type) => {
  const parent = node.parent;
  const children = parent.data.children || parent.data;
  const index = children.findIndex((d) => d.id === data.id);
  children.splice(index, 1);
  if (type === "input") {
    props.data.inputs = [...props.data.inputs];
  } else {
    props.data.outputs = [...props.data.outputs];
  }
};



const isValidVariableNamefn = (item, list, type) => {
  if (!isValidVariableName(item.name)) {
    item.errtip = "变量名只能包含字母、数字和下划线，且不能以数字开头";
  } else if (isrepeat(item.name, list.parent ? list.parent.childNodes : list)) {
    item.errtip = "变量名不能重复";
  } else {
    item.errtip = "";
  }
  if (props.data.inputs) {
    props.data.inputs = [...props.data.inputs];
  }
  if (props.data.outputs) {
    props.data.outputs = [...props.data.outputs];
  }
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

onMounted(() => {
  init();
  rename.value = props.data.role;
});

const init = () => {
  // 初始化节点数据
  if (props.data.type === "llm") {
    // 如果是大模型节点数据  初始化 choice_role_prompt
    props.data.choice_role_prompt = props.data.choice_role_prompt || "";
    // 判断变量存储类型 如果是空间变量 但是没有id 的  把变量名称赋值给id

  } else if (props.data.type === "work_space") {
    // 工作空间变量  初始化id 
    props.data.space_vars.forEach((item, index) => {
      if (!item.id) {
        // 老数据没有id  就用name 代替id
        item.id = item.name;
      }
      item.data_type = item.data_type || "String";
    })
  }
};

const rename = ref(props.data.role);
const errtip = ref("");

const isHide1 = ref(false);
const isHide2 = ref(true);
const isHide3 = ref(true);
const ismetadata_filter = ref(true);
const isHide4 = ref(true);
const isHide5 = ref(true);
const isHide6 = ref(true);
const isHide7 = ref(true);
const isHidevarlist = ref(true);
const isHideIntro = ref(true);
const isHideName = ref(true);

const isDisabled = (node, val) => {
  return node.level > 3 && (val == "Object" || val == "Array<Object>");
};

const changefn = (data, val) => {
  if (val == "Object" || val == "Array<Object>") {
    // data.prefix = "";
  } else {
    data.children = [];
    // data.prefix = '2';
    props.data.outputs = [...props.data.outputs];
  }
};
const changeStartfn = (data, val) => {
  if (val == "Object" || val == "Array<Object>") {
    // data.prefix = "";
  } else if (val == "File" || val == "Array<File>") {
    // data.prefix = "";
    data.constraint = {
      max_file_kb: 1024 * 2,  //文件大小 kb 默认10M
      allowed_ext_types: [],  // 文件类型限制
      max_qty: 1,  // 最大数量
    }
  } else {
    data.children = [];
    data.constraint = undefined;
    // data.prefix = '2';
    props.data.inputs = [...props.data.inputs];
  }
};


const changespace_varsfn = (data, val) => {
  props.space_vars.forEach((item) => {
    if (item.id == val) {
      data.name = item.name;
      data.data_type = item.data_type;
    }
  });
};
const changeprefix = (data, val) => {
  // space 全局空间变量  role 角色自身
  if (val == 'space') {
    // 工作空间删除子节点
    data.children = []
  }
  data.name = "";
  data.data_type = "String";
  data.space_vars_id = "";
};



const switchchangefn = (val, type) => {
  if (val) {
    // 判断是否互斥  分身和ReAct推理 互斥 不能同时开启  ReAct推理 和 自动选择下游  互斥  不能同时开启。
    if (type == "auto_section_run" && props.data.react == true) {
      _this.$message("分身和ReAct推理互斥, 不能同时开启。", "error");
      props.data.auto_section_run = false;
      return false;
    }
    if (type == "react" && props.data.auto_section_run == true) {
      _this.$message("分身和ReAct推理互斥, 不能同时开启。", "error");
      props.data.react = false;
      return false;
    }
    if (type == "react" && props.data.auto_choice_node == true) {
      _this.$message("ReAct推理和自动选择下游互斥,不能同时开启。", "error");
      props.data.react = false;
      return false;
    }
    if (type == "auto_choice_node" && props.data.react == true) {
      _this.$message("ReAct推理和自动选择下游互斥,不能同时开启。", "error");
      props.data.auto_choice_node = false;
      return false;
    }
  }
};

const delConfirmFn = async (txt, fn) => {
  let cfm = await _this.$confirm(txt);
  if (cfm) {
    fn && fn();
  }
};

const flowtestform = ref({ inputs: undefined });

watch(
  () => flowtestform,
  (newVal, oldVal) => {
    // 这里可以执行你需要的操作
    initInput();
  },
  {
    deep: true, // 开启深度监听
  }
);
const initInput = () => {
  // 初始化输入参数

  if (
    props.data.type == "tool" &&
    (props.data.datatype == "flow" || props.data.datatype == "plugin" || props.data.datatype == "mcp") &&
    flowtestform.value.inputs
  ) {
    let inputs = {};
    flowtestform.value.inputs.forEach((item) => {
      inputs[item.name] = item.curvalue;
    });
    props.data.functions[0].options.inputs = JSON.stringify(inputs);
  }
};

const initFlowform = () => {
  if (props.data.type == "tool" && props.data.datatype == "flow") {
    // 工作流节点  设置flowtestform
    let cindex = -1;
    props.funclist.forEach((item, index) => {
      if (
        item.id == props.data.functions[0].options.workflow_id &&
        item.type == "flow"
      ) {
        cindex = index;
      }
    });
    if (cindex >= 0 && props.funclist[cindex].view_json) {
      // 配置数据
      let options = props.data.functions[0].options;

      let inputs = options && options.inputs ? JSON.parse(options.inputs) : {};
      let flow = JSON.parse(props.funclist[cindex].view_json);
      let nodes = flow.nodes;
      let testlist = [];
      nodes.forEach((item) => {
        if (item.data && item.data.type == "start") {
          testlist = cloneDeep(item.data.inputs) || [];
        }
      });

      testlist.forEach((item) => {
        if (inputs && inputs[item.name]) {
          item.curvalue = inputs[item.name];
        } else {
          item.curvalue = store.getters.keyTypesValue[item.data_type];
        }
      });
      flowtestform.value.inputs = cloneDeep(testlist) || [];
    } else {
      // 没找到 配置有错
      flowtestform.value.inputs = undefined;
    }
  } else if (props.data.type == "tool" && (props.data.datatype == "plugin" || props.data.datatype == "mcp")) {
    let funitem = props.data.dataItem;
    let arr = [];
    funitem.in_params.forEach((paramitem) => {
      arr.push(paramitem);
    });
    let testlist = cloneDeep(arr) || [];
    let inputs = props.data.functions[0].options.inputs
      ? JSON.parse(props.data.functions[0].options.inputs)
      : {};
    testlist.forEach((titem) => {
      if (inputs && inputs[titem.name]) {
        titem.curvalue = inputs[titem.name];
      } else {
        titem.curvalue = "";
      }
    });
    flowtestform.value.inputs = cloneDeep(testlist) || [];
  }
};
initFlowform();
const validatePass = (rule, value, callback) => {
  if (value === "") {
    callback(new Error("节点名称不能为空"));
  } else if (value.indexOf('sys') !== -1 || value.indexOf('role') !== -1) {
    callback(new Error("节点名称不能包含'sys'或'role'关键字"));
  } else if (validateString(value)) {
    callback(new Error("节点名称不能包含特殊符号"));
  } else {
    let flag = 0;
    props.nodes.forEach((item) => {
      if (item.data.role == value) {
        flag += 1;
      }
    });
    if (flag > 1) {
      callback(new Error("节点名称不能重复"));
    } else {
      emits("initfn");
      callback();
    }
  }
};
const formRef = ref(null);
const validatePass1 = (formEl) => {
  formEl.validateField("llm_id");
};

const isSelect = () => {
  let id = props.id;
  let arr = props.nodes;
  let cindex = -1;
  arr.forEach((item, index) => {
    if (item.id == id && item.selected) {
      cindex = index;
    }
  });
  return cindex !== -1;
};

const { initNode } = useDragAndDrop();
const curnode = findNode(props.id);

const visible = ref(false);
const curnodenum = ref(0);
const popover = ref(null);
const addNode = (event, item, index) => {
  if (item.type === "loop") {
    _this.$message("暂不支持嵌套循环节点", "error");
    return false;
  }
  // 添加节点

  let curnodedata = findNode(props.id);
  let width = curnodedata.dimensions.width
    ? parseInt(curnodedata.dimensions.width) + 50
    : 800;
  const newNode = initNode(
    cloneDeep(item),
    {
      x: curnodedata.position.x + width + curnodenum.value * 50,
      y: curnodedata.position.y + curnodenum.value * 50,
    },
    undefined,
    props.nodes
  );
  newNode.expandParent = true;
  newNode.parentNode = curnodedata.parentNode;
  newNode.data.pid = curnodedata.data.pid;
  curnodenum.value += 1;
  addNodes(newNode);
  addEdges([
    {
      source: curnodedata.id,
      sourceHandle: "source_1",
      target: newNode.id,
      targetHandle: "target_1",
      type: "button",
      animated: true,
      markerEnd: "arrow",
    },
  ]);
  visible.value = false;
  popover.value && popover.value.hide();
};
const isHideloop_traget = ref(true);

const choiceroleprompt = ref(null);
const outputvarprompt = ref(null);

const isDisabledspace_vars = (data, id) => {
  if (id === undefined) {
    // 没有传入id，都可以显示
    return false;
  }
  let cindex = -1;
  data.forEach((item, index) => {
    if (item.space_vars_id == id) {
      cindex = index;
    }
  })
  return cindex !== -1;
}
// 根据节点类型配置icon
const typeToicon = ref({
  'start': 'icon-kaishi1',
  'work_space': 'icon-gongzuokongjianbianliang',
  'llm': 'icon-damoxing',
  'temp_executor': 'icon-shuchu1',
  'loop': 'icon-pichuli',
  'flow': 'icon-gongzuoliugongju',
  'plugin': 'icon-gongzuochajian',
  'mcp': 'icon-MCP',
  'tool': 'icon-gongju1',
  'loop_start': 'icon-kaishi1',
})

const react_part_prompt = ref(null)
const isXyopen = ref(false);
const isBlopen = ref(false);
const isReopen = ref(false);

const clonenavlist = ref(cloneDeep(props.navlist));

const filterText = ref('')
watch(filterText, (val) => {
  filterNavlist(val)
})

const filterNavlist = (val) => {
  if (val) {
    clonenavlist.value = props.navlist.filter((item) =>
      item.role.toLowerCase().includes(val.toLowerCase())
    );
  } else {
    clonenavlist.value = cloneDeep(props.navlist);
  }
};

const getStartTypelist = () => {
  // let arr = cloneDeep(store.getters.keyTypes);
  // arr['File'] = "File"
  // arr['Array<File>'] = "Array<File>"
  return {
    'String': 'String',
    'Integer': 'Integer',
    'Number': 'Number',
    'Boolean': 'Boolean',
    'Object': 'Object',
    'File': 'File',
    'Array<String>': 'Array<String>',
    'Array<Integer>': 'Array<Integer>',
    'Array<Number>': 'Array<Number>',
    'Array<Boolean>': 'Array<Boolean>',
    'Array<Object>': 'Array<Object>',
    'Array<File>': 'Array<File>',
  };
}

// const showOpt = (node, data, type) => {
//   const parent = node.parent;
//   const children = parent.data.children || parent.data;
//   const index = children.findIndex((d) => d.id === data.id);
//   console.log(index, node, data);
//   // props.data.inputs = [...props.data.inputs];  根据index  修改

// };

const addTag = (data, type) => {
  if (!data.constraint.allowed_ext_types) data.constraint.allowed_ext_types = [];
  let typemap = {
    document: ['TXT', 'MD', 'MARKDOWN', 'PDF', 'HTML', 'XLSX', 'XLS', 'DOCX', 'CSV', 'EML', 'MSG', 'PPTX', 'PPT', 'XML', 'EPUB'],
    image: ['JPG', 'JPEG', 'PNG', 'GIF', 'WEBP', 'SVG'],
    video: ['MP4', 'MOV', 'MPEG', 'MPGA'],
    audio: ['MP3', 'M4A', 'WAV', 'WEBM', 'AMR'],
  }
  if (!typemap[type]) {
    typemap[type] = []
  }
  data.constraint.allowed_ext_types = data.constraint.allowed_ext_types.concat(typemap[type]);
  data.constraint.allowed_ext_types = uniq([...data.constraint.allowed_ext_types]);
}
const isHidevt_file = ref(true);
const vt_file = ref(null);


const curllm = ref({});
const changellm = (val) => {
  console.log(val)
  props.llmlist.forEach((item) => {
    if (item.id == val) {
      curllm.value = item;
      if (curllm.value.type != 'VLM') {
        // 如果不是视觉模型  清空选中状态
        props.data.use_vt = false;
        vt_file.value && vt_file.value.setValue('');
      }
    }
  })
}

if (props.data.llm_id && props.llmlist) {
  // 如果存在大模型 获取大模型
  changellm(props.data.llm_id)
}


</script>

<template>
  <div v-if="props.data.type == 'loop'" class="loopbg"></div>
  <div @click="clicknode()" class="cardbox c-flow-cardbox" :class="[
    {
      on: isSelect(),
      close: !props.data.isopen,
    },
    props.data.type,
  ]" :style="{
    width: props.data.width,
  }">
    <!-- 添加节点按钮 -->

    <div v-if="!props.data.isHideTitle" @click="props.data.isopen = !props.data.isopen" class="header">
      <div class="itembox">
        <div class="ltitle c-icons">
          <span :class="{ off: props.data.isopen }" class="iconfont icon-xiajiantou pointer"
            style="width: 10px; height: 20px; color: #333; padding: 0"></span>

          <span v-if="(typeToicon[props.data.type] || props.data.icon)"
            :class="'iconfont ' + (typeToicon[props.data.type == 'tool' ? props.data.datatype : props.data.type] || props.data.icon)"></span>
          <div style="line-height: 20px;padding-left: 5px;">
            <span>{{ props.data.role }}</span> <br>
            <span v-copy="props.data.id" class="nodeid c-color-aaa c-pointer">id:{{ props.data.id }}</span>
          </div>

        </div>
      </div>
      <div v-if="props.data.type != 'work_space' && props.data.type != 'start'" style="display: flex;
    align-items: center;
    justify-content: flex-end;" class="btns">
        <div class="node_run_debugbtn">


          <el-button @click.stop="emits('node_run_debug', {
            id: props.data.id,
          });" type="primary" plain size="small">运行一次<span style="margin:0"
              class="iconfont icon-liebiao-zhihang"></span></el-button>

          <span @click.stop="copyfn()" title="创建副本" class="iconfont icon-chakanxiangqing-fuzhidaima"></span>
          <span @click.stop="delfn(id)" title="删除节点" class="iconfont icon-liebiao-shanchu"></span>
        </div>

      </div>
    </div>

    <div v-if="props.data.type == 'loop_start' || props.data.type == 'loop_end'" class="body">
      <!-- 循环体 -->
      <div class="loopchild">
        <div class="ltitle c-icons">
          <span v-if="(typeToicon[props.data.type] || props.data.icon)"
            :class="'iconfont ' + (typeToicon[props.data.type == 'tool' ? props.data.datatype : props.data.type] || props.data.icon)"></span>
          <div style="line-height: 20px;padding-left: 5px;">
            <span>{{ props.data.type == "loop_start" ? "开始" : "结束" }}</span> <br>
            <span v-copy="props.data.id" class="nodeid c-color-aaa c-pointer">id:{{ props.data.id }}</span>
          </div>
        </div>
      </div>
    </div>
    <el-form style="width: 100%;" v-else ref="formRef" :data-id="props.id" :model="props.data" label-width="auto"
      label-position="top" inline class="demo-dynamic tl">
      <div class="body">
        <div style="margin-bottom: 0;" v-if="
          props.data.description !== undefined && props.data.type != 'start'
        " class="itembox">
          <div class="ltitle">
            <span :class="{ off: isHideName }" @click.stop="isHideName = !isHideName"
              class="iconfont icon-xiajiantou pointer"></span> <span class="iconfont icon-jiaosexinxi"></span> 角色信息
          </div>

          <el-form-item v-show="isHideName"
            :style="(props.data.type != 'tool' && !props.data.hidellm && props.data.type != 'start') ? 'width: calc(100% - 216px);margin-right: 16px;' : 'width: 100%;margin-right: 0px;'"
            prop="role" label="角色名称" :rules="{
              trigger: 'blur',
              required: true,
              validator: validatePass,
            }">
            <el-input size="small" style="width: 100%" maxlength="20" @click.stop.prevent @mousedown.stop
              v-model="props.data.role" />
          </el-form-item>
          <el-form-item v-show="isHideName" style="width: 200px;margin-right: 0;"
            v-if="props.data.type != 'tool' && !props.data.hidellm && props.data.type != 'start'" prop="llm_id"
            label="大模型" :rules="{
              required: true,
              message: '请选择大模型',
            }">
            <el-select @change="changellm" style="width: 200px" @blur="validatePass1(formRef)" size="small"
              v-model="props.data.llm_id" class="val" filterable placeholder="请选择大模型">
              <el-option v-for="item in llmlist" :value="parseInt(item.id, 10)" :label="item.name">
                <span style="float: left">{{ item.name }}</span>
                <span :style="{float: 'right',color:item.type=='LLM'?'rgb(100,161,255)':'rgb(152,139,255)'}">
                  {{ item.type }}
                </span>
              </el-option>
            </el-select>
          </el-form-item>
          <div v-if="errtip" style="padding-left: 28px;width: 100%;" class="errtip">
            {{ errtip }}
          </div>

          <el-form-item style="width: 100%;margin-right: 0;margin-bottom: 0;" v-show="isHideName" prop="description"
            label="角色介绍" :rules="{
              trigger: 'blur',
              required: true,
              message: '请输入介绍信息',
            }">
            <template #label>
              角色介绍<el-tooltip popper-class="c-flowtip" v-if="props.data.type != 'start'" class="item" effect="dark"
                content="用于上游节点，在自动选择下游角色时候的参考描述" placement="top">
                <span class="iconfont icon-bangzhu"></span>
              </el-tooltip>
            </template>
            <el-input @click.stop.prevent @mousedown.stop @wheel.stop type="textarea" resize="none" size="small"
              :rows="1" placeholder="请输入介绍信息" v-model="props.data.description" />
          </el-form-item>


        </div>

        <!-- 开始输入 -->

        <div v-if="props.data.type == 'start'" class="itembox">
          <div class="ltitle">
            <span :class="{ off: isHidevarlist }" @click.stop="isHidevarlist = !isHidevarlist"
              class="iconfont icon-xiajiantou pointer"></span> <span class="iconfont icon-shuru1"></span> 输入

            <span class="fr">
              <span class="addvarbtn" @click="addInput(0)">
                <span class="iconfont icon-liebiao-zengjia"></span>
                新增变量</span>
            </span>
          </div>

          <div v-show="isHidevarlist" class="outputbox inputbox curstartbox c-treebox">
            <div class="item title">
              <div class="key">变量名</div>
              <div class="type">变量类型</div>
              <div class="intro1">描述</div>
              <div class="opt">是否必须</div>
            </div>
            <el-tree style="width: 100%" :data="props.data.inputs" node-key="id" default-expand-all empty-text=""
              :expand-on-click-node="false">
              <template #default="{ node, data }">
                <div class="item custom-tree-node">
                  <div class="key" :style="'margin-right:-' + 18 * (node.level - 1) + 'px'">
                    <el-input @blur="isValidVariableNamefn(data, node)" @click.stop.prevent @mousedown.stop
                      :disabled="data.disabled" placeholder="输入变量名" size="small" v-model="data.name"
                      :style="'width:' + (170 - 18 * node.level) + 'px'"></el-input>
                  </div>
                  <div class="type">
                    <el-select size="small" v-model="data.data_type" :disabled="data.disabled" @change="
                      (val) => {
                        changeStartfn(data, val);
                      }
                    " placeholder="选择类型">
                      <el-option v-for="(val, key) in getStartTypelist()" :value="key" :label="val"
                        :disabled="isDisabled(node, val)"></el-option>

                    </el-select>
                  </div>

                  <div class="intro1">
                    <el-input size="small" @click.stop.prevent @mousedown.stop v-model="data.desc"
                      placeholder="请描述变量的用途"></el-input>
                  </div>
                  <div class="opt">
                    <div class="chkbox oitem">
                      <el-checkbox :disabled="data.disabled" v-model="data.is_required" label="" size="small" />
                    </div>
                    <div class="addchild oitem">
                      <span title="新增子项" v-show="node.level < 4 &&
                        (data.data_type == 'Object' ||
                          data.data_type == 'Array<Object>')
                        " @click="addInput(node.level, data)" class="iconfont icon-jiahao1"></span>
                      <el-popover
                        v-if="node.level <= 1 && (data.data_type == 'File' || data.data_type == 'Array<File>')"
                        placement="right" :width="600" trigger="click">
                        <template #reference>
                          <span title="配置文件类型" class="iconfont icon-moxingpeizhi-weixuanzhong-caidanicon"></span>

                        </template>
                        <div v-if="data.constraint" class="optfilebox c-form-alignleft">

                          <div class="labelbox">文件大小 <span class="c-tips">（单个文件最大值，单位KB）</span></div>
                          <el-input-number size="small" style="width: 100%;"
                            v-if="data.constraint && data.constraint.max_file_kb" @focus="$event.target.select()"
                            v-model="data.constraint.max_file_kb" placeholder="" :min="1" :precision="0" :step="1"
                            :controls="false" />


                          <div class="labelbox">文件数量 <span class="c-tips">（最多上传文件数量）</span></div>
                          <el-input-number size="small" style="width: 100%;"
                            v-if="data.constraint && data.constraint.max_qty" @focus="$event.target.select()"
                            v-model="data.constraint.max_qty" placeholder="" :disabled="data.data_type == 'File'"
                            :min="1" :precision="0" :step="1" :controls="false" />

                          <div class="labelbox">文件类型 <span class="c-tips">（回车添加自定义类型）</span></div>

                          <el-input-tag style="width: 100%;" clearable @add-tag="() => {
                            data.constraint.allowed_ext_types ? data.constraint.allowed_ext_types : data.constraint.allowed_ext_types = [];
                            data.constraint.allowed_ext_types = uniq([...data.constraint.allowed_ext_types]);
                          }" collapse-tags collapse-tags-tooltip :max-collapse-tags="3"
                            v-model="data.constraint.allowed_ext_types" placeholder="添加自定义文件类型" />

                          <div style="padding-top: 6px;" class="labelbox">快捷添加：
                            <el-button @click="addTag(data, 'image')" size="small" plain>图片</el-button>
                            <el-button @click="addTag(data, 'video')" size="small" plain>视频</el-button>
                            <el-button @click="addTag(data, 'audio')" size="small" plain>音频</el-button>
                            <el-button @click="addTag(data, 'document')" size="small" plain>文档</el-button>
                          </div>
                        </div>
                      </el-popover>
                    </div>
                    <div class="del oitem">
                      <span title="删除当前项" v-if="!data.disabled" @click="remove(node, data, 'input')"
                        class="iconfont icon-liebiao-shanchu"></span>
                    </div>
                  </div>

                  <div v-if="data.errtip" style="width: 100%" class="errtip">
                    {{ data.errtip }}
                  </div>
                </div>
              </template>
            </el-tree>
          </div>
        </div>

        <!-- 工作变量配置 -->
        <div v-if="props.data.space_vars !== undefined" class="itembox">
          <div class="ltitle">
            <span :class="{ off: isHidevarlist }" @click.stop="isHidevarlist = !isHidevarlist"
              class="iconfont icon-xiajiantou pointer"></span> <span class="iconfont icon-bianliangpeizhi"></span> 变量配置

            <span class="fr">


              <span class="addvarbtn" @click="
                props.data.space_vars.push({
                  id: Date.now(),
                  name: '',
                  type: 'over_write',
                  data_type: 'String',

                  errtip: '',
                })
              emits('changespace_varsname', {
                name: '',
                id: Date.now(),
                space_vars: props.data.space_vars,
                eventtype: 'add',
              });
              ">
                <span class="iconfont icon-liebiao-zengjia"></span>
                新增变量</span>
            </span>
          </div>
          <div v-show="isHidevarlist" class="itemcontain">
            <div class="childbox varbox">
              <div class="item title">
                <span class="label">变量</span>
                <span class="val">变量类型</span>
                <span class="val">存储方式</span>
              </div>
              <div v-if="
                !(props.data.space_vars && props.data.space_vars.length > 0)
              " class="c-emptybox">
                暂无变量
              </div>
              <div v-if="
                (props.data.space_vars && props.data.space_vars.length > 0)
              " class="item" v-for="(item, index) in props.data.space_vars" v-show="item.type !== 'HIDE_SPACE_VARS'">
                <span class="label">
                  <el-input @click.stop.prevent @mousedown.stop @blur="
                    isValidVariableNamefn(item, props.data.space_vars);
                  emits('changespace_varsname', {
                    name: item.name,
                    id: item.id,
                    space_vars: props.data.space_vars,
                    eventtype: 'name',
                  });
                  " size="small" placeholder="请输入变量名" v-model="item.name" />
                </span>
                <div class="val">
                  <el-select size="small" @change="
                    (val) => {
                      val == 'String' || val == 'Integer'
                        ? (item.type = 'over_write')
                        : '';
                      emits('changespace_varsname', {
                        data_type: item.data_type,
                        id: item.id,
                        space_vars: props.data.space_vars,
                        eventtype: 'data_type',
                      });
                    }
                  " v-model="item.data_type" placeholder="请选择">
                    <el-option value="String" label="String"></el-option>
                    <el-option value="Integer" label="Integer"></el-option>
                    <el-option value="Number" label="Number"></el-option>
                    <el-option value="Array<String>" label="Array<String>"></el-option>
                    <el-option value="Array<Integer>" label="Array<Integer>"></el-option>
                    <el-option value="Array<Number>" label="Array<Number>"></el-option>
                  </el-select>
                </div>
                <div class="val">
                  <el-select size="small" v-model="item.type" placeholder="请选择">
                    <el-option value="over_write" label="覆盖"></el-option>
                    <el-option v-if="
                      item.data_type == 'Array<Number>' ||
                      item.data_type == 'Array<String>' ||
                      item.data_type == 'Array<Integer>'
                    " value="append" label="追加"></el-option>
                    <el-option v-if="
                      item.data_type == 'Array<Number>' ||
                      item.data_type == 'Array<String>' ||
                      item.data_type == 'Array<Integer>'
                    " value="append_unique" label="不重复追加"></el-option>
                  </el-select>
                  <span title="删除当前项" @click="
                    delConfirmFn(
                      '删除该变量将同步删除工作流下所有节点变量存储下相关的引用，确定要删除么？',
                      () => {

                        emits('changespace_varsname', {
                          data_type: item.data_type,
                          id: item.id,
                          space_vars: props.data.space_vars,
                          eventtype: 'del',
                        });
                        props.data.space_vars.splice(index, 1);
                      }
                    )
                    " class="iconfont icon-liebiao-shanchu"></span>
                </div>
                <div v-if="item.errtip" style="width: 100%" class="errtip">
                  {{ item.errtip }}
                </div>
              </div>
            </div>
          </div>
        </div>


        <!-- 循环体 -->
        <div v-if="props.data.loop_traget !== undefined" style="margin-bottom: -20px;" class="itembox">
          <div class="ltitle">
            <span :class="{ off: isHideloop_traget }" @click.stop="isHideloop_traget = !isHideloop_traget"
              class="iconfont icon-xiajiantou pointer"></span> <span class="iconfont icon-chaifenziduan"></span>
            拆分字段<el-tooltip popper-class="c-flowtip" class="item" effect="dark" content="用于循环的可拆分目标字段" placement="top">
              <span class="iconfont icon-bangzhu"></span>
            </el-tooltip>
          </div>
          <el-form-item v-show="isHideloop_traget && isHideName" style="width: calc(100% - 252px);margin-right: 16px;"
            prop="loop_traget" label="目标字段">
            <div class="nowheel nodrag" style="width: 100%;height: 40px;">
              <Editor :nodes="nodes" :edges="edges" :nodeid="id" v-model="props.data.loop_traget">
              </Editor>
            </div>
          </el-form-item>

          <el-form-item v-show="isHideloop_traget && isHideName" style="width: 110px;margin-right: 16px;"
            prop="loop_traget" label="每批大小">
            <el-input-number style="width: 100%;" size="large" v-if="props.data.loop_size !== undefined"
              @focus="$event.target.select()" v-model="props.data.loop_size" placeholder="分拆大小" :min="1" :precision="0"
              :step="1" :controls="false" />
          </el-form-item>

          <el-form-item style="width: 110px;margin-right: 0px;" prop="max_workers" label="并发数">
            <el-input-number style="width: 100%;" size="large" @focus="$event.target.select()"
              v-model="props.data.max_workers" placeholder="空表示不限制" :min="1" :max="64" :precision="0"
              :controls="false" />
          </el-form-item>

        </div>

        <!-- 并发数 v-if="props.data.type == 'loop'"-->



        <!-- 提示词 -->

        <div v-if="props.data.prompt_template !== undefined" class="itembox">
          <div class="ltitle">
            <span :class="{ off: isHide2 }" @click.stop="isHide2 = !isHide2"
              class="iconfont icon-xiajiantou pointer"></span>
            <span style="font-size: 18px;" class="iconfont icon-tishici-weixuanzhong-caidanicon"></span> 提示词
            <div class="fr">
              <div @click="
                emits('opendrawerfn', {
                  type: 0,
                  item: props.data,
                  id: props.id,
                  nodeid: props.data.id,
                })
                " class="addvarbtn">选择提示词</div>
            </div>
          </div>

          <div v-show="isHide2" class="tscbox utilbox">
            <div v-if="!props.data.prompt_id" class="c-emptybox">
              暂无提示词
            </div>
            <div v-else class="utilitem">
              <div class="name">
                <div class="lbox">
                  {{ props.data.prompt_template.name }}
                </div>
                <div @click.stop class="rbox">

                  <el-button style="margin-right: 10px;" @click.stop="emits('node_run_debug', {
                    type: '1',
                    id: props.data.id,
                    content: props.data.prompt_template.content,
                  });" size="small" plain type="primary">运行一次<span
                      class="iconfont icon-liebiao-zhihang"></span></el-button>


                  <span title="修改" @click="
                    emits('opentscfn', {
                      type: 0,
                      item: props.data.prompt_template,
                      id: props.id,
                      nodeid: props.data.id,
                    })
                    " class="iconfont icon-liebiao-bianji c-pointer"></span>
                  <span title="删除" @click="
                    props.data.prompt_template = '';
                  props.data.prompt_id = '';
                  " class="iconfont icon-liebiao-shanchu c-pointer"></span>

                </div>
              </div>
              <div :title="props.data.prompt_template.content || '这个提示词还没有介绍~'
                " class="introbox">
                <p class="ellipsis3">
                  {{
                    props.data.prompt_template.content || "这个提示词还没有介绍~"
                  }}</p>
              </div>
            </div>
          </div>
        </div>


        <!-- 视觉 -->
        <div v-if="props.data.type == 'llm'" class="itembox">
          <div class="ltitle">
            <span :class="{ off: isHidevt_file }" @click.stop="isHidevt_file = !isHidevt_file"
              class="iconfont icon-xiajiantou pointer"></span><span class="iconfont icon-jiaosexinxi"></span> 视觉
            <el-tooltip popper-class="c-flowtip" v-if="props.data.type == 'llm'" class="item" effect="dark"
              content="开启视觉功能将允许模型输入图片，并根据图像内容消息的理解回答用户问题" placement="top">
              <span class="iconfont icon-bangzhu"></span>
            </el-tooltip>

            <div class="fr">
              <el-switch :disabled="curllm.type != 'VLM'" style="margin-left: 5px" v-model="props.data.use_vt">
              </el-switch>
            </div>
          </div>

          <div v-if="isHidevt_file && props.data.use_vt" style="margin-bottom: 20px;" class="inpauto choiceroleprompt">
            <div style="height: 40px; width: 100%;z-index: 80;">
              <Editor :nodes="nodes" :edges="edges" :nodeid="id" ref="vt_file" v-model="props.data.vt_file">
              </Editor>
            </div>


          </div>
        </div>

        <div style="margin-top: 20px;" v-if="props.data.type == 'llm'" class="itembox">

          <el-form-item v-if="props.data.type == 'llm'" style="width: 100%;margin-right: 0px;margin-bottom: 0;"
            prop="auto_section_run" label="输出分身">
            <template #label>
              <span style="font-weight: bold;font-size: 12px;">输出分身
                <el-tooltip popper-class="c-flowtip" v-if="props.data.type == 'llm'" class="item" effect="dark"
                  content="在面临选择工具、自动决策下游流程、变量存储等多任务并发执行的复杂场景时，大模型可能会遇到处理能力瓶颈。为此，程序特别设计了分身功能，使得该角色能够一分为三，同时并发执行不同的任务。"
                  placement="top">
                  <span class="iconfont icon-bangzhu"></span>
                </el-tooltip>
              </span>
            </template>
            <div class="c-switchbox">
              <div class="label"><span class="iconfont icon-shifoufenshen"></span> {{ props.data.auto_section_run ?
                '开启分身' :
                '未开启分身' }}</div>
              <div class="switch">
                <el-switch @change="
                  (val) => {
                    switchchangefn(val, 'auto_section_run');
                  }
                " v-model="props.data.auto_section_run" />
              </div>
            </div>
          </el-form-item>

        </div>

        <div v-if="
          props.data.functions !== undefined && props.data.type !== 'tool'
        " class="itembox">
          <div class="ltitle">
            <span :class="{ off: isHide3 }" @click.stop="isHide3 = !isHide3"
              class="iconfont icon-xiajiantou pointer"></span><span class="iconfont icon-keyonggongju"></span> 可用工具

            <span class="c-pointer inpopenbox" :class="{ on: isReopen }" @click="isReopen = !isReopen">
              <span class="iconfont icon-anniu-zhankai"></span> {{ isReopen ? '收起' : '展开' }}
            </span>

            <div v-if="props.data.react !== undefined" class="fr">
              <template v-if="props.data.react">
                <span class="rborder">最大推理次数 </span>
                <el-tooltip popper-class="c-flowtip" effect="dark" content="可以进行ReAct的最大轮数，达到最大轮数后，系统会自动添加提示词要求模型停止摊理。"
                  placement="top">
                  <span class="iconfont icon-bangzhu"></span>
                </el-tooltip>
                <el-input-number @click.stop.prevent @mousedown.stop size="small"
                  style="width: 100px;margin-right: 10px;" placeholder="最大react次数" v-model="props.data.react_max_times"
                  :min="1" :max="10" :precision="0" :step="1" />
              </template>
              <span class="rborder">ReAct推理 </span>
              <el-tooltip popper-class="c-flowtip" effect="dark"
                content="思考 → 行动 → 观察 模式。启用后，大模型会多次循环思考或使用工具，速度会变慢，效果会变好" placement="top">
                <span class="iconfont icon-bangzhu"></span>
              </el-tooltip>

              <el-switch style="margin-left: 5px" @change="
                (val) => {
                  switchchangefn(val, 'react');
                }
              " v-model="props.data.react">
              </el-switch>


            </div>
          </div>

          <div v-if="props.data.react && isReopen && isHide3" style="margin-bottom: 20px;"
            class="inpauto choiceroleprompt">
            <div style="height: 100px; width: 100%;z-index: 20;">
              <Editor :nodes="nodes" :edges="edges" :nodeid="id" ref="react_part_prompt"
                v-model="props.data.react_part_prompt">
              </Editor>
            </div>
            <div @click="
              react_part_prompt.setValue(
                store.getters.ComValueMap['react_part_prompt']
              )
              " class="btn-update c-pointer">
              <span title="恢复默认值" class="iconfont icon-huifumorenzhi c-pointer"></span>
              重置
            </div>

          </div>

          <div v-show="isHide3" class="utilbox">
            <div style="    margin: 0;
    padding-top: 0;" class="ltitle">
              选择工具
              <div class="fr"><span style="margin-left: 20px" @click="
                emits('checktypefn', {
                  type: 0,
                  item: props.data,
                  id: props.id,
                })
                " class="addvarbtn"><span class="iconfont icon-liebiao-zengjia"></span> 添加工具</span></div>
            </div>

            <div v-if="props.data.functions && props.data.functions.length < 1" class="c-emptybox">
              暂无工具
            </div>

            <div v-if="props.data.functions && props.data.functions.length > 0"
              v-for="(item, index) in props.data.functions" @click="
                emits('checktypefn', {
                  type: item.fun_name,
                  item: props.data,
                  id: props.id,
                })
                " class="utilitem">
              <div class="name">
                {{ item.name }}
                <br />
                {{ item.fun_name }}
              </div>
              <div class="btns">
                <span title="配置" class="iconfont icon-peizhi"></span>
                <span @click.stop="
                  delConfirmFn('确认删除所选工具么？', () => {
                    props.data.functions.splice(index, 1);
                  })
                  " title="删除" class="iconfont icon-liebiao-shanchu"></span>
              </div>
            </div>
          </div>
        </div>
        <div v-if="props.data.functions !== undefined && props.data.type == 'tool'" class="itembox">
          <div class="ltitle">
            <span :class="{ off: isHide3 }" @click.stop="isHide3 = !isHide3"
              class="iconfont icon-xiajiantou pointer"></span>
            <span class="iconfont icon-keyonggongju"></span>工具配置参数
          </div>

          <div v-show="isHide3" class="optbox">
            <!-- 配置工具参数 -->
            <div v-if="
              (props.data.dataItem &&
                (props.data.dataItem.fun_name == 'vectorstore_retrieve' ||
                  props.data.dataItem.fun_name == 'product_retrieve' ||
                  props.data.dataItem.fun_name ==
                  'inventory_price_retrieve')) ||
              props.data.dataItem.fun_name == 'printer_consumable_retrieve' ||
              props.data.dataItem.fun_name == 'knowledge_retrieve' ||
              props.data.dataItem.fun_name == 'calculator' ||
              props.data.dataItem.fun_name == 'knowledge_append' ||
              props.data.dataItem.fun_name == 'unit_test_add' ||
              props.data.dataItem.fun_name == 'train_case_add' ||
              props.data.dataItem.fun_name == 'flow_node_logs' ||
              props.data.dataItem.fun_name == 'knowledge_add' ||
              props.data.dataItem.fun_name == 'websearch'
            " class="itembox product_searchbox">
              <!-- 文档检索工具配置 -->
              <el-form style="width: 100%;" :model="props.data.functions[0].options" label-position="top" inline
                label-width="auto">


                <template v-if="
                  props.data.dataItem.fun_name ==
                  'knowledge_add'
                ">

                  <el-form-item style="width: 100%;margin-right: 0;" label="">
                    <template #label>
                      knowledgebase_id参数<span class="c-tips ellipsis">{{
                        props.data.functions[0].options.knowledgebase_id_desc }}</span>
                    </template>
                    <div style="height: 42px; width: 100%; z-index: 53">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="id"
                        v-model="props.data.functions[0].options.knowledgebase_id">
                      </Editor>
                    </div>
                  </el-form-item>

                  <el-form-item style="width: 100%;margin-right: 0;" label="">
                    <template #label>
                      category_id参数<span class="c-tips ellipsis">{{ props.data.functions[0].options.category_id_desc
                        }}</span>
                    </template>
                    <div style="height: 42px; width: 100%; z-index: 52">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="id"
                        v-model="props.data.functions[0].options.category_id">
                      </Editor>
                    </div>
                  </el-form-item>

                  <el-form-item style="width: 100%;margin-right: 0;" label="">
                    <template #label>
                      title参数<span class="c-tips ellipsis">{{ props.data.functions[0].options.title_desc
                      }}</span>
                    </template>
                    <div style="height: 42px; width: 100%; z-index: 51">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="id"
                        v-model="props.data.functions[0].options.title">
                      </Editor>
                    </div>
                  </el-form-item>

                  <el-form-item style="width: 100%;margin-right: 0;" label="">
                    <template #label>
                      content参数<span class="c-tips ellipsis">{{ props.data.functions[0].options.content_desc }}</span>
                    </template>
                    <div style="height: 42px; width: 100%; z-index: 50">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="id"
                        v-model="props.data.functions[0].options.content">
                      </Editor>
                    </div>
                  </el-form-item>



                </template>




                <template v-if="
                  props.data.dataItem.fun_name ==
                  'flow_node_logs'
                ">

                  <el-form-item style="width: 100%;margin-right: 0;" label="">
                    <template #label>
                      flow_id参数<span class="c-tips ellipsis">{{ props.data.functions[0].options.flow_id_desc }}</span>
                    </template>
                    <div style="height: 42px; width: 100%; z-index: 43">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="id"
                        v-model="props.data.functions[0].options.flow_id">
                      </Editor>
                    </div>
                  </el-form-item>

                  <el-form-item style="width: 100%;margin-right: 0;" label="">
                    <template #label>
                      role_id参数<span class="c-tips ellipsis">{{ props.data.functions[0].options.role_id_desc }}</span>
                    </template>
                    <div style="height: 42px; width: 100%; z-index: 42">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="id"
                        v-model="props.data.functions[0].options.role_id">
                      </Editor>
                    </div>
                  </el-form-item>

                  <el-form-item style="width: 100%;margin-right: 0;" label="">
                    <template #label>
                      start_time参数<span class="c-tips ellipsis">{{ props.data.functions[0].options.start_time_desc
                      }}</span>
                    </template>
                    <div style="height: 42px; width: 100%; z-index: 41">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="id"
                        v-model="props.data.functions[0].options.start_time">
                      </Editor>
                    </div>
                  </el-form-item>

                  <el-form-item style="width: 100%;margin-right: 0;" label="">
                    <template #label>
                      end_time参数<span class="c-tips ellipsis">{{ props.data.functions[0].options.end_time_desc }}</span>
                    </template>
                    <div style="height: 42px; width: 100%; z-index: 40">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="id"
                        v-model="props.data.functions[0].options.end_time">
                      </Editor>
                    </div>
                  </el-form-item>

                  <el-form-item style="width: 100%;margin-right: 0;" label="">
                    <template #label>
                      max_top_n参数<span class="c-tips ellipsis">{{ props.data.functions[0].options.max_top_n_desc
                      }}</span>
                    </template>
                    <div style="height: 42px; width: 100%; z-index: 39">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="id"
                        v-model="props.data.functions[0].options.max_top_n">
                      </Editor>
                    </div>
                  </el-form-item>

                </template>


                <template v-if="
                  props.data.dataItem.fun_name ==
                  'train_case_add'
                ">

                  <el-form-item style="width: 100%;margin-right: 0;" label="">
                    <template #label>
                      train_cate_id参数<span class="c-tips ellipsis">{{ props.data.functions[0].options.train_cate_id_desc
                      }}</span>
                    </template>
                    <div style="height: 42px; width: 100%; z-index: 43">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="id"
                        v-model="props.data.functions[0].options.train_cate_id">
                      </Editor>
                    </div>
                  </el-form-item>

                  <el-form-item style="width: 100%;margin-right: 0;" label="">
                    <template #label>
                      input_content参数<span class="c-tips ellipsis">{{ props.data.functions[0].options.input_content_desc
                      }}</span>
                    </template>
                    <div style="height: 42px; width: 100%; z-index: 42">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="id"
                        v-model="props.data.functions[0].options.input_content">
                      </Editor>
                    </div>
                  </el-form-item>

                  <el-form-item style="width: 100%;margin-right: 0;" label="">
                    <template #label>
                      output_contet参数<span class="c-tips ellipsis">{{ props.data.functions[0].options.output_contet_desc
                      }}</span>
                    </template>
                    <div style="height: 42px; width: 100%; z-index: 41">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="id"
                        v-model="props.data.functions[0].options.output_contet">
                      </Editor>
                    </div>
                  </el-form-item>

                  <el-form-item style="width: 100%;margin-right: 0;" label="">
                    <template #label>
                      feature参数<span class="c-tips ellipsis">{{ props.data.functions[0].options.feature_desc }}</span>
                    </template>
                    <div style="height: 42px; width: 100%; z-index: 40">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="id"
                        v-model="props.data.functions[0].options.feature">
                      </Editor>
                    </div>
                  </el-form-item>

                  <el-form-item style="width: 100%;margin-right: 0;" label="">
                    <template #label>
                      node_log_id参数<span class="c-tips ellipsis">{{ props.data.functions[0].options.node_log_id_desc
                      }}</span>
                    </template>
                    <div style="height: 42px; width: 100%; z-index: 39">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="id"
                        v-model="props.data.functions[0].options.node_log_id">
                      </Editor>
                    </div>
                  </el-form-item>

                  <el-form-item style="width: 100%;margin-right: 0;" label="">
                    <template #label>
                      test_case_id参数<span class="c-tips ellipsis">{{ props.data.functions[0].options.test_case_id_desc
                      }}</span>
                    </template>
                    <div style="height: 42px; width: 100%; z-index: 38">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="id"
                        v-model="props.data.functions[0].options.test_case_id">
                      </Editor>
                    </div>
                  </el-form-item>


                </template>


                <template v-if="
                  props.data.dataItem.fun_name ==
                  'unit_test_add'
                ">

                  <el-form-item style="width: 100%;margin-right: 0;" label="">
                    <template #label>
                      unit_cate_id参数<span class="c-tips ellipsis">{{ props.data.functions[0].options.unit_cate_id_desc
                      }}</span>
                    </template>
                    <div style="height: 42px; width: 100%; z-index: 33">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="id"
                        v-model="props.data.functions[0].options.unit_cate_id">
                      </Editor>
                    </div>
                  </el-form-item>

                  <el-form-item style="width: 100%;margin-right: 0;" label="">
                    <template #label>
                      node_log_id参数<span class="c-tips ellipsis">{{ props.data.functions[0].options.node_log_id_desc
                      }}</span>
                    </template>
                    <div style="height: 42px; width: 100%; z-index: 32">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="id"
                        v-model="props.data.functions[0].options.node_log_id">
                      </Editor>
                    </div>
                  </el-form-item>

                  <el-form-item style="width: 100%;margin-right: 0;" label="">
                    <template #label>
                      test_note参数<span class="c-tips ellipsis">{{ props.data.functions[0].options.test_note_desc
                      }}</span>
                    </template>
                    <div style="height: 42px; width: 100%; z-index: 31">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="id"
                        v-model="props.data.functions[0].options.test_note">
                      </Editor>
                    </div>
                  </el-form-item>


                </template>

                <template v-if="
                  props.data.dataItem.fun_name ==
                  'knowledge_append'
                ">

                  <el-form-item style="width: 100%;margin-right: 0;" label="">
                    <template #label>
                      doucument_id参数<span class="c-tips ellipsis">{{ props.data.functions[0].options.doucument_id_desc
                      }}</span>
                    </template>
                    <div style="height: 42px; width: 100%; z-index: 23">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="id"
                        v-model="props.data.functions[0].options.doucument_id">
                      </Editor>
                    </div>
                  </el-form-item>

                  <el-form-item style="width: 100%;margin-right: 0;" label="">
                    <template #label>
                      content参数<span class="c-tips ellipsis">{{ props.data.functions[0].options.content_desc }}</span>
                    </template>
                    <div style="height: 42px; width: 100%; z-index: 22">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="id"
                        v-model="props.data.functions[0].options.content">
                      </Editor>
                    </div>
                  </el-form-item>


                </template>




                <el-form-item style="width: 100%;margin-right: 0;" v-if="
                  props.data.dataItem.fun_name ==
                  'printer_consumable_retrieve'
                " label="">
                  <template #label>
                    model参数<span class="c-tips ellipsis">{{ props.data.functions[0].options.model_desc }}</span>
                  </template>
                  <div style="height: 42px; width: 100%; z-index: 17">
                    <Editor :nodes="nodes" :edges="edges" :nodeid="id" v-model="props.data.functions[0].options.model">
                    </Editor>
                  </div>
                </el-form-item>
                <el-form-item style="width: 100%;margin-right: 0;" v-else-if="
                  props.data.dataItem.fun_name ==
                  'calculator'
                " label="">
                  <template #label>
                    expression参数<span class="c-tips ellipsis">{{ props.data.functions[0].options.expression_desc
                    }}</span>
                  </template>
                  <div style="height: 42px; width: 100%; z-index: 17">
                    <Editor :nodes="nodes" :edges="edges" :nodeid="id"
                      v-model="props.data.functions[0].options.expression">
                    </Editor>
                  </div>
                </el-form-item>
                <template v-else-if="props.data.dataItem.fun_name ==
                  'knowledge_retrieve'">


                  <el-form-item style="width: 100%;margin-right: 0;" label="">
                    <template #label>
                      tags参数
                      <!-- <span class="c-tips ellipsis">{{ props.data.functions[0].options.tags_desc }}</span> -->
                      <el-tooltip popper-class="c-flowtip" effect="dark" raw-content
                        content="填写要过滤的知识库标签<br />知识库的标签包含填写的标签或者知识库标签为空的会被匹配。没有填写标签则选择的库均被匹配" placement="top">
                        <span class="iconfont icon-bangzhu"></span>
                      </el-tooltip>
                    </template>
                    <div style="height: 42px; width: 100%; z-index: 15">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="id" v-model="props.data.functions[0].options.tags">
                      </Editor>
                    </div>
                  </el-form-item>
                  <el-form-item style="width: 100%;margin-right: 0;" label="">
                    <template #label>
                      queries参数
                      <!-- <span class="c-tips ellipsis">{{ props.data.functions[0].options.queries_desc }}</span> -->
                      <el-tooltip popper-class="c-flowtip" effect="dark" raw-content
                        content="填写要查询的问题，可以是数组形式<br />queries参数，每个query会在过滤后的库中筛选出topk条数据，合并后过滤评分。" placement="top">
                        <span class="iconfont icon-bangzhu"></span>
                      </el-tooltip>
                    </template>
                    <div style="height: 42px; width: 100%; z-index: 16">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="id"
                        v-model="props.data.functions[0].options.queries">
                      </Editor>
                    </div>
                  </el-form-item>


                </template>

                <el-form-item style="width: 100%;margin-right: 0;" v-if="props.data.dataItem.fun_name ==
                  'vectorstore_retrieve'" label="">
                  <template #label>
                    querys参数<span class="c-tips ellipsis">{{ props.data.functions[0].options.querys_desc }}</span>
                  </template>
                  <div style="height: 42px; width: 100%; z-index: 13">
                    <Editor :nodes="nodes" :edges="edges" :nodeid="id" v-model="props.data.functions[0].options.querys">
                    </Editor>
                  </div>
                </el-form-item>

                <el-form-item style="width: 100%;margin-right: 0;" v-if="props.data.dataItem.fun_name ==
                  'product_retrieve'" label="">
                  <template #label>
                    querys参数<span class="c-tips ellipsis">{{ props.data.functions[0].options.querys_desc }}</span>
                  </template>
                  <div style="height: 42px; width: 100%; z-index: 13">
                    <Editor :nodes="nodes" :edges="edges" :nodeid="id" v-model="props.data.functions[0].options.querys">
                    </Editor>
                  </div>
                </el-form-item>



                <el-form-item style="width: 100%;margin-right: 0;" label=""
                  v-if="props.data.dataItem.fun_name == 'vectorstore_retrieve'">
                  <template #label>
                    brands参数<span class="c-tips ellipsis">{{ props.data.functions[0].options.brands_desc }}</span>
                  </template>
                  <div style="height: 42px; width: 100%; z-index: 12">
                    <Editor :nodes="nodes" :edges="edges" :nodeid="id" v-model="props.data.functions[0].options.brands">
                    </Editor>
                  </div>
                </el-form-item>

                <el-form-item style="width: 100%;margin-right: 0;" label=""
                  v-if="props.data.dataItem.fun_name == 'product_retrieve'">
                  <template #label>
                    nc_ids参数<span class="c-tips ellipsis">{{ props.data.functions[0].options.nc_ids_desc }}</span>
                  </template>
                  <div style="height: 42px; width: 100%; z-index: 11">
                    <Editor :nodes="nodes" :edges="edges" :nodeid="id" v-model="props.data.functions[0].options.nc_ids">
                    </Editor>
                  </div>
                </el-form-item>


                <div v-if="
                  props.data.functions[0].options.doc_knowledge_base_ids !==
                  undefined
                " class="formtitle">
                  <span>请选择知识库</span>
                  &nbsp;
                  <el-tooltip popper-class="c-flowtip" effect="dark" raw-content content="选择本工具使用哪些知识库" placement="top">
                    <span class="iconfont icon-bangzhu"></span>
                  </el-tooltip>
                </div>

                <el-form-item style="width: 100%;margin-right: 0;" v-if="
                  props.data.functions[0].options.doc_knowledge_base_ids !==
                  undefined
                " label="文档知识库">
                  <el-select v-model="props.data.functions[0].options.doc_knowledge_base_ids
                    " multiple collapse-tags :max-collapse-tags="3" placeholder="请选择知识库">
                    <el-option v-for="item in textlist" :key="item.id" :label="item.name" :value="item.id" />
                  </el-select>
                </el-form-item>
                <el-form-item style="width: 100%;margin-right: 0;"
                  v-if="props.data.functions[0].options.doc_top_k !== undefined" label="">
                  <template #label>召回数量
                    <el-tooltip popper-class="c-flowtip" effect="dark" raw-content content="知识库向量查询召回的评分排名靠前的n条"
                      placement="top">
                      <span class="iconfont icon-bangzhu"></span>
                    </el-tooltip>
                  </template>
                  <el-input-number @click.stop.prevent @mousedown.stop style="width: 382px;margin-right: 10px;"
                    placeholder="请填写文本召回文本数" v-model="props.data.functions[0].options.doc_top_k" :min="0" :max="20"
                    :precision="0" :step="1" controls-position="right" /><span
                    v-show="props.data.functions[0].options.doc_top_k > 5"
                    class="c-danger">文本数太多，可能会影响大模型token数超出限制</span>
                </el-form-item>


                <el-form-item style="width: 100%;margin-right: 0;" v-if="
                  props.data.functions[0].options.excel_knowledge_base_ids !==
                  undefined
                " label="EXCEL参数库">
                  <el-select v-model="props.data.functions[0].options.excel_knowledge_base_ids
                    " multiple collapse-tags :max-collapse-tags="3" placeholder="请选择EXCEL参数库">
                    <el-option v-for="item in excellist" :key="item.id" :label="item.name" :value="item.id" />
                  </el-select>
                </el-form-item>
                <el-form-item style="width: 100%;margin-right: 0;" v-if="
                  props.data.functions[0].options.excel_top_k !== undefined
                " label="">
                  <template #label>召回数量
                    <el-tooltip popper-class="c-flowtip" effect="dark" raw-content content="知识库向量查询召回的评分排名靠前的n条"
                      placement="top">
                      <span class="iconfont icon-bangzhu"></span>
                    </el-tooltip>
                  </template>
                  <el-input-number @click.stop.prevent @mousedown.stop style="width: 382px;margin-right: 10px;"
                    placeholder="请填写EXCEL参数库召回文本数" v-model="props.data.functions[0].options.excel_top_k" :min="0"
                    :max="20" :precision="0" :step="1" controls-position="right" /><span
                    v-show="props.data.functions[0].options.excel_top_k > 5"
                    class="c-danger">文本数太多，可能会影响大模型token数超出限制</span>
                </el-form-item>



                <el-form-item style="width: 100%;margin-right: 0;"
                  v-if="props.data.functions[0].options.top_k !== undefined" label="召回文本数">
                  <el-input-number @click.stop.prevent @mousedown.stop style="width: 382px;margin-right: 10px;"
                    v-model="props.data.functions[0].options.top_k" placeholder="请填写召回文本数" :min="0" :max="20"
                    :precision="0" :step="1" controls-position="right" />
                  <span v-show="props.data.functions[0].options.top_k > 5"
                    class="c-danger">文本数太多，可能会影响大模型token数超出限制</span>
                </el-form-item>


                <el-form-item style="width: 100%;margin-right: 0;" v-if="
                  props.data.functions[0].options.filter_value !== undefined
                " label="">
                  <template #label>评分过滤
                    <el-tooltip popper-class="c-flowtip" effect="dark" raw-content content="知识库向量查询分数的阈值，低于此分数的将不会召回"
                      placement="top">
                      <span class="iconfont icon-bangzhu"></span>
                    </el-tooltip>
                  </template>
                  <el-slider @click.stop.prevent @mousedown.stop style="width: 382px;margin-right: 3px;"
                    v-model="props.data.functions[0].options.filter_value" :step="0.05" :min="0" :max="1" />
                  <span style="padding-left: 20px" v-show="props.data.functions[0].options.filter_value > 0.5"
                    class="c-danger">过滤分数过高，可能会影响召回文档数</span>
                </el-form-item>


                <div v-if="props.data.dataItem.fun_name == 'knowledge_retrieve'" class="formtitle">
                  <span>唯一查询编码</span>
                  &nbsp;
                  <el-tooltip popper-class="c-flowtip" effect="dark" content="根据Excel文档的唯一编码查询，将会按照编码 和 元数据，召回跟编码匹配的所有文
档，过滤 taqs和 queries，只按照ids查询" placement="top">
                    <span class="iconfont icon-bangzhu"></span>
                  </el-tooltip>
                </div>

                <el-form-item v-if="props.data.dataItem.fun_name == 'knowledge_retrieve'"
                  style="width: 100%;margin-right: 0;" label="">
                  <template #label>
                    ids参数
                    <!-- <span class="c-tips ellipsis">{{ props.data.functions[0].options.ids_desc }}</span> -->
                    <el-tooltip popper-class="c-flowtip" effect="dark" raw-content
                      content="数组形式，可以填写一个或多个，对应Excel模板里的 唯一编码" placement="top">
                      <span class="iconfont icon-bangzhu"></span>
                    </el-tooltip>
                  </template>
                  <div style="height: 42px; width: 100%; z-index: 14">
                    <Editor :nodes="nodes" :edges="edges" :nodeid="id" v-model="props.data.functions[0].options.ids">
                    </Editor>
                  </div>
                </el-form-item>
                <div style="margin-bottom: 16px;" class="itembox"
                  v-if="props.data.functions[0].options && props.data.functions[0].options.metadata_filter !== undefined">
                  <div class="ltitle">
                    <span :class="{ off: ismetadata_filter }" @click.stop="ismetadata_filter = !ismetadata_filter"
                      class="iconfont icon-xiajiantou pointer"></span> <span
                      class="iconfont icon-keyonggongju"></span>元数据
                    <el-tooltip popper-class="c-flowtip" effect="dark" raw-content content="与ids参数类似，可以过滤Excel的表头数
据据，具体说明参考官方文档" placement="top">
                      <span class="iconfont icon-bangzhu"></span>
                    </el-tooltip>
                    <span class="fr">


                      <span class="addvarbtn" @click="
                        props.data.functions[0].options.metadata_filter.push({
                          id: Date.now(),
                          key: '',
                          operator: '=',
                          value: '',
                          desc: '',
                        })

                        ">
                        <span class="iconfont icon-liebiao-zengjia"></span>
                        添加条件</span>
                    </span>
                  </div>


                  <div v-show="ismetadata_filter" class="itemcontain">

                    <div class="childbox varbox">
                      <div class="item title">
                        <span style="width:25%" class="val">字段</span>
                        <span style="width:25%" class="val">操作符</span>
                        <span style="width:25%" class="val">值</span>
                        <span style="width:25%" class="val">描述</span>
                      </div>
                      <div v-if="
                        !(props.data.functions[0].options && props.data.functions[0].options.metadata_filter.length > 0)
                      " class="c-emptybox">
                        暂无数据
                      </div>

                      <div v-if="
                        (props.data.functions[0].options && props.data.functions[0].options.metadata_filter.length > 0)
                      " class="item" v-for="(item, index) in props.data.functions[0].options.metadata_filter">
                        <div style="width:25%" class="val">
                          <el-input @click.stop.prevent @mousedown.stop
                            @blur="item.key ? item.errtip = '' : item.errtip = '字段不能为空'" size="small" placeholder=""
                            v-model="item.key" />
                        </div>
                        <div style="width:25%" class="val">
                          <el-select size="small" v-model="item.operator" placeholder="请选择">
                            <el-option value="=" label="="></el-option>
                          </el-select>
                        </div>
                        <div style="width:25%" class="val">
                          <el-input @click.stop.prevent @mousedown.stop size="small" placeholder=""
                            v-model="item.value" />

                        </div>

                        <div style="width:25%" class="val">
                          <el-input @blur="item.desc ? item.errtip = '' : item.errtip = '描述不能为空'" @click.stop.prevent
                            @mousedown.stop size="small" placeholder="" v-model="item.desc" />
                          <span title="删除当前项" @click="
                            delConfirmFn(
                              '确定要删除该数据吗？',
                              () => {
                                props.data.functions[0].options.metadata_filter.splice(index, 1);
                              }
                            )
                            " class="iconfont icon-liebiao-shanchu"></span>
                        </div>
                        <div v-if="item.errtip" style="width: 100%" class="errtip">
                          {{ item.errtip }}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>



                <el-form-item style="width: 100%;margin-right: 0;" v-if="
                  props.data.functions[0].options.output_option !== undefined
                " label="输出格式">
                  <el-radio-group v-model="props.data.functions[0].options.output_option">
                    <el-radio value="json">输出json格式内容</el-radio>
                    <el-radio value="markdown">输出markdown内容</el-radio>

                  </el-radio-group>
                </el-form-item>
              </el-form>
            </div>
            <div v-else @wheel.stop class="itembox c-scroll-box">

              <div class="testbox">
                <div class="testbody">
                  <el-form style="width: 100%;" ref="formflowRef" :model="flowtestform" label-width="auto"
                    class="demo-dynamic">
                    <template v-if="flowtestform.inputs">
                      <el-form-item style="width: 100%;margin-right: 0;" v-for="(item, index) in flowtestform.inputs"
                        :key="item.key" :label="''" :prop="'inputs[' + index + '].curvalue'">
                        <div class="namebox">
                          <span class="name">{{ item.name }}</span>
                          <span v-if="item.is_required" class="c-danger">*</span>

                          <span v-if="item.caption" class="desc ellipsis" :title="item.caption">{{
                            item.caption
                          }}</span>
                          <span v-else class="desc ellipsis" :title="item.desc">{{
                            item.desc
                          }}</span>
                          <span class="type">{{ item.data_type }}</span>
                        </div>

                        <div v-if="item.name == 'user_input'" :style="'height: 240px; width: 100%;z-index: ' +
                          (1000 - index)
                          ">
                          <Editor :nodes="nodes" :edges="edges" :nodeid="id" v-model="item.curvalue"></Editor>
                        </div>
                        <div v-else :style="'height: 60px; width: 100%;z-index: ' + (1000 - index)
                          ">
                          <Editor :nodes="nodes" :edges="edges" :nodeid="id" v-model="item.curvalue"></Editor>
                        </div>
                      </el-form-item>
                    </template>

                    <el-form-item v-if="
                      props.data.functions[0].options.output_option !==
                      undefined
                    " label="输出格式">
                      <el-radio-group v-model="props.data.functions[0].options.output_option">
                        <el-radio value="json">输出json格式内容</el-radio>
                        <el-radio value="markdown">输出markdown内容</el-radio>

                      </el-radio-group>
                    </el-form-item>
                  </el-form>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="!props.data.isHideChild" class="itembox">
          <div class="ltitle">
            <span :class="{ off: isHide5 }" @click.stop="isHide5 = !isHide5"
              class="iconfont icon-xiajiantou pointer"></span>
            <span class="iconfont icon-xiayoujiaose"></span>
            下游角色<el-tooltip popper-class="c-flowtip" class="item" effect="dark"
              content="本节点的下游节点，当有多个下游，且开启自动选择时，大模型会根据任务情况自动选择（可以选择多个）" placement="top">
              <span class="iconfont icon-bangzhu"></span>

            </el-tooltip>
            <span class="c-pointer inpopenbox" :class="{ on: isXyopen }" @click="isXyopen = !isXyopen">
              <span class="iconfont icon-anniu-zhankai"></span> {{ isXyopen ? '收起' : '展开' }}
            </span>

            <div v-if="props.data.auto_choice_node !== undefined" class="fr">
              <span class="rborder">自动选择</span>
              <el-tooltip popper-class="c-flowtip" effect="dark" content="开启后，大模型根据任务情况选择分支，关闭后，所有分支都会被执行"
                placement="top">
                <span class="iconfont icon-bangzhu"></span>
              </el-tooltip>
              <el-switch style="margin-left: 5px" @change="
                (val) => {
                  switchchangefn(val, 'auto_choice_node');
                }
              " v-model="props.data.auto_choice_node">
              </el-switch>
            </div>
          </div>
          <div v-show="isHide5" class="itemcontain">
            <div v-if="props.data.auto_choice_node && isXyopen" style="margin-bottom: 20px;"
              class="inpauto choiceroleprompt">
              <div style="height: 100px; width: 100%">
                <Editor :nodes="nodes" :edges="edges" :nodeid="id" ref="choiceroleprompt"
                  v-model="props.data.choice_role_prompt"></Editor>
              </div>
              <div @click="
                choiceroleprompt.setValue(
                  store.getters.ComValueMap['choice_role_prompt']
                )
                " class="btn-update c-pointer">
                <span title="恢复默认值" class="iconfont icon-huifumorenzhi c-pointer"></span>
                重置
              </div>

            </div>
            <div class="xyjsbox">
              <div style="margin-bottom: 10px; color: #333;" class="citem">
                <span class="label">角色名</span>
                <span class="val">最大运行次数</span>
              </div>
              <div v-if="
                !(props.data.next_nodes && props.data.next_nodes.length > 0)
              " class="c-emptybox">
                暂无下游角色
              </div>
              <div v-if="
                (props.data.next_nodes && props.data.next_nodes.length > 0)
              " class="citem" v-for="item in props.data.next_nodes">
                <div class="label">
                  <el-input :value="item.role" disabled type="text"></el-input>
                </div>
                <div @click.stop.prevent @mousedown.stop class="val">
                  <el-input-number style="width: 100%;" v-model="item.max_run_times" :min="1" :max="1000"
                    :controls="true">
                  </el-input-number>
                </div>
              </div>
            </div>
          </div>
        </div>

        <template v-if="props.data.outputs !== undefined">
          <!-- <div v-if="props.data.type == 'start'" class="itembox">
          <div class="ltitle">输入</div>
        </div> -->
          <div v-if="props.data.type !== 'start'" class="itembox">
            <div class="ltitle">
              <span :class="{ off: isHide6 }" @click.stop="isHide6 = !isHide6"
                class="iconfont icon-xiajiantou pointer"></span> <span class="iconfont icon-bianliangcunchu"></span>
              变量存储<el-tooltip popper-class="c-flowtip" class="item" effect="dark"
                content="使用大模型提取文本的能力，进行各种变量的存储，可以存储到自身，或者工作空间" placement="top">
                <span class="iconfont icon-bangzhu"></span>
              </el-tooltip>
              <span class="c-pointer inpopenbox" :class="{ on: isBlopen }" @click="isBlopen = !isBlopen">
                <span class="iconfont icon-anniu-zhankai"></span> {{ isBlopen ? '收起' : '展开' }}
              </span>
              <span class="fr">
                <span class="addvarbtn" @click="addOutput(0)">
                  <span class="iconfont icon-liebiao-zengjia"></span>
                  新增变量</span>
              </span>
            </div>
          </div>

          <div v-show="isHide6 && isBlopen" class="inpauto choiceroleprompt">
            <div style="height: 100px; width: 100%;margin-bottom: 20px;">
              <Editor :nodes="nodes" :edges="edges" :nodeid="id" ref="outputvarprompt"
                v-model="props.data.output_var_prompt"></Editor>
            </div>
            <div @click="
              outputvarprompt.setValue(
                store.getters.ComValueMap['output_var_prompt']
              )
              " class="btn-update c-pointer">
              <span title="恢复默认值" class="iconfont icon-huifumorenzhi c-pointer"></span>
              重置
            </div>

          </div>
          <div v-show="isHide6" class="outputbox c-flow-outputbox c-treebox">
            <div class="item title">
              <div class="intro">存储位置</div>
              <div class="key">变量名</div>
              <div class="type">变量类型</div>

              <div class="intro1">描述</div>
              <div class="opt"></div>
            </div>
            <div v-if="props.data.outputs && props.data.outputs.length < 1" class="c-emptybox">
              暂无变量
            </div>
            <el-tree v-if="props.data.outputs && props.data.outputs.length > 0" style="width: 100%"
              :data="props.data.outputs" node-key="id" default-expand-all empty-text=" " :expand-on-click-node="false">
              <template #default="{ node, data }">
                <div class="item custom-tree-node">
                  <div class="intro">
                    <el-select v-show="node.level <= 1" size="small" :disabled="node.level > 1" @change="
                      (val) => {
                        changeprefix(data, val);
                      }
                    " v-model="data.prefix" placeholder="存储位置">
                      <el-option value="space" label="工作空间"></el-option>
                      <el-option value="role" label="角色自身"></el-option>
                    </el-select>
                  </div>
                  <div class="key" @click.stop.prevent @mousedown.stop
                    :style="'margin-right:-' + 18 * (node.level - 1) + 'px'">
                    <el-input v-if="data.prefix != 'space'" @blur="isValidVariableNamefn(data, node)"
                      placeholder="输入变量名" size="small" v-model="data.name"
                      :style="'width:' + (160 - 18 * node.level) + 'px'"></el-input>
                    <el-select v-if="data.prefix == 'space'" :style="'width:' + (160 - 18 * node.level) + 'px'"
                      size="small" v-model="data.space_vars_id" @change="
                        (val) => {
                          changespace_varsfn(data, val);
                          isValidVariableNamefn(data, node);
                        }
                      " placeholder="选择工作空间变量">
                      <el-option v-for="(item, index) in props.space_vars"
                        :disabled="isDisabledspace_vars(props.data.outputs, item.id) && data.space_vars_id != item.id"
                        :value="item.id" :label="item.name"></el-option>
                    </el-select>
                  </div>
                  <div class="type">
                    <el-select size="small" :disabled="data.prefix == 'space'" v-model="data.data_type" @change="
                      (val) => {
                        changefn(data, val);
                      }
                    " placeholder="选择类型">
                      <el-option v-for="(val, key) in store.getters.keyTypes" :value="key" :label="val"
                        :disabled="isDisabled(node, val)"></el-option>
                    </el-select>
                  </div>

                  <div @click.stop.prevent @mousedown.stop class="intro1">
                    <el-input size="small" v-model="data.desc" placeholder="请描述变量的用途"></el-input>
                  </div>
                  <div class="opt">
                    <div class="chkbox oitem">
                      <!-- <el-checkbox v-model="data.is_required" label="" size="small" /> -->
                      <span title="新增子项" v-show="node.level < 4 &&
                        (data.data_type == 'Object' ||
                          data.data_type == 'Array<Object>')
                        " @click="addOutput(node.level, data)" class="iconfont icon-shuzhuang-tianjia"></span>
                    </div>
                    <!-- <div class="addchild oitem"></div> -->
                    <div class="del oitem">
                      <span title="删除当前项" @click="remove(node, data, 'output')"
                        class="iconfont icon-liebiao-shanchu"></span>
                    </div>
                  </div>

                  <div v-if="data.errtip" style="width: 100%" class="errtip">
                    {{ data.errtip }}
                  </div>
                </div>
              </template>
            </el-tree>
          </div>
        </template>
      </div>
    </el-form>
  </div>
  <Handle :id="'target_1'" v-if="
    props.data.type != 'start' &&
    props.data.type != 'work_space' &&
    props.data.type != 'loop_start'
  " type="target" class="c-handle c-handletarget" :position="Position.Left" />

  <el-popover v-if="curnode.parentNode && curnode.data.type != 'loop_end'" ref="popover" :visible="visible"
    placement="right" :width="400">
    <template #reference>
      <Handle @mouseup="visible = !visible" :id="'source_1'" v-if="
        props.data.type != 'end' &&
        props.data.type != 'work_space' &&
        props.data.type != 'loop_end'
      " type="source" :class="{ on: visible }" class="c-handle c-handlesource addbtn" :position="Position.Right" />
    </template>

    <div class="navbox">
      <el-input type="text" clearable size="small" v-model="filterText" placeholder="搜索"></el-input>
      <el-scrollbar>
        <div v-for="(item, index) in clonenavlist.filter(
          (item) => item.datatype == 'llm'
        )" :key="index" @click="addNode($event, item, index)" class="item c-shadow">
          <div :title="item.role" class="c-icons ellipsis">
            <span :class="'iconfont ' + item.icon"></span>
            <div class="ellipsis">{{ item.role }}</div>
          </div>
        </div>
        <div class="navlisttitle">工具</div>
        <div v-for="(item, index) in clonenavlist.filter(
          (item) => item.datatype == 'tool'
        )" :key="index" @click="addNode($event, item, index)" class="item c-shadow">
          <div :title="item.role" class="c-icons ellipsis">
            <span :class="'iconfont ' + item.icon"></span>
            <div class="ellipsis">{{ item.role }}</div>
          </div>
        </div>
        <div class="navlisttitle">工作流工具</div>
        <div v-for="(item, index) in clonenavlist.filter(
          (item) => item.datatype == 'flow'
        )" :key="index" @click="addNode($event, item, index)" class="item c-shadow">
          <div :title="item.role" class="c-icons ellipsis">
            <span :class="'iconfont ' + item.icon"></span>
            <div class="ellipsis">{{ item.role }}</div>
          </div>
        </div>

        <div class="navlisttitle">工具插件</div>
        <div v-for="(item, index) in clonenavlist.filter(
          (item) => item.datatype == 'plugin'
        )" :key="index" @click="addNode($event, item, index)" class="item c-shadow">
          <div :title="item.role" class="c-icons ellipsis">
            <span :class="'iconfont ' + item.icon"></span>
            <div class="ellipsis">{{ item.role }}</div>
          </div>
        </div>

        <div class="navlisttitle">MCP工具</div>
        <div v-for="(item, index) in clonenavlist.filter(
          (item) => item.datatype == 'mcp'
        )" :key="index" @click="addNode($event, item, index)" class="item c-shadow">
          <div :title="item.role" class="c-icons ellipsis">
            <span :class="'iconfont ' + item.icon"></span>
            <div class="ellipsis">{{ item.role }}</div>
          </div>
        </div>

      </el-scrollbar>
    </div>
  </el-popover>

  <Handle v-else :id="'source_1'" v-if="
    props.data.type != 'end' &&
    props.data.type != 'work_space' &&
    props.data.type != 'loop_end'
  " type="source" class="c-handle c-handlesource" :position="Position.Right" />


</template>

<style scoped>
.formtitle {
  font-size: 12px;
  text-align: left;
  padding: 5px 16px;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  position: relative;
  width: 100%;
  background: #f6fafd;
  margin: 0 -16px 16px -16px;
}

.optfilebox {
  display: block;
  width: 100%;
  text-align: left;
}

.optfilebox .labelbox {
  display: flex;
  width: 100%;
  text-align: left;
  align-items: center;
  justify-content: flex-start;
  padding-top: 16px;
  padding-bottom: 10px;

}

.optfilebox .c-tips {
  margin-left: 0;
  padding-left: 0;
}

.node_run_debugbtn {
  display: flex;
  align-items: center;
  cursor: pointer;
}



.node_run_debugbtn>.iconfont:hover {
  color: var(--el-color-primary);
}

.node_run_debugbtn .icon-liebiao-shanchu:hover {
  color: var(--el-color-danger);
}

.node_run_debugbtn .icon-liebiao-shanchu {
  padding-left: 0;
}

.c-tips {
  display: inline-block;
  max-width: 400px;
  line-height: 12px;
  font-size: 12px;
  position: relative;
  top: 1px;
}

.inpopenbox {
  display: inline-flex;
  align-items: center;
  justify-content: flex-start;
  color: var(--el-color-primary);
  font-weight: normal;
}

.inpopenbox.on .iconfont {
  transform: rotate(180deg);
}

.inpopenbox .iconfont {
  margin: 0;
  transition: all 0.3s;
}

.loopbg {
  position: absolute;
  left: 16px;
  right: 16px;
  top: 16px;
  bottom: 16px;
  background: var(--c-flowbg-color);
}

.optbox {
  width: 100%;
}

.xyjsbox {
  margin-top: 0px;
  padding: 12px;
  box-sizing: border-box;
}

.xyjsbox .citem {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  margin-bottom: 20px;
}

.xyjsbox .citem:nth-last-child(1) {
  margin-bottom: 0;
}

.xyjsbox .citem .label,
.xyjsbox .citem .val {
  width: calc(50% - 8px);
}

.xyjsbox .citem .label {
  margin-right: 16px;
}

.xyjsbox .citem .val {
  margin-right: 0;
}

.addvarbtn {
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--el-color-primary);
  font-size: 14px;
}

.addvarbtn .icon-liebiao-zengjia {
  margin-right: 4px;
}

.addvarbtn:hover {
  opacity: 0.7;
}

.btn-update {
  position: absolute;
  background: #fff;
  right: 6px;
  bottom: 6px;
  z-index: 55;
  cursor: pointer;
  font-size: 12px;
}

.btn-update .iconfont {
  font-size: 12px;
}

/* nowheel 类名可以禁用滚轮缩放事件 nodrag 禁用拖拽 输入框里禁用 */
.choiceroleprompt {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  position: relative;
  display: block;
  width: 100%;
}

.isHideloop_traget {
  display: flex;
  align-items: center;
  justify-content: flex-start;
}



.loopchild {
  padding-top: 0px;
}

.navbox {
  width: 100%;
  height: 50vh;
}

.navbox .item {
  display: block;
  cursor: pointer;
  margin-bottom: 10px;
  padding: 10px;
}

.navbox .item .c-icons {
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.navbox .navlisttitle {
  text-align: left;
  font-weight: bold;
  padding: 10px 15px 15px 15px;
}

.addgroupsbox {
  position: absolute;
  right: 10px;
  top: 50%;
  margin-top: -10px;
  width: 20px;
  height: 20px;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  cursor: pointer;
  font-size: 22px;
  font-weight: bold;
  color: #fff;
  background: var(--el-color-success);
  border-radius: 50%;
}

.nodeid {
  color: #aaa;
  font-size: 14px;
}

.flowbox {
  max-height: 400px;
  overflow-y: auto;
  overflow-x: hidden;
}

.cardbox>.demo-dynamic {
  padding-bottom: 20px;
}

.cardbox.loop_start {
  width: 240px !important;
}

.cardbox.close>.demo-dynamic {
  padding-bottom: 0px;
}

.demo-dynamic .namebox {
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  flex-wrap: wrap;
  width: 100%;
}

.demo-dynamic .namebox .name {
  font-weight: bold;
  color: #333;
  margin-right: 5px;
}

.demo-dynamic .namebox .c-danger {
  padding: 0;
  margin-right: 5px;
}

.demo-dynamic .namebox .desc {
  color: #999;
  margin-right: 5px;
  max-width: 200px;
}

.demo-dynamic .namebox .type {
  background: #eee;
  display: inline-block;
  padding: 2px 5px;
  line-height: 18px;
  border-radius: 3px;
  font-size: 12px;
}

.testbox {
  display: block;
  height: 100%;
  width: 100%;
}

.testbox .iconfont,
.testbox .title {
  font-weight: bold;
  font-size: 26px;
  text-align: left;
}

.c-handle {
  width: 30px;
  height: 100%;
  align-items: center;
  display: flex;
  justify-content: center;
  background: none;
  border: none;
}

/* .c-handle.c-handletarget{
  transform: translate(-20px, -50%);
} */
.c-handle::after {
  content: "";
  display: flex;
  align-items: center;
  justify-content: center;
  width: 4px;
  height: 16px;
  background: var(--el-color-primary);
  border-radius: 2px;
  transition: all 0.3s;
  position: relative;
  right: -1px;
}

.c-handle.c-handletarget::after {
  background: #651FF3;
  left: -1px;
}

.icon-qitaleidengguang {
  color: #1948e7;
  font-weight: bold;
  font-size: 20px;
}

.icon-bangzhu {
  color: #999;
}

.utilbox {
  text-align: left;
  position: relative;
  width: 100%;
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: flex-start;
}

.utilbox .addbtn {
  position: absolute;
  top: 0px;
  right: 0px;
}

.utilbox .tr {
  margin-bottom: 10px;
}

.utilbox .utilitem {
  display: flex;
  position: relative;
  text-align: left;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  padding: 0px;
  cursor: pointer;
  transition: all 0.3s;
  width: calc(50% - 6px);
  margin-bottom: 12px;
  box-sizing: border-box;
  padding: 12px;
  align-items: center;
  justify-content: space-between;
}

.utilbox .utilitem:nth-child(2n) {
  margin-right: 12px;
}

.utilbox .utilitem:nth-child(2n+1) {
  margin-right: 0px;
}

.c-dataset-btns .icon-liebiao-shanchu {
  padding-left: 0;
}

.utilbox.tscbox {
  padding: 0;
  width: 100%;
}

.utilbox.tscbox .utilitem {
  display: block;
  padding: 0px;
  margin: 0;
  width: 100%;
  box-sizing: border-box;
  padding-bottom: 0px;
}

.tscbox .utilitem .name {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
  background: #F6F8FA;
  border-radius: 8px 8px 0px 0px;
  border-bottom: 1px solid var(--el-border-color);
  color: #333333;
  padding: 8px;
}

.tscbox .utilitem .name .rbox {
  flex-shrink: 0;
}

.utilbox .utilitem .btns {}

.utilbox .utilitem:hover {
  border-color: var(--el-color-primary);
}

.utilbox .utilitem:hover .btns {
  display: block;
}

.utilbox .utilitem .btns .icon-peizhi:hover {
  color: var(--el-color-primary);
}

.utilbox .icon-jiahao1 {
  font-weight: bold;
}

.rborder {
  display: inline-block;
  padding: 2px 5px;
}

.namebox {
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
}

.namebox.c-require-icon::before {
  transform: translate(8px, 0);
  margin-right: 14px;
}

.namebox .item {
  width: 48%;
}

.namebox .selbox {
  display: flex;
  align-items: center;
}

.namebox .selbox .label {
  width: 70px;
  text-align: center;
}

.namebox .selbox .val {
  width: calc(100% - 80px);
}

.icon-liebiao-shanchu {
  cursor: pointer;
  padding-left: 10px;
}

.icon-liebiao-shanchu:hover {
  color: var(--el-color-danger);
}

.introbox {
  font-size: 12px;
  color: var(--c-font-color);
  text-align: left;
  padding: 8px;
  word-break: break-all;
  max-height: 60px;
}

.itembox .item {
  padding: 5px 10px;
  box-sizing: border-box;
}

.itembox .flexbox .item {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.itembox .childbox .item {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  flex-wrap: wrap;
}

.itembox .childbox .item .val,
.itembox .childbox .item .label {
  width: 50%;
  text-align: left;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  box-sizing: border-box;
  padding: 0 5px;
}

.itembox .childbox .item.title .val,
.itembox .childbox .item.title .label {
  text-align: center;
  justify-content: center;
}

.itembox .childbox .item.title.lf .val,
.itembox .childbox .item.title.lf .label {
  text-align: left;
  justify-content: flex-start;
}

.itembox .childbox.outbox .item .val,
.itembox .childbox.outbox .item .label {
  width: 25%;
}

.itembox .childbox.varbox .item .label {
  width: 30%;
}

.itembox .childbox.varbox .item .val {
  width: 35%;
}

.itembox .childbox.varbox.startbox .item .val {
  width: 50%;
}

.itembox .childbox.varbox .item .opt {
  width: 20%;
}

.itembox .childbox.varbox .item .val .iconfont {
  flex-shrink: 0;
  padding-left: 10px;
  cursor: pointer;
}

.xyjsbox,
.varbox,
.outputbox {
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  width: 100%;
  overflow: hidden;
}

.varbox .item {
  padding: 12px 10px 0px 10px;
}

.itembox .itemcontain {
  display: block;
  width: 100%;
}

.varbox .item:nth-last-child(1) {
  padding-bottom: 12px;
}

.outputbox .item {
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  flex-wrap: wrap;
  width: 100%;
  text-align: left;
  padding: 0;
}

.start .outputbox .item {
  padding-left: 10px;
}

.itembox .item.title,
.outputbox .item.title {
  color: #aaa;
  font-size: 12px;
  background: #fcfcfc;
  text-align: center;
  padding-top: 6px;
  padding-bottom: 6px;
}

.outputbox .item.title .key {
  width: 170px;
}

.outputbox .item div {
  box-sizing: border-box;
}

.outputbox .item.title div {
  padding-top: 5px;
  padding-bottom: 5px;
}

.outputbox .item .key {
  width: 160px;
  padding: 10px 5px 10px 0px;
}

.outputbox .item .type {
  width: 140px;
  padding: 10px 5px;
}

.outputbox .item .intro {
  width: 110px;
  padding: 10px 10px;
}

.outputbox .item .intro1 {
  width: 190px;
  padding: 10px 10px;
}

.curstartbox.outputbox .item .intro1 {
  width: 160px;
}

.outputbox .item .opt {
  width: 80px;
  padding: 10px 10px;
}

.outputbox .item .opt {
  display: flex;
  align-items: center;
}

.outputbox .item .opt .oitem {
  width: 33.3%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.outputbox .item .opt .iconfont {
  cursor: pointer;
}

.errtip {
  display: inline-block;
  text-align: left;
  color: var(--el-color-danger);
  padding: 0 0 5px 0px;
  font-size: 12px;
  font-weight: normal;
}

.toolbox {
  text-align: left;
}

.toolbox .item {
  padding: 5px 10px;
  cursor: pointer;
}

.toolbox .item:hover {
  background: #f3f3f3;
}

.toolbox .item.del:hover {
  background: var(--el-color-danger-light-8);
}

.inpbox {
  text-align: left;
  padding: 10px 0;
}

.ltitle {
  font-size: 12px;
  text-align: left;
  padding: 16px 0;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  position: relative;
  width: 100%;
}

.ltitle .iconfont {
  margin-right: 2px;
}

.ltitle .fr {
  position: absolute;
  right: 0;
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.ltitle .iconfont.pointer {
  padding: 0;
  font-size: 12px;
  transition: all 0.3s;
  transform: rotate(-90deg);
}

.ltitle .iconfont.pointer.icon-xiajiantou {
  padding: 0;
  font-size: 12px;
  transition: all 0.3s;
  transform: rotate(-90deg);
  width: 10px;
  height: 20px;
  margin-right: 10px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ltitle .iconfont.pointer.off {
  transform: rotate(0deg);
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header .btns .iconfont {
  margin-left: 10px;
  cursor: pointer;
  position: relative;
  z-index: 10;
}

.header .ltitle {
  font-size: 16px;
}

.cardbox .itembox {
  margin-bottom: 0;
  display: flex;
  flex-wrap: wrap;
  width: 100%;
}

.cardbox>div:nth-last-child(1) {
  margin-bottom: 16px;
}

.cardbox.loop_start>div:nth-last-child(1) {
  margin-bottom: 0;
}

.cardbox .header .itembox {
  margin-bottom: 0;
}

.cardbox {
  background: #fff;
  border-radius: 14px;
  border: none;
  position: relative;
  width: 750px;
  box-sizing: border-box;
  padding: 0px 16px;
  overflow: hidden;
}

.cardbox.loop {
  width: 100%;
}

.cardbox .header {
  background: #fff;
  padding: 0px;
  margin: 0 -16px;
  padding: 0 16px;
  border-bottom: 1px solid var(--el-border-color);
}

.cardbox.close .header {
  border-bottom: none;
}

.cardbox .body {
  display: block;
  transition: all 0.3s;
  padding: 0;
  width: 100%;
}

.cardbox .btn-delbox {
  position: absolute;
  right: -38px;
  top: 0px;
  z-index: 10;
  display: none;
  width: 40px;
  height: 40px;
}

.cardbox:hover .btn-delbox {
  display: block;
}

.cardbox.close .body {
  max-height: 0;
  overflow: hidden;
  padding: 0 10px;
}

.icon-shugui {
  color: var(--chakra-colors-primary-600);
  font-size: 20px;
}
</style>


<style>
.c-flow-outputbox .item.custom-tree-node .intro {
  position: relative;
  left: -26px;

}

.c-flow-outputbox .item.custom-tree-node .errtip {
  left: 110px;
  position: relative;
}

.c-flow-outputbox .el-tree-node__expand-icon {
  left: 105px;
}

.c-flow-box .vue-flow__node {
  background: #fff;
  border: 1px solid transparent;
  border-radius: 14px;
}

.c-flow-box .vue-flow__node:hover {
  border: 1px solid var(--el-color-primary);
}

.c-flow-box .vue-flow__node.selected {
  border: 1px solid var(--el-color-success);
}

.c-handle.addbtn.on::after,
.c-flow-box .vue-flow__node:hover .c-handle.addbtn::after,
.c-handle.addbtn:hover::after {
  content: "+";
  color: #fff;
  width: 20px;
  height: 20px;
  border-radius: 100%;
  font-size: 18px;
}
</style>
