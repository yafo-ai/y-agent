<script setup>
import { ref, toRef, watch, onMounted, onUnmounted } from "vue";
import {
  Position,
  VueFlow,
  useVueFlow,
  ConnectionMode,
  useGetPointerPosition,
  MarkerType,
} from "@vue-flow/core";
import { Controls } from "@vue-flow/controls";
import "@vue-flow/controls/dist/style.css";
import { goback, getTime } from "@/components/comp.js";
import CardNode from "./CardNode.vue";
import EdgeWithButton from "./EdgeWithButton.vue";
import useDragAndDrop from "./useDnD";
import { Background } from "@vue-flow/background";
import content from "@/components/content.vue";
import {
  knowledges,
  add_update,
  workflowget,
  workflowrun,
  model_configall,
  tool_flows,
  tools,
  exportJson,
  exportXml,
  node_run_debug,
  node_prompt_debug,
  mcp_providerlist,
  filesuploads,
} from "@/api/api";
import CompApp from "@/views/app/list.vue";
import { renameChildrenKey, transferString } from "@/assets/utils/util.js";
import Editor from "@/components/editor.vue";
import {
  isInteger,
  isValidJSON,
  isValidNumber,
} from "@/assets/utils/validator.js";
import icon from "@/components/icon.vue"
import tscEdit from "@/views/app/edit.vue";
import { cloneDeep } from "lodash"; // 引入lodash库的cloneDeep方法进行深拷贝
import { useStore } from "vuex";

import { useRoute, useRouter } from "vue-router";
const route = useRoute();
const router = useRouter();
const store = useStore();
import { v4 as uuidv4 } from "uuid";

const websocket = ref(null);
const uuid = ref("");
const initwebsocket = () => {
  uuid.value = uuidv4();
  let url = window.location.host || "193.111.99.208";
  if (url == "localhost:5173") {
    url = "193.111.99.208";
  }

  let SOCKET_URL = "ws://" + url + "/ws/" + uuid.value + "/workflow"; //正式环境
  if (websocket.value) return false;
  websocket.value = new WebSocket(SOCKET_URL);
  websocket.value.onopen = (event) => { };
  websocket.value.onmessage = (event) => {
    var resdata = JSON.parse(event.data);
    if (resdata.type == "error") {
      _this.$message(resdata.data.message, "error");
      isLoading.value = false;
      workflowrunfnLoading.value = false;
      return false;
    }
    if (resdata.type == "ai_answer") {
      console.log('收到AI消息开始：=============================================================')
      console.log(resdata.data.message)
      console.log('收到AI消息结束：=============================================================')
      sharelist.value.push({ type: 1, mes: resdata.data.message });
    }

    if (resdata.type == "ai_finish") {
      isLoading.value = false;
      workflowrunfnLoading.value = false;
    }
  };
  websocket.value.onclose = (event) => {
    setTimeout(initwebsocket, 1000); //连接关闭后，重新建立连接
  };
  websocket.value.onerror = (event) => {
    if (websocket.value) {
      websocket.value.close();
    }
    websocket.value = null;
  };
};
const isLoading = ref(false);
const sendSocket = (data) => {
  isLoading.value = true;
  workflowrunfnLoading.value = true;
  websocket.value && websocket.value.send(JSON.stringify(data)); //发送消息
};

onMounted(() => {
  if (route.path == "/flowshare") {
    initwebsocket();
  }
});

onUnmounted(() => {
  websocket.value && websocket.value.close();
  websocket.value = null;
});

const {
  addNodes,
  addEdges,
  screenToFlowCoordinate,
  onNodesInitialized,
  onNodeDragStop,
  onNodesChange,
  onEdgesChange,
  applyEdgeChanges,
  applyNodeChanges,
  updateNode,
  onConnect,
  findNode,
  fitView,
  ZoomTo,
  onPaneClick,
  onPaneMouseMove,
  onMoveEnd,
  GetViewport,
} = useVueFlow();
const { onDragOver, onDrop, onDragLeave, isDragOver } = useDragAndDrop();

const { onDragStart, getName, getId, initNode } = useDragAndDrop();



const nodes = ref([
  {
    id: 100000000001,
    type: "card",
    data: {
      width: "620px",
      id: 100000000001,
      type: "start",
      role: "开始",
      icon: "icon-kaishi1",
      isopen: true,
      isHideChild: true,
      next_nodes: undefined,
      hidebtn: true,
      description: "流程起点",
      inputs: [
        {
          id: Date.now(),
          name: "user_input",
          data_type: "String",
          desc: "用户本轮对话输入内容",
          is_required: true,
          disabled: true,
        },
      ],
    },
    position: { x: 600, y: 300 },
  },
  {
    id: 100000000000,
    type: "card",
    data: {
      width: "400px",
      id: 100000000000,
      type: "work_space",
      role: "工作空间变量",
      icon: "icon-gongzuokongjianbianliang",
      isopen: true,
      space_vars: [],
      isHideChild: true,
      next_nodes: undefined,
      hidebtn: true,
      outputs: undefined,
      description: undefined,
      prompt_template: undefined,
      functions: undefined,
    },
    position: { x: 100, y: 300 },
  },
]);
const edges = ref([]);

const navlist = ref([
  {
    id: 1,
    type: "llm",
    datatype: "llm",
    role: "大模型",
    icon: "icon-damoxing",
    isopen: true,
    next_nodes: [],
    description: "",
    prompt_template: "",
    react_part_prompt: store.getters.ComValueMap["react_part_prompt"],
    choice_role_prompt: store.getters.ComValueMap["choice_role_prompt"],
    output_var_prompt: store.getters.ComValueMap["output_var_prompt"],
    auto_section_run: false,
    use_vt: false,
    vt_file:"",
    llm_id: "",
    functions: [],
    outputs: [],
    react: false,
    react_max_times: 10,
    auto_choice_node: false,
  },
  {
    id: 2,
    type: "temp_executor",
    datatype: "llm",
    role: "执行器",
    icon: "icon-shuchu1",
    isopen: true,
    next_nodes: [],
    description: "用于通过模板直接执行系统函数，可以通过jinja模板编写处理逻辑",
    prompt_template: "",
    choice_role_prompt: "",
    auto_section_run: false,

    hidellm: true,
    llm_id: "",
  },
  {
    id: Date.now(),
    type: "loop",
    datatype: "llm",
    role: "分批处理",
    icon: "icon-pichuli",
    isopen: true,
    next_nodes: [],
    max_workers: 1,
    description: "分批处理",
    prompt_template: undefined,
    loop_traget: "",
    loop_size: "",
    choice_role_prompt: "",
    auto_section_run: false,
    hidellm: true,
    // noCopy:true,
    llm_id: "",
  },
]);

const isShowFlow = ref(false);
const params = ref(null);
if (route.query.id) {


  let api_key = route.query.api_key || undefined;
  workflowget({ id: route.query.id, api_key }, route.path).then((res) => {
    params.value = res;
    document.title = res.name;
    if (res.view_json) {
      nodes.value = JSON.parse(res.view_json).nodes;
      nodes.value.forEach((item) => {
        if (item.data.type == "work_space") {
          // 工作空间变量
          curspace_vars.value = item.data.space_vars;
        }
      });
      let earr = JSON.parse(res.view_json).edges;
      earr.forEach((item) => {
        if (item.type !== "button") {
          item.type = "button";
          item.animated = true;
          item.markerEnd = MarkerType.Arrow;
        }
      });
      edges.value = earr;
      console.log(nodes.value, earr);
    }

    if (route.path == "/flowshare") {
      // 如果是分享页面
      testfn();
    } else {
      getFlowlist();
    }
  });
} else {
  goback(null, router, "/flowlist");
}

const getFlowlist = () => {
  tool_flows({
    page: 1,
    pagesize: 36,
  }).then(async (res) => {
    res.forEach((item) => {
      let inputs = "";
      if (item.view_json) {
        let flow = JSON.parse(item.view_json);
        inputs = JSON.stringify(maptoNodes(flow));
      }

      item.type = "flow";
      funclist.value.push({
        ...item,
        fun_name: "workflow_" + item.id,
        tool: "workflow_" + item.id,
        desc: item.caption,
        name: item.name,
        options: {
          workflow_id: item.id,
          inputs: inputs,
        },
      });
    });

    // 获取工具插件
    let utilres = await tools({
      page: 1,
      pagesize: 10000,
      is_enable: true,
    });
    if (utilres && utilres.rows && utilres.rows.length > 0) {
      utilres.rows.forEach((item) => {
        item.type = "plugin";
        item.datatype = "plugin";
        item.in_params = item.in_params || [];
        let in_paramsarr = [];
        item.in_params.forEach((initem) => {
          // 过滤掉所有有默认值的参数不显示在输入框中
          if (!initem.default_value) {
            in_paramsarr.push(initem)
          }
        })
        item.in_params = in_paramsarr;


        let inputs = {};
        item.in_params.forEach((paramitem) => {
          if (paramitem.default_value) {
            // 如果有默认值  这个字段不做处理
            // inputs[paramitem.name] = paramitem.default_value;
          } else {
            inputs[paramitem.name] = "";
          }
        });

        funclist.value.push({
          ...item,
          fun_name: item.func_name,
          tool: item.func_name,
          desc: item.caption,
          name: item.name,
          options: {
            inputs: JSON.stringify(inputs),
            output_option: "json",
          },
        });
      });
    }

    // 获取mcp工具
    let mcpres = await mcp_providerlist();

    if (mcpres && mcpres.rows && mcpres.rows.length > 0) {
      mcpres.rows.forEach((item) => {
        item.type = "plugin";
        item.datatype = "mcp";
        item.in_params = item.in_params || [];
        let inputs = {};
        item.in_params.forEach((paramitem) => {
          if (paramitem.default_value) {
            // 如果有默认值  这个字段不做处理
            // inputs[paramitem.name] = paramitem.default_value;
          } else {
            inputs[paramitem.name] = "";
          }
        });

        funclist.value.push({
          ...item,
          fun_name: item.func_name,
          tool: item.func_name,
          desc: item.caption,
          name: item.name,
          options: {
            inputs: JSON.stringify(inputs),
            output_option: "json",
          },
        });
      });
    }

    initnavlist();
    isShowFlow.value = true;

    if (route.path == "/flowshare") {
      // 如果是分享页面
      testfn();
    }
  });
};

const save = (fn) => {
  add_update({
    ...params.value,
    view_json: JSON.stringify({
      nodes: renameChildrenKey(cloneDeep(nodes.value)),
      edges: renameChildrenKey(cloneDeep(edges.value)),
    }),
    // view_json:'',
  }).then((res) => {
    if (!fn) {
      _this.$message("保存成功");
    }
    fn && fn();
  });
};

const curflow = ref(null);
const removeNode = (nodeId) => {
  // 删除节点
  const toDelete = new Set();
  function removeNodesDeep(nodeId) {
    // 根据id  递归删除节点
    for (let i = 0; i < nodes.value.length; i++) {
      if (nodes.value[i].parentNode == nodeId) {
        removeNodesDeep(nodes.value[i].id);
      } else if (nodes.value[i].id == nodeId) {
        toDelete.add(nodes.value[i].id);
      }
    }
  }
  removeNodesDeep(nodeId);
  nodes.value = nodes.value.filter((node) => !toDelete.has(node.id));

  // 删除无效的边
  const isDelEdge = new Set();
  function removeEdges() {
    // 根据id  递归删除节点
    for (let i = 0; i < edges.value.length; i++) {
      let sourceindex = -1;
      let targetindex = -1;
      let edge = edges.value[i];
      nodes.value.forEach((node, index) => {
        if (node.id == edge.source) {
          sourceindex = index;
        }

        if (node.id == edge.target) {
          targetindex = index;
        }
      });
      if (targetindex === -1 || sourceindex === -1) {
        // 说明该边无效
        isDelEdge.add(edges.value[i].id);
        continue;
      }
    }
  }
  removeEdges();
  edges.value = edges.value.filter((edge) => !isDelEdge.has(edge.id));

  initNodeSize();
};
let onNodeDragStopTimer = null;
onNodeDragStop((event) => {
  if (!event.node.parentNode) {
    return false;
  }
  clearTimeout(onNodeDragStopTimer);
  onNodeDragStopTimer = setTimeout(() => {
    initNodeSize();
  }, 70);
});

const initNodeSize = () => {
  nodes.value.forEach((node) => {
    if (node.data.type == "loop") {
      initParentNode(node);
    }
  });
};

const initParentNode = (pnode) => {
  let curnodes = [];
  nodes.value.forEach((node) => {
    if (node.parentNode == pnode.id) {
      curnodes.push(node);
    }
  });

  if (curnodes.length > 0) {
    let sizes = calculateBoundingBoxWithSize(curnodes);
    let w = sizes.width <= 1000 ? 1000 : sizes.width;
    let h = sizes.height <= 850 ? 850 : sizes.height;

    pnode.style.width = w + "px";
    pnode.style.height = h + "px";

    updateNode(pnode.id, pnode, { replace: true });
  } else {
    // 删除全部  更新高度

    pnode.style.width = "1000px";
    pnode.style.height = "850px";
    updateNode(pnode.id, pnode, { replace: true });
  }
};

function calculateBoundingBoxWithSize(nodes) {
  let minX = Infinity,
    minY = Infinity;
  let maxX = -Infinity,
    maxY = -Infinity;
  nodes.forEach((node) => {
    const { width, height } = node.dimensions;
    const { x, y } = node.position; // 假设默认尺寸
    minX = Math.min(minX, x);
    minY = Math.min(minY, y);
    maxX = Math.max(maxX, x + width);
    maxY = Math.max(maxY, y + height);
  });

  return {
    width: maxX + 40,
    height: maxY + 40,
    x: minX,
    y: minY,
  };
}


onNodesChange(async (changes) => {
  const nextChanges = [];
  for (const change of changes) {
    if (change.type === "select") {
      // 如果是选中 提升节点
      let curnode = findNode(change.id);
      if (!curnode.isParent && curnode.parentNode) {
        // 如果是子节点  查找父节点
        let pnode = findNode(curnode.parentNode);
        if (change.selected) {
          pnode.zIndex = 10;
        } else {
          // 取消选中  降低父节点层级
          pnode.zIndex = 0;
        }
        updateNode(pnode.id, pnode, { replace: true });

      }

    } if (change.type === "remove") {
      removeNode(change.id);
    } else {
      nextChanges.push(change);
    }
  }
  applyNodeChanges(nextChanges);
});

onEdgesChange(async (changes) => {
  const nextChanges = [];

  for (const change of changes) {
    nextChanges.push(change);
  }
  applyEdgeChanges(nextChanges);
});

const copynode = (nodeId) => {
  // 复制节点

  nodes.value.forEach((item) => {
    if (item.id === nodeId) {
      const newNode = initNode(
        cloneDeep(item.data),
        item.position,
        cloneDeep(item)
      );
      newNode.position = {
        x: item.position.x + (item.dimensions.width + 50),
        y: item.position.y + 50,
      };
      addNodes(newNode);
    }
  });
};

function getTransformMatrixValues(element) {
  const style = window.getComputedStyle(element);
  const matrix = new DOMMatrix(style.transform); // 使用DOMMatrix解析transform矩阵
  return {
    scaleX: matrix.a, // 缩放X轴比例
    scaleY: matrix.d, // 缩放Y轴比例
    translateX: matrix.e, // 水平位移
    translateY: matrix.f, // 垂直位移
  };
}

const addNode = (event, item, index) => {
  // 添加节点
  const element = document.querySelector(".vue-flow__transformationpane");
  const matrixValues = getTransformMatrixValues(element);
  const scale = matrixValues.scaleX;
  const w = window.innerWidth / 2;
  const h = window.innerHeight / 2;
  const position = screenToFlowCoordinate({
    x: w - 300 * scale,
    y: h - 300 * scale,
  });

  const newNode = initNode(cloneDeep(item), position);

  addNodes(newNode);
};



const isShowAdd = ref(false);

const msmap = ref({
  1: "用于查询店铺政策、产品知识、常见参数等的知识库查询工具。适用于一般性问题、多个产品比较类问题等",
  2: "提取的查询问题列表",
  3: "品牌选择项：华为、惠普、奔图、爱普生、佳能、兄弟、东芝、利盟、京瓷、联想、施乐；根据聊天记录和问题选择品牌，不涉及品牌时留空",
  4: "仅当问题中明确包含产品[id]并且是询问该商品的规格时，才使用此工具查询特定[id]商品的规格信息",
  5: "提取的查询问题列表",
  6: "提取产品id列表",
  7: "用于根据商品的品牌、型号查询NC系统商品价格和库存",
  8: '"输出json格式","输出markdown内容"',
  9: '[{"brand":"商品1的品牌","model":"商品1的型号"},{"brand":"商品2的品牌","model":"商品2的型号"}]',
});
const resetFlow = () => {
  store.commit("flowdata", { curnodeid: "" });
};

// store.dispatch('initializeWebsocket', 'wss://your-websocket-url');

watch(
  () => nodes.value.length,
  (newVal, oldVal) => {
    // 这里可以执行你需要的操作
    initNodes();
  },
  {
    deep: true, // 开启深度监听
  }
);

watch(
  () => edges.value.length,
  (newVal, oldVal) => {
    // 这里可以执行你需要的操作
    initNodes();
  },
  {
    deep: true, // 开启深度监听
  }
);

const initNodes = () => {
  nodes.value.forEach((item) => {
    // 初始化子节点数据
    let cdata = [];
    edges.value.forEach((edge) => {
      if (item.id === edge.source) {
        // 如果是子节点
        let cnum = 1;
        if (item.data.next_nodes && item.data.next_nodes.length > 0) {
          // 如果存在子节点，查找节点num
          item.data.next_nodes.forEach((child) => {
            if (child.id === edge.targetNode.id) {
              cnum = child.max_run_times;
            }
          });
        }
        let param = cloneDeep(edge.targetNode);
        param.max_run_times = cnum;
        cdata.push({
          id: param.id,
          max_run_times: cnum,
          role: param.data.role,
        });
      }
    });
    item.data.next_nodes = cdata;
  });
};

const xlform = ref({
  product_knowledge_base_ids: [],
  product_top_k: 1,
  doc_knowledge_base_ids: [],
  doc_top_k: 1,
  excel_knowledge_base_ids: [],
  excel_top_k: 1,
  filter_value: 0.3,
  output_option: "json",
  description: "",
  querys_desc: "",
  brands_desc: "",
});
const funclist = ref([
  // {
  //   fun_name: "vectorstore_retrieve",
  //   name: "文档库检索",
  //   tool: "vectorstore_retrieve",
  //   desc: "用于查询店铺政策、产品知识、常见参数等的知识库查询工具。适用于一般性问题、多个产品比较类问题等",
  //   options: {
  //     product_knowledge_base_ids: [],
  //     product_top_k: 1,
  //     doc_knowledge_base_ids: [],
  //     doc_top_k: 1,
  //     excel_knowledge_base_ids: [],
  //     excel_top_k: 1,
  //     filter_value: 0.3,
  //     output_option: "json",
  //     description: msmap.value[1],
  //     querys_desc: msmap.value[2],
  //     brands_desc: msmap.value[3],
  //     querys: '',
  //     brands: '',
  //   },
  // },
  // {
  //   fun_name: "product_retrieve",
  //   name: "产品参数检索",
  //   nodeType: "tool",
  //   tool: "product_retrieve",
  //   desc: "仅当问题中明确包含产品[id]并且是询问该商品的规格时，才使用此工具查询特定[id]商品的规格信息。",
  //   options: {
  //     excel_knowledge_base_ids: [],
  //     excel_top_k: 1,
  //     output_option: "json",
  //     description: msmap.value[4],
  //     querys_desc: msmap.value[5],
  //     nc_ids_desc: msmap.value[6],
  //     nc_ids: '',
  //     querys: '',
  //   },
  // },
  // {
  //   fun_name: "inventory_price_retrieve",
  //   name: "NC商品价格库存查询",
  //   tool: "inventory_price_retrieve",
  //   nodeType: "tool",
  //   desc: msmap.value[7],
  //   options: {
  //     output_option: "json",
  //     description: msmap.value[7],
  //     querys_desc: msmap.value[9],
  //     querys: "",
  //   },
  // },
  // {
  //   fun_name: "printer_consumable_retrieve",
  //   name: "打印设备耗材查询",
  //   nodeType: "tool",

  //   tool: "printer_consumable_retrieve",
  //   desc: "用于查询打印设备的适用耗材（硒鼓、墨盒、碳粉、粉盒、粉仓、墨水、色带架、色带芯等）",
  //   options: {
  //     description:
  //       "用于查询打印设备的适用耗材（硒鼓、墨盒、碳粉、粉盒、粉仓、墨水、色带架、色带芯等）",
  //     model_desc: "提取打印设备的型号，类似LaserJet Pro MFP M226dw",
  //     model: "",
  //   },
  // },
  // {
  //   fun_name: "websearch",
  //   name: "互联网搜索",
  //   tool: "websearch",
  //   nodeType: "tool",
  //   desc: "使用搜索引擎查询相关信息",
  //   options: {
  //     output_option: "json",
  //     description: "使用搜索引擎查询相关信息",
  //     querys_desc: "填写要查询的内容",
  //     querys: "",
  //     top_k: 1,
  //   },
  // },
  {
    fun_name: "knowledge_retrieve",
    name: "知识库查询",
    tool: "knowledge_retrieve",
    desc: "知识库查询工具，用于查询各种领域知识。",
    options: {
      "description": "知识库查询工具，用于查询各种领域知识。",
      "queries": "",
      "queries_desc": "提取要查询的问题列表",
      "tags": "",
      "tags_desc": "提取要查询问题的标签列表",
      "ids": "",
      "ids_desc": "提取要查询问题的id列表",
      product_knowledge_base_ids: undefined,
      product_top_k: undefined,
      doc_knowledge_base_ids: [],
      doc_top_k: 1,
      excel_knowledge_base_ids: [],
      excel_top_k: 1,
      filter_value: 0.3,
      output_option: "json",
      metadata_filter: [],
    },
  },

  {
    fun_name: "calculator",
    name: "计算器",
    tool: "calculator",
    nodeType: "tool",
    desc: "计算器工具，用于执行数学表达式。",
    options: {
      description: "计算器工具，用于执行数学表达式。",
      expression_desc: "填写要计算的数学表达式",
      expression: "",
    },
  },
  {
    fun_name: "knowledge_append",
    name: "知识库内容追加",
    tool: "knowledge_append",
    nodeType: "tool",
    desc: "用于向知识库指定的文档中追加内容。",
    options: {
      description: "用于向知识库指定的文档中追加内容。",
      doucument_id_desc: "填写文档的id",
      doucument_id: "",
      content_desc: "填写要追加的知识内容",
      content: "",
    },
  },
  {
    fun_name: "unit_test_add",
    name: "添加单元测试",
    tool: "unit_test_add",
    nodeType: "tool",
    desc: "用于把指定的流程运行日志添加到单元测试中。",
    options: {
      description: "用于把指定的流程运行日志添加到单元测试中。",
      unit_cate_id_desc: "填写要添加单元测试的指定分类id",
      unit_cate_id: "",
      node_log_id: "",
      node_log_id_desc: "填写要添加单元测试的节点日志id",
      test_note: "",
      test_note_desc: "填写测试备注信"
    },
  },
  {
    fun_name: "train_case_add",
    name: "添加语料",
    tool: "train_case_add",
    nodeType: "tool",
    desc: "用于向指定的语料分类中添加语料。",
    options: {

      "description": "用于向指定的语料分类中添加语料。",
      "train_cate_id": "",
      "train_cate_id_desc": "填写语料所要归属的分类id",
      "input_content": "",
      "input_content_desc": "填写语料的输入文本",
      "output_contet": "",
      "output_contet_desc": "填写语料的输出文本",
      "feature": "",
      "feature_desc": "填写语料的特征文本",
      "node_log_id": "",
      "node_log_id_desc": "填写与该语料关联的节点日志ID，非必填",
      "test_case_id": "",
      "test_case_id_desc": "填写与该语料关联的单元测试ID，非必填"
    },
  },
  {
    fun_name: "flow_node_logs",
    name: "查询流程日志",
    tool: "flow_node_logs",
    nodeType: "tool",
    desc: "用于使用指定条件查询流程日志",
    options: {
      description: "用于使用指定条件查询流程日志",
      flow_id: "",
      flow_id_desc: "填写流程id",
      role_id: "",
      role_id_desc: "填写节点角色id",
      start_time: "",
      start_time_desc: "填写日志起始日期，格式：yyyy-MM-dd hh:mm:ss",
      end_time: "",
      end_time_desc: "填写日志结束日期，格式：yyyy-MM-dd hh:mm:ss",
      max_top_n: "",
      max_top_n_desc: "填写最大返回的日志数量",
    },
  },
  {
    fun_name: "knowledge_add",
    name: "知识库文档添加",
    tool: "knowledge_add",
    nodeType: "tool",
    desc: "用于向指定的知识库指定的分类中添加一份独立的知识文档。",
    options: {
      description: "用于向指定的知识库指定的分类中添加一份独立的知识文档。",
      knowledgebase_id_desc: "填写文档所属知识库id",
      knowledgebase_id: "",
      category_id: "",
      category_id_desc: "填写文档所属分类id",
      title: "",
      title_desc: "填写文档的标题",
      content: "",
      content_desc: "填写文档的内容",
    },
  },
]);

const getValByKey = (type, key) => {
  var map = {
    knowledge_add: {
      dataType: "tool",
      description: "用于向指定的知识库指定的分类中添加一份独立的知识文档。",
      knowledgebase_id_desc: "填写文档所属知识库id",
      knowledgebase_id: "",
      category_id: "",
      category_id_desc: "填写文档所属分类id",
      title: "",
      title_desc: "填写文档的标题",
      content: "",
      content_desc: "填写文档的内容",
    },
    flow_node_logs: {
      dataType: "tool",
      description: "用于使用指定条件查询流程日志",
      flow_id_desc: "填写流程id",
      role_id_desc: "填写节点角色id",
      start_time_desc: "填写日志起始日期，格式：yyyy-MM-dd hh:mm:ss",
      end_time_desc: "填写日志结束日期，格式：yyyy-MM-dd hh:mm:ss",
      max_top_n_desc: "填写最大返回的日志数量",
    },
    train_case_add: {
      dataType: "tool",
      "description": "用于向指定的语料分类中添加语料。",
      "train_cate_id_desc": "填写语料所要归属的分类id",
      "input_content_desc": "填写语料的输入文本",
      "output_contet_desc": "填写语料的输出文本",
      "feature_desc": "填写语料的特征文本",
      "node_log_id_desc": "填写与该语料关联的节点日志ID，非必填",
      "test_case_id_desc": "填写与该语料关联的单元测试ID，非必填"
    },
    unit_test_add: {
      dataType: "tool",
      description: "用于把指定的流程运行日志添加到单元测试中。",
      unit_cate_id_desc: "填写要添加单元测试的指定分类id",
      node_log_id_desc: "填写要添加单元测试的节点日志id",
      test_note_desc: "填写测试备注信"
    },
    knowledge_append: {
      dataType: "tool",
      description: "用于向知识库指定的文档中追加内容。",
      doucument_id_desc: "填写文档的id",
      content_desc: "填写要追加的知识内容",
    },
    calculator: {
      dataType: "tool",
      description: "计算器工具，用于执行数学表达式。",
      expression_desc: "填写要计算的数学表达式",
    },
    vectorstore_retrieve: {
      description: msmap.value[1],
      dataType: "tool",
      querys_desc: msmap.value[2],
    },
    product_retrieve: {
      description: msmap.value[4],
      dataType: "tool",
      querys_desc: msmap.value[5],
    },
    inventory_price_retrieve: {
      description: msmap.value[7],
      querys_desc: msmap.value[9],
      dataType: "tool",
    },
    printer_consumable_retrieve: {
      description:
        "用于查询打印设备的适用耗材（硒鼓、墨盒、碳粉、粉盒、粉仓、墨水、色带架、色带芯等）",
      model_desc: "提取打印设备的型号，类似LaserJet Pro MFP M226dw",
      dataType: "tool",
    },
    websearch: {
      description: "使用搜索引擎查询相关信息",
      model_desc: "使用搜索引擎查询相关信息",
      dataType: "tool",
    },
    knowledge_retrieve: {
      "description": "知识库查询工具，用于查询各种领域知识。",
      "queries_desc": "提取的查询问题列表",
      "tags_desc": "提取的查询问题的标签列表",
      "ids_desc": "提取查询问题的id列表",
      dataType: "tool",
    },
  };
  if (map[type] && map[type][key] !== undefined) return map[type][key];
  return "";
};

const clonenavlist = ref([])
const clonefunclist = ref([])
const initnavlist = () => {
  let arr = cloneDeep(funclist.value);
  clonefunclist.value = arr;
  console.log(arr)
  arr.forEach((item) => {
    let curopt = cloneDeep(item.options);
    // 提取共有属性以减少重复
    const commonProps = {
      id: item.id + "_" + new Date().getTime(), // 优化点3：将时间戳计算移至循环外部（如果可能）
      type: "tool",
      width: "750px",
      isopen: true,
      next_nodes: [],
      prompt_template: undefined,
      choice_role_prompt: undefined,
      auto_section_run: undefined,
      llm_id: undefined,
      functions: [
        {
          fun_name: item.fun_name,
          options: curopt,
          name: item.name,
        },
      ],
      outputs: undefined,
      react: undefined,
      react_max_times: 10,
      auto_choice_node: undefined,
      dataItem: item,
    };

    // 根据条件设置特定属性
    let specificProps;
    if (item.type == "flow") {
      specificProps = {
        datatype: "flow",
        role: item.name,
        icon: "icon-gongzuoliugongju",
        description: item.caption,
        caption: item.caption,
      };
    } else if (item.type == "plugin" && item.datatype == "plugin") {
      specificProps = {
        datatype: "plugin",
        role: item.name,
        icon: "icon-gongzuochajian",
        description: item.caption,
        caption: item.caption,
      };
    } else if (item.type == "plugin" && item.datatype == "mcp") {
      specificProps = {
        datatype: "mcp",
        role: item.name,
        icon: "icon-MCP",
        description: item.caption,
        caption: item.caption,
      };
    } else {
      specificProps = {
        datatype: "tool",
        role: item.name,
        icon: "icon-gongju1",
        description: getValByKey(item.fun_name, "description"),
      };
    }

    // 合并共有属性和特定属性，并推入navlist
    navlist.value.push({ ...commonProps, ...specificProps });

  });


  clonenavlist.value = cloneDeep(navlist.value);
  console.log(navlist.value)
};
const filterfuncText = ref("");
watch(filterfuncText, (val) => {
  filterFunclist(val)
})
const filterText = ref('')
watch(filterText, (val) => {
  filterNavlist(val)
})




const filterNavlist = (val) => {
  if (val) {
    navlist.value = clonenavlist.value.filter((item) =>
      item.role.toLowerCase().includes(val.toLowerCase())
    );
  } else {
    navlist.value = cloneDeep(clonenavlist.value);
  }
};
const filterFunclist = (val) => {
  if (val) {
    funclist.value = clonefunclist.value.filter((item) =>
      item.name.toLowerCase().includes(val.toLowerCase())
    );
  } else {
    funclist.value = cloneDeep(clonefunclist.value);
  }
};

const maptoNodes = (flow, options) => {
  let testlist = [];
  let nodes = [];
  let inputs = options && options.inputs ? JSON.parse(options.inputs) : {};
  if (flow) {
    nodes = flow.nodes;
    nodes.forEach((item) => {
      if (item.data && item.data.type == "start") {
        testlist = cloneDeep(item.data.inputs) || [];
      }
    });
  }

  testlist.forEach((item) => {
    if (inputs && inputs[item.name]) {
      item.curvalue = inputs[item.name];
    } else {
      item.curvalue = "";
    }
  });

  if (options === undefined) {
    // 初始化
    let inputs = {};
    testlist.forEach((item) => {
      inputs[item.name] = item.curvalue;
    });
    return inputs;
  } else {
    flowtestform.value.inputs = cloneDeep(testlist) || [];
  }
};

const setInputs = () => {
  let inputs = {};
  flowtestform.value.inputs.forEach((item) => {
    inputs[item.name] = item.curvalue;
  });
  checkFunctions.value.forEach((item) => {
    if (item.fun_name == curNodeData.value.type) {
      item.options.inputs = JSON.stringify(inputs);
      item.options.output_option = flowtestform.value.output_option;
    }
  });
};

const getFunclist = (type, datatype) => {
  return funclist.value.filter((item) => {
    if (type) {
      if (datatype) {
        return item.type === type && item.datatype === datatype;
      } else {
        return item.type === type;
      }

    } else {
      return item.type !== "flow" && item.type !== "plugin";
    }
  });
};

const isChecked = (item) => {
  let flag = false;
  checkFunctions.value.forEach((citem) => {
    if (item.fun_name === citem.fun_name) {
      flag = true;
    }
  });
  return flag;
};

const checkItem = (item) => {
  if (isChecked(item)) {
    let index = checkFunctions.value.findIndex(
      (citem) => citem.fun_name === item.fun_name
    );
    checkFunctions.value.splice(index, 1);
  } else {
    checkFunctions.value.push({
      fun_name: item.fun_name,
      options: cloneDeep(item.options),
      name: item.name,
    });
  }
};

const checkFunctions = ref([]);
const curNodeData = ref(null);
const isShowFuncdialog = ref(false);
const curTitle = ref("工作流配置");
const checktype = (data) => {
  curTitle.value = "工作流配置";
  flowtestform.value.type = undefined;
  console.log(data)
  nodeid.value = data.id;
  curNodeData.value = data || null;
  checkFunctions.value = cloneDeep(data.item.functions) || [];
  if (curNodeData.value.type == 0) {
    curTitle.value = "选择工具";
    // 选择工具
  } else if (getValByKey(curNodeData.value.type, "dataType") == "tool") {
    // 配置文档检索工具
    checkFunctions.value.forEach((item) => {
      if (item.fun_name == curNodeData.value.type) {
        curTitle.value = item.name;
        xlform.value = cloneDeep(item.options);
      }
    });
  } else {
    // 配置工作流
    let cindex = -1;
    funclist.value.forEach((item, index) => {
      if (item.fun_name == curNodeData.value.type) {
        cindex = index;
      }
    });
    if (cindex !== -1) {
      let funitem = funclist.value[cindex];
      if (funitem.type === "plugin") {
        // 配置工具插件
        checkFunctions.value.forEach((item) => {
          if (item.fun_name == curNodeData.value.type) {
            curTitle.value = funitem.name;
            flowtestform.value.output_option = item.options.output_option || undefined;
            flowtestform.value.type = funitem.type;
            flowtestform.value.caption = funitem.desc;
            let arr = [];
            funitem.in_params.forEach((citem) => {
              if (citem.default_value) {
                // 如果有默认值 自动不处理
                // citem.curvalue = citem.default_value;
              } else {
                arr.push(citem);
              }

            });
            let testlist = cloneDeep(arr) || [];
            let inputs = item.options.inputs
              ? JSON.parse(item.options.inputs)
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
        });
      } else if (funitem.view_json) {
        let flow = JSON.parse(funitem.view_json);
        checkFunctions.value.forEach((item) => {
          if (item.fun_name == curNodeData.value.type) {
            curTitle.value = item.name;
            flowtestform.value.output_option = item.options.output_option || undefined;
            maptoNodes(flow, cloneDeep(item.options));
            flowtestform.value.caption = funitem.caption;
          }
        });
      } else {
        _this.$message("未找到该工具配置，请先配置相关参数", "error");
        return;
      }
    } else {
      _this.$message("未找到该工具配置，请先配置相关参数", "error");
      return;
    }
  }
  isShowFuncdialog.value = true;
};
const delConfirmFn = async (txt, fn) => {
  let cfm = await _this.$confirm(txt);
  if (cfm) {
    fn && fn();
  }
};
const subfn = async (formEl) => {
  let cindex = -1;
  console.log(xlform.value)
  nodes.value.forEach((item, index) => {
    if (curNodeData.value && curNodeData.value.id === item.id) {
      cindex = index;
    }
  });
  if (curNodeData.value.type == 0) {
    // 选择工具
  } else if (getValByKey(curNodeData.value.type, "dataType") == "tool") {

    // 配置文档检索工具
    checkFunctions.value.forEach((item) => {
      if (item.fun_name == curNodeData.value.type) {
        item.options = cloneDeep(xlform.value);
      }
    });
  } else {
    if (!formEl) return;
    let vald = await formEl.validate((valid) => {
      if (valid) {
        setInputs();
      } else {
        return false;
      }
    });
    if (!vald) return false;
  }
  if (cindex !== -1) {
    nodes.value[cindex].data.functions = checkFunctions.value;
  }
  isShowFuncdialog.value = false;
};

const textlist = ref([]);
const splist = ref([]);
const excellist = ref([]);

if (route.path != "/flowshare") {
  knowledges().then((res) => {
    let arr = res || [];
    textlist.value = [];
    arr.forEach((item) => {
      if (item.type == 2) {
        splist.value.push(item);
      } else if (item.type == 1) {
        textlist.value.push(item);
      } else if (item.type == 3) {
        excellist.value.push(item);
      }
    });
  });
}

const drawer = ref(false);
const checkList = ref([]);
const configtype = ref("");
const curData = ref(null);
const appsubfn = (itemlist) => {
  let cindex = -1;
  nodes.value.forEach((item, index) => {
    if (curData.value && curData.value.id === item.id) {
      cindex = index;
    }
  });
  nodes.value[cindex].data.prompt_template = itemlist[0];
  nodes.value[cindex].data.prompt_id = itemlist[0].id;
  drawer.value = false;
  checkList.value = [];
};
const opendrawer = (data) => {
  nodeid.value = data.id;
  curData.value = data;
  curnodedataid.value = data.nodeid;
  curflowid.value = route.query.id;
  if (data.item.prompt_template && data.item.prompt_template.id) {
    checkList.value = [{ id: data.item.prompt_template.id }];
  } else {
    checkList.value = [];
  }

  drawer.value = true;
};

const showTest = ref(false);
const testlist = ref([]);
const testform = ref({ inputs: [] });
const flowtestform = ref({ inputs: [] });

const testfn = () => {
  if (runresult.value) {
    // 如果存在的时候 直接显示缓存结果 不获取最新的
    runresult.value.__isShowBtn__ = true;
    isShowResult.value = true;
    return false;
  }

  nodes.value.forEach((item) => {
    if (item.data && item.data.type == "start") {
      testlist.value = cloneDeep(item.data.inputs) || [];
    }
  });

  testlist.value.forEach((item) => {
    // 遍历所有输入项，如果有缓存就直接赋值过去

    let curindex = -1;
    testform.value.inputs.forEach((citem, cindex) => {
      if (citem.id == item.id) {
        curindex = cindex;
      }
    });
    if (curindex !== -1) {
      if (item.data_type == "File" || item.data_type == "Array<File>") {
        // 文件类型
        item.fileList = testform.value.inputs[curindex].fileList;
      }
      item.curvalue = testform.value.inputs[curindex].curvalue;
    } else {
      if (item.data_type == "File") {
        // 文件类型
        item.curvalue = {};
        item.fileList = [];
      } else if (item.data_type == "Array<File>") {
        // 文件类型
        item.curvalue = [];
        item.fileList = [];
      } else {
        item.curvalue = store.getters.keyTypesValue[item.data_type];
      }
    }
  });

  testform.value.inputs = cloneDeep(testlist.value) || [];
  showTest.value = true;
};

const formRef = ref(null);
const runresult = ref(null);
const isShowResult = ref(false);
const formflowRef = ref(null);
const workflowrunfnLoading = ref(false);
const workflowrunfn = (formEl) => {
  if (route.path == "/flowshare") {
    // 分享流程
    if (workflowrunfnLoading.value) {
      return false;
    }
    workflowrunfnLoading.value = true;
    let inputs = {};
    testform.value.inputs.forEach((item) => {
      inputs[item.name] = item.curvalue;
    });
    sharelist.value.push({
      type: 2,
      mes: inputs.user_input,
    });

    sendSocket({
      type: "run_workflow",
      data: {
        question_id: uuid.value,
        pin_id: uuid.value,
        workflow_id: route.query.id,
        user_id: uuid.value,
        input: inputs,
        origin: 3,
        api_key: route.query.api_key,
      },
    });
    return false;
  }

  let nodesflag = true;
  let errmes = "";
  nodes.value.forEach((item) => {
    if (item.data && item.data.type == "llm") {
      // 校验节点是否配置提示词 大模型 名称
      if (!item.data.prompt_id) {
        errmes = "请检查节点配置，提示词不能为空!";
        nodesflag = false;
      }

      if (!item.data.llm_id) {
        errmes = "请检查节点配置，大模型不能为空!";
        nodesflag = false;
      }

      if (item.data.role == "" || item.data.role == undefined) {
        errmes = "请检查节点配置，节点名称不能为空!";
        nodesflag = false;
      }
    }
  });
  if (!nodesflag) {
    _this.$message(errmes, "error");
    return false;
  }
  if (!formEl) return;
  formEl.validate((valid) => {
    if (valid) {
      let id = route.query.id;
      let param = { id: id, inputs: "" };
      let inputs = {};
      testform.value.inputs.forEach((item) => {
        inputs[item.name] = item.curvalue;
      });
      param.inputs = JSON.stringify(inputs);
      param.use_log = true;
      workflowrun(param).then((res) => {
        res.flow_name = params.value.name;
        runresult.value = res;
        runresult.value.__isShowBtn__ = true;
        testSize.value = "760px";
        isShowResult.value = true;
      });
    } else {
      return false;
    }
  });
};
import result from "@/views/flow/components/result.vue";

const validatorfn = (rule, value, callback) => {
  let item = rule.row;
  if (!item.is_required && !value) {
  } else if (item.is_required && !value && value !== 0) {
    callback(new Error("请输入" + item.name));
    return false;
  } else if (value) {
    if (item.data_type == "String") {
    } else if (item.data_type == "Integer") {
      if (!isInteger(value)) {
        callback(new Error("请输入整数"));
        return false;
      }
    } else if (item.data_type == "Number") {
      if (!isValidNumber(value)) {
        callback(new Error("请输入数字"));
        return false;
      }
    } else if (item.data_type == "Object") {
      if (!isValidJSON(value)) {
        callback(new Error("请输入正确的json"));
        return false;
      }
    } else if (item.data_type.indexOf("Array") !== -1 && item.data_type.indexOf("File") === -1) {

      if (!isValidJSON(value)) {
        callback(new Error("请输入正确的数组"));
        return false;
      }
    }
  }
  callback();
};

const isShowtscEdit = ref(false);
const tscEditItem = ref({
  name: "",
  content: "",
  id: undefined,
  prompt_type_id: null,
});
const curnodedataid = ref("");
const curflowid = ref("");
const nodeid = ref("");
const opentsc = (data) => {
  nodeid.value = data.id;
  curnodedataid.value = data.nodeid;
  curflowid.value = route.query.id;
  let item = data.item;
  if (item) {
    tscEditItem.value = cloneDeep(item);
    isShowtscEdit.value = true;
  }
};

const subtsc = (item, type) => {
  nodes.value.forEach((ele) => {
    if (ele.data.prompt_template && ele.data.prompt_template.id == item.id) {
      ele.data.prompt_template.name = item.name;
      ele.data.prompt_template.content = item.content;
      ele.data.prompt_template.prompt_type_id = item.prompt_type_id;
    }
  });

  isShowtscEdit.value = false;
};
const tscerrfn = (err) => {
  // let item = tscEditItem.value;
  //  nodes.value.forEach((ele) => {
  //   if (ele.data.prompt_template &&  (ele.data.prompt_template.id == item.id)) {
  //     if(err.detail && err.detail.indexOf('未找到该数据') !== -1){
  //       ele.data.prompt_template = '';
  //       ele.data.prompt_id = undefined;
  //     }
  //   }
  // });
};

const llmlist = ref([]);
//  获取大模型配置
if (route.path != "/flowshare") {
  model_configall({}).then((res) => {
    llmlist.value = res || [];
  });
}
const testSize = ref("760px");

const curContext = ref([]);
const dialogFormVisible1 = ref(false);

// 分享页
const sharelist = ref([]);

const resultChange = (item) => { };


const curspace_vars = ref([]);

const changespace_varsname = (data) => {
  if (data.eventtype == "add") {
    curspace_vars.value = data.space_vars;
  } else if (data.eventtype == "del") {
    // 删除  遍历所有节点 删除对应id的数据
    nodes.value.forEach((item) => {
      if (item.data.type == "llm") {
        // 工作空间变量
        if (item.data.outputs && item.data.outputs.length > 0) {
          deleteNodeById(item.data.outputs, data.id);
        }
      }
    });
  } else {
    let spaceitem = null;
    data.space_vars.forEach((item) => {
      if (item.id == data.id) {
        spaceitem = item;
      }
    });
    // 更新name  或者 data_type
    nodes.value.forEach((item) => {
      if (item.data.type == "llm") {
        // 遍历大模型节点并更新
        findAndUpdateNode(item.data.outputs, data.id, spaceitem);
      }
    });
  }

  nodes.value = [].concat(nodes.value);
};

function findAndUpdateNode(tree, id, data) {
  for (let i = 0; i < tree.length; i++) {
    if (tree[i].space_vars_id === id) {
      tree[i].name = data.name; // 找到并修改节点名称
      tree[i].data_type = data.data_type; // 找到并修改节点名称
      return true; // 找到并修改成功，返回true
    } else if (tree[i].children && tree[i].children.length > 0) {
      // 如果当前节点有子节点，递归查找子节点
      if (findAndUpdateNode(tree[i].children, id, data)) {
        return true; // 在子节点中找到并修改成功，返回true
      }
    }
  }
  return false; // 没有找到指定ID的节点，返回false
}
function findNodeAndParent(node, id, parentChildren, parentIndex) {
  if (node.space_vars_id === id) {
    return { parentChildren, parentIndex };
  } else if (node.children) {
    for (let i = 0; i < node.children.length; i++) {
      const result = findNodeAndParent(node.children[i], id, node.children, i);
      if (result) {
        return result;
      }
    }
  }
  return null;
}

function deleteNodeById(tree, id) {
  tree.forEach((node, index) => {
    const result = findNodeAndParent(node, id, tree, index);
    if (result) {
      result.parentChildren.splice(result.parentIndex, 1); // 删除节点
      return true; // 删除成功
    }
  });

  return false; // 未找到节点或已删除
}

const ismetadata_filter = ref(true);
const curshowPrompt = ref({});
const showPrompt = ref(false);


const node_run_debugfn = async (data) => {

  let res = null
  if (data.type == '1') {
    res = await node_prompt_debug({
      "flow_id": route.query.id,
      "runner_id": data.id + '',
      prompt_temp: data.content
    })
  } else {
    res = await node_run_debug({
      "flow_id": route.query.id,
      "runner_id": data.id + ''
    })
  }

  if (res) {
    if (data.type == '1') {
      // 调试提示词
      curshowPrompt.value = res.prompt_str;
      showPrompt.value = true;
    } else {
      // 调试节点
      runresult.value = cloneDeep(res);
      runresult.value.__uid__ = runresult.value.id;  //试运行不需要id
      runresult.value.__flowid__ = route.query.id;  //试运行不需要id
      runresult.value.__runnerid__ = data.id + '';  //试运行不需要id
      runresult.value.__isShowBtn__ = false;
      runresult.value.id = undefined;  //试运行不需要id
      isShowResult.value = true;
    }
  }
}




const panelTo = () => {
  // let curnode = findNode(nodes.value);
  // curnode.selected = true;
  // updateNode(curnode.id, curnode, { replace: true });
  curflow.value.fitView({
    padding: 10, // 可选，视窗周围的填充距离
    minZoom: 0.8,
    maxZoom: 1,
    nodes: [selectNode.value] // 需要展示的节点 ID 数组
  });
}
const selectNode = ref("");
watch(selectNode, (val) => {
  panelTo(val)
})

const isShowmcp = ref(true);
const isShowplu = ref(true);
const isShowflw = ref(true);
const isShowtool = ref(true);
function validateFileTypeWithRegex(file, allowedExtensions) {
  // 创建一个正则表达式来匹配任意一种允许的扩展名
  const regex = new RegExp(`\\.(${allowedExtensions.join('|')})$`, 'i'); // 'i' 用于不区分大小写
  // 检查文件名是否匹配正则表达式
  return regex.test(file.name);
}
const beforeAvatarUpload = (file, item) => {
  if (file.size > item.constraint.max_file_kb * 1024) {
    _this.$message(`文件大小不能超过${item.constraint.max_file_kb}KB`, "error");
    return false;
  }
  if (!validateFileTypeWithRegex(file, item.constraint.allowed_ext_types)) {
    _this.$message(`不支持的文件类型，请上传${item.constraint.allowed_ext_types}格式文件`, "error");
    return false;
  }
  store.commit("loading", true);
  return true;
};

const filesuploadsfn = (fileparams, type) => {
  console.log(item);
  return;
  filesuploads(fileparams, type).then((res) => {
    console.log(res)
  })
}

const sucfn = (res, file, files,item) => {
  store.commit("loading", false);
  let arr = []
  item.fileList.forEach((item) => {
    arr.push(item.response);
  });

  if(item.data_type == 'File'){
    item.curvalue = arr[0];
  }else{
    item.curvalue = arr;
  }
  console.log(item);
};
const errfn = (err) => {
  store.commit("loading", false);
  let myError = err.toString();
  myError = myError.replace("UploadAjaxError: ", "");
  myError = JSON.parse(myError);
  _this.$message(myError.detail, "error");
};

const copymesfn = (mes) =>{
  console.log(mes);
  localStorage.setItem('COMMON__MARKDOWN_EDITOR__TEXT',mes)
}

</script>

<template>
  <div @click="resetFlow()" class="pagebox c-pagebox">
    <div class="topbox">
      <div class="selectbox">
        <div @click="goback(null, $router, '/flowlist')" class="back">

          <span class="title" v-if="params && params.name">{{ params.name }}</span>

        </div>


      </div>
      <div class="btnbox">
        <el-select v-model="selectNode" filterable placeholder="快速定位节点" style="width: 200px;margin-right:16px;">
          <el-option v-for="item in nodes.filter((item) => item.data.type != 'loop_start')" :key="item.id"
            :label="item.data.role" :value="item.id" />
        </el-select>
        <el-button plain @click="save(() => { testfn() })">保存并运行</el-button>
        <el-button type="primary" @click="save()">保存</el-button>

        <span @click="goback(null, $router, '/flowlist')" class="c-iconbackbox">
          <span class="iconfont icon-fuwenben-chexiao"></span> 返回
        </span>
      </div>
    </div>

    <div v-if="!isShowAdd" @click="isShowAdd = true" title="选择节点" class="showAddbtn">
      <span class="iconfont icon-jiahao1"></span>
    </div>
    <div :class="{ open: isShowAdd }" class="navbox">
      <div class="title">
        <span @click="filterText = ''; isShowAdd = false;" class="iconfont icon-fanhui"></span>
        <el-input style="width:calc(100% - 50px);" type="text" v-model="filterText" clearable size="small"
          placeholder="搜索" />
      </div>
      <div class="navbody">
        <el-scrollbar>
          <div v-for="(item, index) in navlist.filter(
            (item) => item.datatype == 'llm'
          )" :key="index" class="vue-flow__node-input item" @click="addNode($event, item, index)" :draggable="true"
            @dragstart="onDragStart($event, cloneDeep(item), nodes)">
            <div :title="item.role" class="c-icons">
              <span :class="'iconfont ' + item.icon"></span>
              <div class="ellipsis">{{ item.role }}</div>
            </div>
            <span class="iconfont icon-liebiao-zengjia"></span>
          </div>
          <div class="navlisttitle">
            <span class="c-open-zhankaibox" :class="{ on: isShowtool }" @click="isShowtool = !isShowtool">
              <span class="iconfont icon-anniu-zhankai"></span> {{ isShowtool ? '' : '' }}工具
            </span>
          </div>
          <div v-show="isShowtool" v-for="(item, index) in navlist.filter(
            (item) => item.datatype == 'tool'
          )" :key="index" class="vue-flow__node-input item c-shadow" :draggable="true"
            @click="addNode($event, item, index)" @dragstart="onDragStart($event, cloneDeep(item), nodes)">
            <div :title="item.role" class="c-icons">
              <span :class="'iconfont ' + item.icon"></span>
              <div class="ellipsis">{{ item.role }}</div>
            </div>
            <span class="iconfont icon-liebiao-zengjia"></span>
          </div>
          <div class="navlisttitle">
            <span class="c-open-zhankaibox" :class="{ on: isShowflw }" @click="isShowflw = !isShowflw">
              <span class="iconfont icon-anniu-zhankai"></span> {{ isShowflw ? '' : '' }}工作流工具
            </span>
          </div>
          <div v-show="isShowflw" v-for="(item, index) in navlist.filter(
            (item) => item.datatype == 'flow'
          )" :key="index" class="vue-flow__node-input item c-shadow" :draggable="true"
            @click="addNode($event, item, index)" @dragstart="onDragStart($event, cloneDeep(item), nodes)">
            <div :title="item.role" class="c-icons">
              <span :class="'iconfont ' + item.icon"></span>
              <div class="ellipsis">{{ item.role }}</div>
            </div>
            <span class="iconfont icon-liebiao-zengjia"></span>
          </div>

          <div class="navlisttitle">
            <span class="c-open-zhankaibox" :class="{ on: isShowplu }" @click="isShowplu = !isShowplu">
              <span class="iconfont icon-anniu-zhankai"></span> {{ isShowplu ? '' : '' }}API工具
            </span>
          </div>
          <div v-show="isShowplu" v-for="(item, index) in navlist.filter(
            (item) => item.datatype == 'plugin'
          )" :key="index" class="vue-flow__node-input item c-shadow" :draggable="true"
            @click="addNode($event, item, index)" @dragstart="onDragStart($event, cloneDeep(item), nodes)">
            <div :title="item.role" class="c-icons">
              <span :class="'iconfont ' + item.icon"></span>
              <div class="ellipsis">{{ item.role }}</div>
            </div>
            <span class="iconfont icon-liebiao-zengjia"></span>
          </div>

          <div class="navlisttitle">
            <span class="c-open-zhankaibox" :class="{ on: isShowmcp }" @click="isShowmcp = !isShowmcp">
              <span class="iconfont icon-anniu-zhankai"></span> {{ isShowmcp ? '' : '' }}MCP工具
            </span>
          </div>
          <div v-show="isShowmcp" v-for="(item, index) in navlist.filter(
            (item) => item.datatype == 'mcp'
          )" :key="index" class="vue-flow__node-input item c-shadow" :draggable="true"
            @click="addNode($event, item, index)" @dragstart="onDragStart($event, cloneDeep(item), nodes)">
            <div :title="item.role" class="c-icons">
              <span :class="'iconfont ' + item.icon"></span>
              <div class="ellipsis">{{ item.role }}</div>
            </div>
            <span class="iconfont icon-liebiao-zengjia"></span>
          </div>
        </el-scrollbar>
      </div>
    </div>


    <!-- @connect="onConnect" @connect-end="onConnectEnd" :is-valid-connection="isValidConnection" 
      @connect-start="onConnectStart"
      @pane-click="paneClick" @connect-end="onConnectEnd" :is-valid-connection="isValidConnection" 
    @connect-start="onConnectStart"
        @connect-start="onConnectStart" 、 :elevate-edges-on-select="true" 选中边提升zindex
        @connect-end="onConnectEnd"  -->
    <div @drop="onDrop" v-if="route.path != '/flowshare' && isShowFlow" class="flow c-flow-box">
      <VueFlow :maxZoom="1" :apply-default="false" :elevate-edges-on-select="true" :minZoom="0.2" ref="curflow"
        :connection-mode="ConnectionMode.Strict" v-model:nodes="nodes" v-model:edges="edges" @dragover="onDragOver"
        @dragleave="onDragLeave" class="custom-node-flow" fit-view-on-init>
        <template #edge-button="buttonEdgeProps">
          <EdgeWithButton :id="buttonEdgeProps.id" :source-x="buttonEdgeProps.sourceX"
            :source-y="buttonEdgeProps.sourceY" :target-x="buttonEdgeProps.targetX" :target-y="buttonEdgeProps.targetY"
            :source-position="buttonEdgeProps.sourcePosition" :target-position="buttonEdgeProps.targetPosition"
            :marker-end="buttonEdgeProps.markerEnd" :style="buttonEdgeProps.style" />
        </template>
        <template #node-card="props">
          <CardNode :id="props.id" @delfn="removeNode" @copyfn="copynode" @initfn="initNodes" @checktypefn="checktype"
            @opendrawerfn="opendrawer" @opentscfn="opentsc" @changespace_varsname="changespace_varsname"
            @node_run_debug="node_run_debugfn" :space_vars="curspace_vars" :llmlist="llmlist" :edges="edges"
            :nodes="nodes" :data="props.data" :splist="splist" :textlist="textlist" :excellist="excellist"
            :funclist="funclist" :navlist="navlist" />
        </template>
        <!-- <Background bg-color="#F6FAFD" /> gap背景点的间距-->
        <Background pattern-color="#F6FAFD" :gap="0" />
        <Controls position="right-bottom" />
      </VueFlow>
    </div>
  </div>

  <el-drawer v-model="isShowFuncdialog" class="c-drawer-box" :title="curNodeData ? curTitle : ''" size="600px">
    <div style="margin:0 4px 10px 4px;text-align: left;" class="filterfuncTextbox">
      <el-input v-if="curNodeData.type == 0" clearable v-model="filterfuncText" placeholder="搜索" />
    </div>
    <div class="utlidialog">
      <el-scrollbar ref="scrollbarlog">
        <div style="margin:0 20px;">
          <div v-if="curNodeData.type == 0" class="itembox utilbox">
            <!-- 选择工具 -->

            <div v-for="item in getFunclist()" class="item" @click="checkItem(item)" :class="{ on: isChecked(item) }">
              <div class="name">{{ item.name }}</div>
              <div class="desc">{{ item.desc }}</div>
              <span v-if="isChecked(item)" class="iconfont icon-xuanzhong"></span>
            </div>

            <div class="utilboxtitle">
              工具流工具 <span class="c-tips">(工作流被设置为工具 )</span>
            </div>

            <div class="c-empty" v-if="getFunclist('flow').length < 1">
              暂无数据
            </div>

            <div v-for="item in getFunclist('flow')" class="item" @click="checkItem(item)"
              :class="{ on: isChecked(item) }">
              <div class="name">{{ item.name }}</div>
              <div class="desc">{{ item.desc }}</div>
              <span v-if="isChecked(item)" class="iconfont icon-xuanzhong"></span>
            </div>

            <div class="utilboxtitle">
              API工具 <span class="c-tips">(启用的API工具插件 )</span>
            </div>

            <div class="c-empty" v-if="getFunclist('plugin', 'plugin').length < 1">
              暂无数据
            </div>

            <div v-for="item in getFunclist('plugin', 'plugin')" class="item" @click="checkItem(item)"
              :class="{ on: isChecked(item) }">
              <div class="name">{{ item.name }}</div>
              <div class="desc">{{ item.desc }}</div>
              <span v-if="isChecked(item)" class="iconfont icon-xuanzhong"></span>
            </div>

            <div class="utilboxtitle">
              MCP工具 <span class="c-tips">(MCP工具插件)</span>
            </div>

            <div class="c-empty" v-if="getFunclist('plugin', 'mcp').length < 1">
              暂无数据
            </div>

            <div v-for="item in getFunclist('plugin', 'mcp')" class="item" @click="checkItem(item)"
              :class="{ on: isChecked(item) }">
              <div class="name">{{ item.name }}</div>
              <div class="desc">{{ item.desc }}</div>
              <span v-if="isChecked(item)" class="iconfont icon-xuanzhong"></span>
            </div>




          </div>

          <div v-else-if="getValByKey(curNodeData.type, 'dataType') == 'tool'" class="itembox product_searchbox">
            <!-- 文档检索工具配置 -->
            <el-form class="tl" :model="xlform" label-position="top" inline label-width="auto">
              <el-form-item style="width: 100%;margin-right: 0;" label="">
                <template #label> <span style="font-weight: bold;">工具描述</span> </template>
                <el-input style="width: calc(100% - 27px)" v-model="xlform.description"
                  :placeholder="getValByKey(curNodeData.type, 'description')" type="text" />
                <span @click="
                  xlform.description = getValByKey(
                    curNodeData.type,
                    'description'
                  )
                  " title="恢复默认值" style="margin-left: 10px" class="iconfont icon-huifumorenzhi c-pointer"></span>
              </el-form-item>

              <div v-if="curNodeData.type == 'printer_consumable_retrieve'" class="c-cardspacebox">
                <div class="ctitle">model参数</div>
                <div class="citem">
                  <div class="label">描述</div>
                  <div class="valuebox" style="width:100%">
                    <el-input v-model="xlform.model_desc" :placeholder="getValByKey(curNodeData.type, 'model_desc')"
                      type="text" style="width: calc(100% - 27px)" />

                    <span @click="xlform.model_desc = getValByKey(
                      curNodeData.type,
                      'model_desc'
                    )" title="恢复默认值" style="margin-left: 10px" class="iconfont icon-huifumorenzhi c-pointer"></span>
                  </div>
                </div>
                <div class="citem">
                  <div class="label">值</div>
                  <div :style="'height: 60px; width: 100%;z-index: 17'">
                    <Editor :nodes="nodes" :edges="edges" :nodeid="nodeid" v-model="xlform.model"></Editor>
                  </div>
                </div>
              </div>

              <template v-if="curNodeData.type == 'knowledge_add'">
                <div class="c-cardspacebox">
                  <div class="ctitle">knowledgebase_id参数</div>
                  <div class="citem">
                    <div class="label">描述</div>
                    <div class="valuebox" style="width:100%">
                      <el-input v-model="xlform.knowledgebase_id_desc"
                        :placeholder="getValByKey(curNodeData.type, 'knowledgebase_id_desc')" type="text"
                        style="width: calc(100% - 27px)" />
                      <span @click="xlform.knowledgebase_id_desc = getValByKey(
                        curNodeData.type,
                        'knowledgebase_id_desc'
                      )" title="恢复默认值" style="margin-left: 10px" class="iconfont icon-huifumorenzhi c-pointer"></span>
                    </div>
                  </div>
                  <div class="citem">
                    <div class="label">值</div>
                    <div :style="'height: 60px; width: 100%;z-index: 50'">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="nodeid" v-model="xlform.knowledgebase_id"></Editor>
                    </div>
                  </div>
                </div>


                <div class="c-cardspacebox">
                  <div class="ctitle">category_id参数</div>
                  <div class="citem">
                    <div class="label">描述</div>
                    <div class="valuebox" style="width:100%">
                      <el-input v-model="xlform.category_id_desc"
                        :placeholder="getValByKey(curNodeData.type, 'category_id_desc')" type="text"
                        style="width: calc(100% - 27px)" />
                      <span @click="xlform.category_id_desc = getValByKey(
                        curNodeData.type,
                        'category_id_desc'
                      )" title="恢复默认值" style="margin-left: 10px" class="iconfont icon-huifumorenzhi c-pointer"></span>
                    </div>
                  </div>
                  <div class="citem">
                    <div class="label">值</div>
                    <div :style="'height: 60px; width: 100%;z-index: 49'">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="nodeid" v-model="xlform.category_id"></Editor>
                    </div>
                  </div>
                </div>

                <div class="c-cardspacebox">
                  <div class="ctitle">title参数</div>
                  <div class="citem">
                    <div class="label">描述</div>
                    <div class="valuebox" style="width:100%">
                      <el-input v-model="xlform.title_desc"
                        :placeholder="getValByKey(curNodeData.type, 'title_desc')" type="text"
                        style="width: calc(100% - 27px)" />
                      <span @click="xlform.title_desc = getValByKey(
                        curNodeData.type,
                        'title_desc'
                      )" title="恢复默认值" style="margin-left: 10px" class="iconfont icon-huifumorenzhi c-pointer"></span>
                    </div>
                  </div>
                  <div class="citem">
                    <div class="label">值</div>
                    <div :style="'height: 60px; width: 100%;z-index: 48'">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="nodeid" v-model="xlform.title"></Editor>
                    </div>
                  </div>
                </div>

                <div class="c-cardspacebox">
                  <div class="ctitle">content参数</div>
                  <div class="citem">
                    <div class="label">描述</div>
                    <div class="valuebox" style="width:100%">
                      <el-input v-model="xlform.content_desc"
                        :placeholder="getValByKey(curNodeData.type, 'content_desc')" type="text"
                        style="width: calc(100% - 27px)" />
                      <span @click="xlform.content_desc = getValByKey(
                        curNodeData.type,
                        'content_desc'
                      )" title="恢复默认值" style="margin-left: 10px" class="iconfont icon-huifumorenzhi c-pointer"></span>
                    </div>
                  </div>
                  <div class="citem">
                    <div class="label">值</div>
                    <div :style="'height: 60px; width: 100%;z-index: 47'">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="nodeid" v-model="xlform.content"></Editor>
                    </div>
                  </div>
                </div>


              </template>

              <template v-if="curNodeData.type == 'flow_node_logs'">
                <div class="c-cardspacebox">
                  <div class="ctitle">flow_id参数</div>
                  <div class="citem">
                    <div class="label">描述</div>
                    <div class="valuebox" style="width:100%">
                      <el-input v-model="xlform.flow_id_desc"
                        :placeholder="getValByKey(curNodeData.type, 'flow_id_desc')" type="text"
                        style="width: calc(100% - 27px)" />
                      <span @click="xlform.flow_id_desc = getValByKey(
                        curNodeData.type,
                        'flow_id_desc'
                      )" title="恢复默认值" style="margin-left: 10px" class="iconfont icon-huifumorenzhi c-pointer"></span>
                    </div>
                  </div>
                  <div class="citem">
                    <div class="label">值</div>
                    <div :style="'height: 60px; width: 100%;z-index: 50'">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="nodeid" v-model="xlform.flow_id"></Editor>
                    </div>
                  </div>
                </div>


                <div class="c-cardspacebox">
                  <div class="ctitle">role_id参数</div>
                  <div class="citem">
                    <div class="label">描述</div>
                    <div class="valuebox" style="width:100%">
                      <el-input v-model="xlform.role_id_desc"
                        :placeholder="getValByKey(curNodeData.type, 'role_id_desc')" type="text"
                        style="width: calc(100% - 27px)" />
                      <span @click="xlform.role_id_desc = getValByKey(
                        curNodeData.type,
                        'role_id_desc'
                      )" title="恢复默认值" style="margin-left: 10px" class="iconfont icon-huifumorenzhi c-pointer"></span>
                    </div>
                  </div>
                  <div class="citem">
                    <div class="label">值</div>
                    <div :style="'height: 60px; width: 100%;z-index: 49'">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="nodeid" v-model="xlform.role_id"></Editor>
                    </div>
                  </div>
                </div>

                <div class="c-cardspacebox">
                  <div class="ctitle">start_time参数</div>
                  <div class="citem">
                    <div class="label">描述</div>
                    <div class="valuebox" style="width:100%">
                      <el-input v-model="xlform.start_time_desc"
                        :placeholder="getValByKey(curNodeData.type, 'start_time_desc')" type="text"
                        style="width: calc(100% - 27px)" />
                      <span @click="xlform.start_time_desc = getValByKey(
                        curNodeData.type,
                        'start_time_desc'
                      )" title="恢复默认值" style="margin-left: 10px" class="iconfont icon-huifumorenzhi c-pointer"></span>
                    </div>
                  </div>
                  <div class="citem">
                    <div class="label">值</div>
                    <div :style="'height: 60px; width: 100%;z-index: 48'">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="nodeid" v-model="xlform.start_time"></Editor>
                    </div>
                  </div>
                </div>

                <div class="c-cardspacebox">
                  <div class="ctitle">end_time参数</div>
                  <div class="citem">
                    <div class="label">描述</div>
                    <div class="valuebox" style="width:100%">
                      <el-input v-model="xlform.end_time_desc"
                        :placeholder="getValByKey(curNodeData.type, 'end_time_desc')" type="text"
                        style="width: calc(100% - 27px)" />
                      <span @click="xlform.end_time_desc = getValByKey(
                        curNodeData.type,
                        'end_time_desc'
                      )" title="恢复默认值" style="margin-left: 10px" class="iconfont icon-huifumorenzhi c-pointer"></span>
                    </div>
                  </div>
                  <div class="citem">
                    <div class="label">值</div>
                    <div :style="'height: 60px; width: 100%;z-index: 47'">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="nodeid" v-model="xlform.end_time"></Editor>
                    </div>
                  </div>
                </div>

                <div class="c-cardspacebox">
                  <div class="ctitle">max_top_n参数</div>
                  <div class="citem">
                    <div class="label">描述</div>
                    <div class="valuebox" style="width:100%">
                      <el-input v-model="xlform.max_top_n_desc"
                        :placeholder="getValByKey(curNodeData.type, 'max_top_n_desc')" type="text"
                        style="width: calc(100% - 27px)" />
                      <span @click="xlform.max_top_n_desc = getValByKey(
                        curNodeData.type,
                        'max_top_n_desc'
                      )" title="恢复默认值" style="margin-left: 10px" class="iconfont icon-huifumorenzhi c-pointer"></span>
                    </div>
                  </div>
                  <div class="citem">
                    <div class="label">值</div>
                    <div :style="'height: 60px; width: 100%;z-index: 36'">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="nodeid" v-model="xlform.max_top_n"></Editor>
                    </div>
                  </div>
                </div>



              </template>



              <template v-if="curNodeData.type == 'train_case_add'">
                <div class="c-cardspacebox">
                  <div class="ctitle">train_cate_id参数</div>
                  <div class="citem">
                    <div class="label">描述</div>
                    <div class="valuebox" style="width:100%">
                      <el-input v-model="xlform.train_cate_id_desc"
                        :placeholder="getValByKey(curNodeData.type, 'train_cate_id_desc')" type="text"
                        style="width: calc(100% - 27px)" />
                      <span @click="xlform.train_cate_id_desc = getValByKey(
                        curNodeData.type,
                        'train_cate_id_desc'
                      )" title="恢复默认值" style="margin-left: 10px" class="iconfont icon-huifumorenzhi c-pointer"></span>
                    </div>
                  </div>
                  <div class="citem">
                    <div class="label">值</div>
                    <div :style="'height: 60px; width: 100%;z-index: 40'">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="nodeid" v-model="xlform.train_cate_id"></Editor>
                    </div>
                  </div>
                </div>


                <div class="c-cardspacebox">
                  <div class="ctitle">input_content参数</div>
                  <div class="citem">
                    <div class="label">描述</div>
                    <div class="valuebox" style="width:100%">
                      <el-input v-model="xlform.input_content_desc"
                        :placeholder="getValByKey(curNodeData.type, 'input_content_desc')" type="text"
                        style="width: calc(100% - 27px)" />
                      <span @click="xlform.input_content_desc = getValByKey(
                        curNodeData.type,
                        'input_content_desc'
                      )" title="恢复默认值" style="margin-left: 10px" class="iconfont icon-huifumorenzhi c-pointer"></span>
                    </div>
                  </div>
                  <div class="citem">
                    <div class="label">值</div>
                    <div :style="'height: 60px; width: 100%;z-index: 39'">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="nodeid" v-model="xlform.input_content"></Editor>
                    </div>
                  </div>
                </div>

                <div class="c-cardspacebox">
                  <div class="ctitle">output_contet参数</div>
                  <div class="citem">
                    <div class="label">描述</div>
                    <div class="valuebox" style="width:100%">
                      <el-input v-model="xlform.output_contet_desc"
                        :placeholder="getValByKey(curNodeData.type, 'output_contet_desc')" type="text"
                        style="width: calc(100% - 27px)" />
                      <span @click="xlform.output_contet_desc = getValByKey(
                        curNodeData.type,
                        'output_contet_desc'
                      )" title="恢复默认值" style="margin-left: 10px" class="iconfont icon-huifumorenzhi c-pointer"></span>
                    </div>
                  </div>
                  <div class="citem">
                    <div class="label">值</div>
                    <div :style="'height: 60px; width: 100%;z-index: 38'">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="nodeid" v-model="xlform.output_contet"></Editor>
                    </div>
                  </div>
                </div>

                <div class="c-cardspacebox">
                  <div class="ctitle">feature参数</div>
                  <div class="citem">
                    <div class="label">描述</div>
                    <div class="valuebox" style="width:100%">
                      <el-input v-model="xlform.feature_desc"
                        :placeholder="getValByKey(curNodeData.type, 'feature_desc')" type="text"
                        style="width: calc(100% - 27px)" />
                      <span @click="xlform.feature_desc = getValByKey(
                        curNodeData.type,
                        'feature_desc'
                      )" title="恢复默认值" style="margin-left: 10px" class="iconfont icon-huifumorenzhi c-pointer"></span>
                    </div>
                  </div>
                  <div class="citem">
                    <div class="label">值</div>
                    <div :style="'height: 60px; width: 100%;z-index: 37'">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="nodeid" v-model="xlform.feature"></Editor>
                    </div>
                  </div>
                </div>

                <div class="c-cardspacebox">
                  <div class="ctitle">node_log_id参数</div>
                  <div class="citem">
                    <div class="label">描述</div>
                    <div class="valuebox" style="width:100%">
                      <el-input v-model="xlform.node_log_id_desc"
                        :placeholder="getValByKey(curNodeData.type, 'node_log_id_desc')" type="text"
                        style="width: calc(100% - 27px)" />
                      <span @click="xlform.node_log_id_desc = getValByKey(
                        curNodeData.type,
                        'node_log_id_desc'
                      )" title="恢复默认值" style="margin-left: 10px" class="iconfont icon-huifumorenzhi c-pointer"></span>
                    </div>
                  </div>
                  <div class="citem">
                    <div class="label">值</div>
                    <div :style="'height: 60px; width: 100%;z-index: 36'">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="nodeid" v-model="xlform.node_log_id"></Editor>
                    </div>
                  </div>
                </div>

                <div class="c-cardspacebox">
                  <div class="ctitle">test_case_id参数</div>
                  <div class="citem">
                    <div class="label">描述</div>
                    <div class="valuebox" style="width:100%">
                      <el-input v-model="xlform.test_case_id_desc"
                        :placeholder="getValByKey(curNodeData.type, 'test_case_id_desc')" type="text"
                        style="width: calc(100% - 27px)" />
                      <span @click="xlform.test_case_id_desc = getValByKey(
                        curNodeData.type,
                        'test_case_id_desc'
                      )" title="恢复默认值" style="margin-left: 10px" class="iconfont icon-huifumorenzhi c-pointer"></span>
                    </div>
                  </div>
                  <div class="citem">
                    <div class="label">值</div>
                    <div :style="'height: 60px; width: 100%;z-index: 35'">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="nodeid" v-model="xlform.test_case_id"></Editor>
                    </div>
                  </div>
                </div>

              </template>


              <template v-if="curNodeData.type == 'unit_test_add'">
                <div class="c-cardspacebox">
                  <div class="ctitle">unit_cate_id参数</div>
                  <div class="citem">
                    <div class="label">描述</div>
                    <div class="valuebox" style="width:100%">
                      <el-input v-model="xlform.unit_cate_id_desc"
                        :placeholder="getValByKey(curNodeData.type, 'unit_cate_id_desc')" type="text"
                        style="width: calc(100% - 27px)" />
                      <span @click="xlform.unit_cate_id_desc = getValByKey(
                        curNodeData.type,
                        'unit_cate_id_desc'
                      )" title="恢复默认值" style="margin-left: 10px" class="iconfont icon-huifumorenzhi c-pointer"></span>
                    </div>
                  </div>
                  <div class="citem">
                    <div class="label">值</div>
                    <div :style="'height: 60px; width: 100%;z-index: 30'">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="nodeid" v-model="xlform.unit_cate_id"></Editor>
                    </div>
                  </div>
                </div>


                <div class="c-cardspacebox">
                  <div class="ctitle">node_log_id参数</div>
                  <div class="citem">
                    <div class="label">描述</div>
                    <div class="valuebox" style="width:100%">
                      <el-input v-model="xlform.node_log_id_desc"
                        :placeholder="getValByKey(curNodeData.type, 'node_log_id_desc')" type="text"
                        style="width: calc(100% - 27px)" />
                      <span @click="xlform.node_log_id_desc = getValByKey(
                        curNodeData.type,
                        'node_log_id_desc'
                      )" title="恢复默认值" style="margin-left: 10px" class="iconfont icon-huifumorenzhi c-pointer"></span>
                    </div>
                  </div>
                  <div class="citem">
                    <div class="label">值</div>
                    <div :style="'height: 60px; width: 100%;z-index: 29'">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="nodeid" v-model="xlform.node_log_id"></Editor>
                    </div>
                  </div>
                </div>

                <div class="c-cardspacebox">
                  <div class="ctitle">test_note参数</div>
                  <div class="citem">
                    <div class="label">描述</div>
                    <div class="valuebox" style="width:100%">
                      <el-input v-model="xlform.test_note_desc"
                        :placeholder="getValByKey(curNodeData.type, 'test_note_desc')" type="text"
                        style="width: calc(100% - 27px)" />
                      <span @click="xlform.test_note_desc = getValByKey(
                        curNodeData.type,
                        'test_note_desc'
                      )" title="恢复默认值" style="margin-left: 10px" class="iconfont icon-huifumorenzhi c-pointer"></span>
                    </div>
                  </div>
                  <div class="citem">
                    <div class="label">值</div>
                    <div :style="'height: 60px; width: 100%;z-index: 29'">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="nodeid" v-model="xlform.test_note"></Editor>
                    </div>
                  </div>
                </div>

              </template>

              <template v-if="curNodeData.type == 'knowledge_append'">
                <div class="c-cardspacebox">
                  <div class="ctitle">doucument_id参数</div>
                  <div class="citem">
                    <div class="label">描述</div>
                    <div class="valuebox" style="width:100%">
                      <el-input v-model="xlform.doucument_id_desc"
                        :placeholder="getValByKey(curNodeData.type, 'doucument_id_desc')" type="text"
                        style="width: calc(100% - 27px)" />
                      <span @click="xlform.doucument_id_desc = getValByKey(
                        curNodeData.type,
                        'doucument_id_desc'
                      )" title="恢复默认值" style="margin-left: 10px" class="iconfont icon-huifumorenzhi c-pointer"></span>
                    </div>
                  </div>
                  <div class="citem">
                    <div class="label">值</div>
                    <div :style="'height: 60px; width: 100%;z-index: 20'">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="nodeid" v-model="xlform.doucument_id"></Editor>
                    </div>
                  </div>
                </div>


                <div class="c-cardspacebox">
                  <div class="ctitle">content参数</div>
                  <div class="citem">
                    <div class="label">描述</div>
                    <div class="valuebox" style="width:100%">
                      <el-input v-model="xlform.content_desc"
                        :placeholder="getValByKey(curNodeData.type, 'content_desc')" type="text"
                        style="width: calc(100% - 27px)" />
                      <span @click="xlform.content_desc = getValByKey(
                        curNodeData.type,
                        'content_desc'
                      )" title="恢复默认值" style="margin-left: 10px" class="iconfont icon-huifumorenzhi c-pointer"></span>
                    </div>
                  </div>
                  <div class="citem">
                    <div class="label">值</div>
                    <div :style="'height: 60px; width: 100%;z-index: 20'">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="nodeid" v-model="xlform.content"></Editor>
                    </div>
                  </div>
                </div>
              </template>

              <div v-if="curNodeData.type == 'calculator'" class="c-cardspacebox">
                <div class="ctitle">expression参数</div>
                <div class="citem">
                  <div class="label">描述</div>
                  <div class="valuebox" style="width:100%">
                    <el-input v-model="xlform.expression_desc"
                      :placeholder="getValByKey(curNodeData.type, 'expression_desc')" type="text"
                      style="width: calc(100% - 27px)" />
                    <span @click="xlform.expression_desc = getValByKey(
                      curNodeData.type,
                      'expression_desc'
                    )" title="恢复默认值" style="margin-left: 10px" class="iconfont icon-huifumorenzhi c-pointer"></span>
                  </div>
                </div>
                <div class="citem">
                  <div class="label">值</div>
                  <div :style="'height: 60px; width: 100%;z-index: 16'">
                    <Editor :nodes="nodes" :edges="edges" :nodeid="nodeid" v-model="xlform.expression"></Editor>
                  </div>
                </div>
              </div>




              <template v-if="curNodeData.type == 'vectorstore_retrieve'">

                <div class="c-cardspacebox">
                  <div class="ctitle">querys参数</div>
                  <div class="citem">
                    <div class="label">描述</div>
                    <div class="valuebox" style="width:100%">
                      <el-input v-model="xlform.querys_desc" :placeholder="getValByKey(curNodeData.type, 'querys_desc')"
                        type="text" style="width: calc(100% - 27px)" />
                      <span @click="xlform.querys_desc = getValByKey(
                        curNodeData.type,
                        'querys_desc'
                      )" title="恢复默认值" style="margin-left: 10px" class="iconfont icon-huifumorenzhi c-pointer"></span>
                    </div>
                  </div>
                  <div class="citem">
                    <div class="label">值</div>
                    <div :style="'height: 60px; width: 100%;z-index: 15'">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="nodeid" v-model="xlform.querys"></Editor>
                    </div>
                  </div>
                </div>

                <div class="c-cardspacebox">
                  <div class="ctitle">brands参数</div>
                  <div class="citem">
                    <div class="label">描述</div>
                    <div class="valuebox" style="width:100%">
                      <el-input v-model="xlform.brands_desc" :placeholder="msmap[3]" type="text"
                        style="width: calc(100% - 27px)" />
                      <span @click="xlform.brands_desc = msmap[3]" title="恢复默认值" style="margin-left: 10px"
                        class="iconfont icon-huifumorenzhi c-pointer"></span>
                    </div>
                  </div>
                  <div class="citem">
                    <div class="label">值</div>
                    <div :style="'height: 60px; width: 100%;z-index: 14'">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="nodeid" v-model="xlform.brands"></Editor>
                    </div>
                  </div>
                </div>

              </template>


              <template v-if="curNodeData.type == 'product_retrieve'">

                <div class="c-cardspacebox">
                  <div class="ctitle">querys参数</div>
                  <div class="citem">
                    <div class="label">描述</div>
                    <div class="valuebox" style="width:100%">
                      <el-input v-model="xlform.querys_desc" :placeholder="getValByKey(curNodeData.type, 'querys_desc')"
                        type="text" style="width: calc(100% - 27px)" />
                      <span @click="xlform.querys_desc = getValByKey(
                        curNodeData.type,
                        'querys_desc'
                      )" title="恢复默认值" style="margin-left: 10px" class="iconfont icon-huifumorenzhi c-pointer"></span>
                    </div>
                  </div>
                  <div class="citem">
                    <div class="label">值</div>
                    <div :style="'height: 60px; width: 100%;z-index: 15'">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="nodeid" v-model="xlform.querys"></Editor>
                    </div>
                  </div>
                </div>


                <div class="c-cardspacebox">
                  <div class="ctitle">nc_ids参数</div>
                  <div class="citem">
                    <div class="label">描述</div>
                    <div class="valuebox" style="width:100%">
                      <el-input v-model="xlform.nc_ids_desc" :placeholder="msmap[6]" type="text"
                        style="width: calc(100% - 27px)" />
                      <span @click="xlform.nc_ids_desc = msmap[6]" title="恢复默认值" style="margin-left: 10px"
                        class="iconfont icon-huifumorenzhi c-pointer"></span>
                    </div>
                  </div>
                  <div class="citem">
                    <div class="label">值</div>
                    <div :style="'height: 60px; width: 100%;z-index: 14'">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="nodeid" v-model="xlform.nc_ids"></Editor>
                    </div>
                  </div>
                </div>
              </template>

              <template v-if="curNodeData.type == 'knowledge_retrieve'">

                <div class="c-cardspacebox">
                  <div class="ctitle">queries参数</div>
                  <div class="citem">
                    <div class="label">描述</div>
                    <div class="valuebox" style="width:100%">
                      <el-input style="width: calc(100% - 27px)" v-model="xlform.queries_desc"
                        :placeholder="getValByKey(curNodeData.type, 'queries_desc')" type="text" />
                      <span @click="
                        xlform.queries_desc = getValByKey(
                          curNodeData.type,
                          'queries_desc'
                        )
                        " title="恢复默认值" style="margin-left: 10px" class="iconfont icon-huifumorenzhi c-pointer"></span>
                    </div>
                  </div>
                  <div class="citem">
                    <div class="label">值</div>
                    <div :style="'height: 60px; width: 100%;z-index: 13'">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="nodeid" v-model="xlform.queries"></Editor>
                    </div>
                  </div>
                </div>


                <div class="c-cardspacebox">
                  <div class="ctitle">tags参数</div>
                  <div class="citem">
                    <div class="label">描述</div>
                    <div class="valuebox" style="width:100%">
                      <el-input style="width: calc(100% - 27px)" v-model="xlform.tags_desc"
                        :placeholder="getValByKey(curNodeData.type, 'tags_desc')" type="text" />
                      <span @click="
                        xlform.tags_desc = getValByKey(
                          curNodeData.type,
                          'tags_desc'
                        )
                        " title="恢复默认值" style="margin-left: 10px" class="iconfont icon-huifumorenzhi c-pointer"></span>
                    </div>
                  </div>
                  <div class="citem">
                    <div class="label">值</div>
                    <div :style="'height: 60px; width: 100%;z-index: 12'">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="nodeid" v-model="xlform.tags"></Editor>
                    </div>
                  </div>
                </div>


                <div class="c-cardspacebox">
                  <div class="ctitle">ids参数</div>
                  <div class="citem">
                    <div class="label">描述</div>
                    <div class="valuebox" style="width:100%">
                      <el-input style="width: calc(100% - 27px)" v-model="xlform.ids_desc"
                        :placeholder="getValByKey(curNodeData.type, 'ids_desc')" type="text" />
                      <span @click="
                        xlform.ids_desc = getValByKey(
                          curNodeData.type,
                          'ids_desc'
                        )
                        " title="恢复默认值" style="margin-left: 10px" class="iconfont icon-huifumorenzhi c-pointer"></span>
                    </div>
                  </div>
                  <div class="citem">
                    <div class="label">值</div>
                    <div :style="'height: 60px; width: 100%;z-index: 11'">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="nodeid" v-model="xlform.ids"></Editor>
                    </div>
                  </div>
                </div>



              </template>





              <el-form-item style="width: calc(50% - 8px);margin-right: 16px;"
                v-if="xlform.doc_knowledge_base_ids !== undefined" label="文档知识库">
                <el-select v-model="xlform.doc_knowledge_base_ids" multiple collapse-tags :max-collapse-tags="2"
                  placeholder="请选择知识库">
                  <el-option v-for="item in textlist" :key="item.id" :label="item.name" :value="item.id" />
                </el-select>
              </el-form-item>
              <el-form-item style="width: calc(50% - 8px);margin-right: 0px;" v-if="xlform.doc_top_k !== undefined"
                label="文档知识库召回文本数">
                <el-input-number style="width: 100%" placeholder="请填写文本召回文本数" v-model="xlform.doc_top_k" :min="0"
                  :max="20" :precision="0" :step="1" controls-position="right" /><span v-show="xlform.doc_top_k > 5"
                  class="c-danger">文本数太多，可能会影响大模型token数超出限制</span>
              </el-form-item>

              <!-- <el-form-item style="width: calc(50% - 8px);margin-right: 16px;"
                v-if="xlform.product_knowledge_base_ids !== undefined" label="产品知识库">
                <el-select v-model="xlform.product_knowledge_base_ids" multiple collapse-tags :max-collapse-tags="2" placeholder="请选择商品知识库">
                  <el-option v-for="item in splist" :key="item.id" :label="item.name" :value="item.id" />
                </el-select>
              </el-form-item>
              <el-form-item style="width: calc(50% - 8px);margin-right: 0px;" v-if="xlform.product_top_k !== undefined"
                label="产品知识库召回文本数">
                <el-input-number style="width: 100%" v-model="xlform.product_top_k" placeholder="请填写商品召回文本数" :min="0"
                  :max="20" :precision="0" :step="1" controls-position="right" />
                <span v-show="xlform.product_top_k > 5" class="c-danger">文本数太多，可能会影响大模型token数超出限制</span>
              </el-form-item> -->


              <el-form-item style="width: calc(50% - 8px);margin-right: 16px;"
                v-if="xlform.excel_knowledge_base_ids !== undefined" label="EXCEL参数库">
                <el-select v-model="xlform.excel_knowledge_base_ids" multiple collapse-tags :max-collapse-tags="2"
                  placeholder="请选择EXCEL参数库">
                  <el-option v-for="item in excellist" :key="item.id" :label="item.name" :value="item.id" />
                </el-select>
              </el-form-item>
              <el-form-item style="width: calc(50% - 8px);margin-right: 0px;" v-if="xlform.excel_top_k !== undefined"
                label="EXCEL参数库召回文本数">
                <el-input-number style="width: 100%" placeholder="请填写EXCEL参数库召回文本数" v-model="xlform.excel_top_k"
                  :min="0" :max="20" :precision="0" :step="1" controls-position="right" /><span
                  v-show="xlform.excel_top_k > 5" class="c-danger">文本数太多，可能会影响大模型token数超出限制</span>
              </el-form-item>

              <el-form-item style="width: calc(50% - 8px);margin-right: 16px;" v-if="xlform.top_k !== undefined"
                label="召回文本数">
                <el-input-number style="width: 100%" placeholder="请填写召回文本数" v-model="xlform.top_k" :min="0" :max="20"
                  :precision="0" :step="1" controls-position="right" /><span v-show="xlform.top_k > 5"
                  class="c-danger">文本数太多，可能会影响大模型token数超出限制</span>
              </el-form-item>

              <div v-if="xlform.metadata_filter !== undefined" class="cardbox">
                <div style="margin-bottom: 16px;" class="itembox">
                  <div class="ltitle">
                    <span :class="{ off: ismetadata_filter }" @click.stop="ismetadata_filter = !ismetadata_filter"
                      class="iconfont icon-xiajiantou pointer"></span> <span
                      class="iconfont icon-keyonggongju"></span>元数据过滤
                    <span class="fr">


                      <span class="addvarbtn" @click="
                        xlform.metadata_filter.push({
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
                        !(xlform && xlform.metadata_filter.length > 0)
                      " class="c-emptybox">
                        暂无数据
                      </div>

                      <div v-if="
                        (xlform && xlform.metadata_filter.length > 0)
                      " class="item" v-for="(item, index) in xlform.metadata_filter">
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
                                xlform.metadata_filter.splice(index, 1);
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
              </div>



              <el-form-item style="width: calc(50% - 8px);margin-right: 0px;" v-if="xlform.output_option !== undefined"
                label="输出格式">
                <el-radio-group v-model="xlform.output_option">
                  <el-radio value="json">输出json格式内容</el-radio>
                  <el-radio value="markdown">输出markdown内容</el-radio>
                </el-radio-group>
              </el-form-item>

              <el-form-item style="width: 100%;margin-right: 0px;" v-if="xlform.filter_value !== undefined"
                label="评分过滤值">
                <el-slider style="width: 300px" v-model="xlform.filter_value" :step="0.05" :min="0" :max="1" />
                <span v-show="xlform.filter_value > 0.5" class="c-danger">过滤分数过高，可能会影响召回文档数</span>
              </el-form-item>


            </el-form>
          </div>

          <div v-else-if="flowtestform.type == 'plugin'" class="itembox flowbox">
            <el-form ref="formflowRef" :model="flowtestform" label-width="auto" label-position="top" inline
              class="demo-dynamic tl">
              <el-form-item style="width: 100%;margin-right: 0;" label="">
                <template #label> <span style="font-weight: bold;">工具描述</span> </template>
                <el-input style="width: calc(100%)" v-model="flowtestform.caption" disabled type="text" />
              </el-form-item>
              <el-form-item style="width: 100%;margin-right: 0px;" v-if="isShowFuncdialog && flowtestform.inputs"
                v-for="(item, index) in flowtestform.inputs" :key="item.key">
                <div class="c-cardspacebox">
                  <div class="ctitle">{{ item.name }}参数<span v-if="item.is_required" class="require">*</span> <span
                      class="type">{{ item.data_type }}</span></div>
                  <div class="citem">
                    <div class="label">描述</div>
                    <el-input style="width: 100%" disabled v-model="item.caption" type="text" />
                  </div>
                  <div class="citem">
                    <div class="label">值</div>
                    <div :style="'height: 60px; width: 100%;z-index: ' + (1000 - index)">
                      <Editor :nodes="nodes" :edges="edges" :nodeid="nodeid" v-model="item.curvalue"></Editor>
                    </div>
                  </div>
                </div>

              </el-form-item>
              <el-form-item style="width: 100%;margin-right: 0px;" v-if="flowtestform.output_option !== undefined"
                label="输出格式">
                <el-radio-group v-model="flowtestform.output_option">
                  <el-radio value="markdown">输出markdown内容</el-radio>
                  <el-radio value="json">输出json格式内容</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-form>
          </div>

          <div v-else class="itembox flowbox">
            <div class="testbox">
              <div class="testbody">
                <el-form style="margin: 0px 20px;text-align: left;" ref="formflowRef" :model="flowtestform"
                  label-width="auto" label-position="top" inline class="demo-dynamic">

                  <el-form-item style="width: 100%;margin-right: 0;" label="">
                    <template #label> <span style="font-weight: bold;">工具描述</span> </template>
                    <el-input style="width: calc(100%)" v-model="flowtestform.caption" disabled type="text" />
                  </el-form-item>

                  <el-form-item style="width: 100%;margin-right: 0px;" v-if="isShowFuncdialog && flowtestform.inputs"
                    v-for="(item, index) in flowtestform.inputs" :key="item.key"
                    :prop="'inputs[' + index + '].curvalue'">


                    <div class="c-cardspacebox">
                      <div class="ctitle">{{ item.name }}参数<span v-if="item.is_required" class="require">*</span> <span
                          class="type">{{ item.data_type }}</span></div>
                      <div class="citem">
                        <div class="label">描述</div>
                        <el-input style="width: 100%" disabled v-model="item.desc" type="text" />
                      </div>
                      <div class="citem">
                        <div class="label">值</div>
                        <div :style="'height: 60px; width: 100%;z-index: ' + (1000 - index)">
                          <Editor :nodes="nodes" :edges="edges" :nodeid="nodeid" v-model="item.curvalue"></Editor>
                        </div>
                      </div>
                    </div>
                  </el-form-item>
                </el-form>
              </div>
            </div>
          </div>
        </div>
      </el-scrollbar>
    </div>
    <div class="dialog-footer">
      <el-button @click="isShowFuncdialog = false" plain> 取消 </el-button>
      <el-button type="primary" @click="subfn(formflowRef)"> 保存 </el-button>
    </div>
  </el-drawer>
  <!-- <v-md-preview :text="curResult.prompt_str"></v-md-preview> -->

  <el-drawer v-model="showPrompt" :close-on-click-modal="true" size="780px" title="运行结果" direction="rtl">
    <div style="margin:0 -16px;height:100%;">
      <el-scrollbar>
        <v-md-preview :text="curshowPrompt"></v-md-preview>
      </el-scrollbar>
    </div>
  </el-drawer>


  <div v-if="route.path == '/flowshare'" class="sharebg"></div>
  <div class="sharepage c-sharepage" v-if="route.path == '/flowshare'">
    <div class="meslist">
      <el-scrollbar ref="shareScroll">
        <div v-for="(item, index) in sharelist" :key="index" class="item" :class="{
          lbox: item.type == 1,
          rbox: item.type == 2,
          ['js-' + item.id]: true,
          active: dialogFormVisibleid == item.id,
        }">
          <div class="mes">
            <span @click="copymesfn(item.mes)" class="iconfontbox">
              <icon v-if="item.type == 2" type="userphone" width="30" height="30"></icon>
              <icon v-if="item.type == 1" type="jiqiren" width="30" height="30"></icon>
            </span>
            <div>
              <v-md-preview :text="item.mes"></v-md-preview>
            </div>
          </div>
        </div>
        <div v-if="isLoading" class="item loadingbox">
          <div v-loading="isLoading" class="load"></div>
          <!-- 数据加载中 -->
        </div>
      </el-scrollbar>
    </div>
    <!-- 分享聊天记录 -->
  </div>

  <el-drawer v-model="showTest" :close-on-click-modal="true" :modal="route.path != '/flowshare'" :size="testSize"
    title="试运行" direction="rtl">
    <div v-show="!isShowResult" class="testbox">


      <div class="testbody">
        <el-scrollbar>
          <el-form style="margin: 0 20px;" ref="formRef" :model="testform" label-width="auto" class="demo-dynamic">
            <el-form-item v-for="(item, index) in testform.inputs" :key="item.key"
              :prop="'inputs[' + index + '].curvalue'" :rules="{
                trigger: 'blur',
                validator: validatorfn,
                row: item,
              }">

              <div class="c-cardspacebox">
                <div class="ctitle">{{ item.name }}参数<span v-if="item.is_required" class="require">*</span> <span
                    class="type">{{ item.data_type }}</span></div>
                <div :title="item.desc" class="citem">
                  <div class="label">描述</div>
                  <el-input style="width: 100%" disabled v-model="item.desc" type="text" />
                </div>
                <div class="citem">
                  <div style="display:flex;align-items: center;justify-content: space-between;" class="label">
                    <span>值</span>
                  </div>
                  <div>
                    <!-- <Editor :nodes="nodes" :edges="edges" :nodeid="nodeid" v-model="item.curvalue"></Editor> -->
                    <template v-if="item.data_type == 'File' || item.data_type == 'Array<File>'">
                      <el-upload v-if="item.constraint" class="upload-demo" v-model:file-list="item.fileList"
                        :headers="{ authorization: 'Bearer ' + store.state.token }" :action="'/api/files/upload?flow_id='+route.query.id+(route.query.api_key?'&api_key='+route.query.api_key : '')"
                        :show-file-list="true" :limit="item.constraint.max_qty" 
                        :auto-upload="true"
                        :multiple="item.constraint.max_qty > 1"
                        :on-exceed="(files, fileList) => { exceedFile(files, fileList, item) }" :on-error="errfn"
                        :on-change="(file, files) =>{item.fileList = files;sucfn({}, file, files, item);}"
                        :on-remove="(file, files) =>{item.fileList = files; sucfn({}, file, files, item);}"
                        :on-success="(res, file, files) => { sucfn(res, file, files, item); }"
                        :before-upload="(file) => { return beforeAvatarUpload(file, item); }">
                        <el-button size="small" type="primary">上传文件</el-button>
                        <template #tip>
                          <div class="el-upload__tip c-tips">
                            文件大小不能超过 {{ item.constraint.max_file_kb }}KB，
                            仅支持下列文件格式：<span v-for="citem in item.constraint.allowed_ext_types">{{ citem }}, </span>
                          </div>
                        </template>
                      </el-upload>
                      <!-- <div style="text-align: right;">
                        <el-button :disabled="item.fileList.length < 1" @click="filesuploadsfn(item)" type="success"
                          size="small">确定上传</el-button>
                      </div> -->
                    </template>
                    <template v-else-if="item.data_type == 'String'">
                      <el-input v-if="item.name == 'user_input'" :placeholder="'请输入' + item.name"
                        v-model="item.curvalue" type="textarea" :rows="6" />
                      <el-input v-else :placeholder="'请输入' + item.name" v-model="item.curvalue" />
                    </template>
                    <template v-else-if="
                      item.data_type == 'Integer' || item.data_type == 'Number'
                    ">
                      <el-input-number v-model="item.curvalue" style="width: 500px; text-align: left"
                        :placeholder="'请输入' + item.name" :controls="true" controls-position="right" size="small" />
                    </template>
                    <template v-else-if="item.data_type == 'Boolean'">
                      <el-switch v-model="item.curvalue" />
                    </template>
                    <template v-else>
                      <el-input v-model="item.curvalue" :rows="10" type="textarea" :placeholder="'请输入' + item.name" />
                    </template>
                  </div>
                </div>
              </div>


            </el-form-item>
          </el-form>
        </el-scrollbar>
      </div>
      <div class="dialog-footer">
        <el-button :disabled="workflowrunfnLoading" :loading="workflowrunfnLoading" @click="workflowrunfn(formRef)"
          type="primary">运行</el-button>
      </div>
    </div>
  </el-drawer>

  <el-drawer v-model="drawer" size="90%" title="" direction="rtl">
    <CompApp @subfn="appsubfn" :curdataid="curnodedataid" :curflowid="curflowid" :isCheck="true" :nodeid="nodeid"
      :nodes="nodes" :edges="edges" :checkList="checkList">
    </CompApp>
  </el-drawer>

  <tscEdit v-model="isShowtscEdit" @subfn="subtsc" @errfn="tscerrfn" :nodeid="nodeid" :curdataid="curnodedataid"
    :curflowid="curflowid" :nodes="nodes" :edges="edges" :item="tscEditItem"></tscEdit>

  <content title="引用内容" :curContext="curContext" v-model="dialogFormVisible1"></content>

  <template v-if="route.path != '/flowshare'">
    <result v-model="isShowResult" @change="resultChange" @btnclose="
      (type) => {
        runresult = null;
        if (type) testfn();
      }
    " :data="runresult"></result>
  </template>


</template>

<style scoped>
.selectbox {
  display: flex;
  align-items: center;
  justify-content: flex-start;
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
  padding-top: 6px;
  padding-bottom: 6px;
}

.cardbox {
  background: #fff;
  border-radius: 14px;
  border: none;
  position: relative;
  width: 100%;
  box-sizing: border-box;
  padding: 0px;
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

.navbody {
  height: calc(100% - 70px);
}

.navlisttitle {
  text-align: left;
  font-weight: bold;
  padding: 10px 15px 15px 15px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.utilboxtitle {
  font-weight: bold;
  padding: 10px 0px;
  border-bottom: 1px solid #f1f1f1;
  margin-bottom: 20px;
  font-size: 16px;
}

.utilboxtitle .c-tips {
  font-size: 12px;
  font-weight: normal;
  color: #aaa;
}

.testbox .timecontain .opensection {
  font-size: 12px;
  transition: all 0.3s;
  display: inline-block;
}

.testbox .timecontain .opensection.on {
  transform: rotate(-90deg);
}

.testbox :deep(.github-markdown-body) {
  padding: 10px 10px 0 10px;
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

.testbox .testbody {
  display: block;
  height: calc(100% - 60px);
  margin: 0 -20px;
}



.testbox .iconfont {
  cursor: pointer;
}

.testbox .btns {
  text-align: right;
}

.c-danger {
  padding-left: 20px;
}

.utlidialog {
  height: calc(100% - 90px);
  margin: 0 -16px;
}

.utilbox {
  text-align: left;
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

.utilbox .item>.iconfont.icon-xuanzhong {
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

.titlebox .icon-damoxing {
  font-size: 24px;
  font-weight: bold;
  color: #1948e7;
}

.titlebox .icon-peizhi {
  font-size: 24px;
  font-weight: bold;
  color: #19e73b;
}

.btnbox {
  display: flex;
  align-items: center;
}

.topbox {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-right: 10px;
  padding-left: 10px;
  height: 56px;
}

.topbox .back {
  padding: 5px 10px;
  display: flex;
  align-items: center;
  cursor: pointer;
  font-size: 14px;
}

.topbox .back:hover {
  color: var(--el-color-primary);
}

.topbox .back .iconfont {
  font-size: 24px;
}

.pagebox {
  display: block;
  width: 100%;
  height: 100%;
}

.flow {
  width: 100%;
  height: calc(100% - 56px);
  box-sizing: border-box;
  background: #F6FAFD;
}

.showAddbtn {
  position: absolute;
  z-index: 10;
  cursor: pointer;
  display: block;
  width: 40px;
  height: 40px;
  line-height: 40px;
  background: rgba(64, 158, 255, 0.85);
  border-radius: 100%;
  color: #fff;
  left: 24px;
  top: 80px;
}

.showAddbtn .iconfont {
  font-weight: bold;
  color: #fff;
  font-size: 28px;
  transition: all 0.3s;
  display: inline-block;
}

.showAddbtn:hover .iconfont {
  transform: rotate(360deg);
}

.navbox {
  width: 0px;
  opacity: 0;
  box-sizing: border-box;
  padding: 0px;
  position: absolute;
  left: 0;
  top: 57px;
  bottom: 600px;
  z-index: 9;
  background: #fff;
  border-right: 1px solid #f1f1f1;
  transition: all 0.3s;
}

.navbox.open {
  width: 304px;
  opacity: 1;
  bottom: 0px;
  z-index: 111;
}

.navbox .item {
  cursor: pointer;
  display: flex;
  text-align: left;
  margin: 0 16px;
  box-sizing: border-box;
  align-items: center;
  justify-content: space-between;
  font-size: 16px;
  font-weight: bold;
  border: none;
  box-shadow: none;
  padding: 12px;
  width: calc(100% - 32px);
}

.navbox .item:hover {
  background: #F6FAFD;
}

.navbox .item .ellipsis {
  max-width: 186px;
}

.navbox .item>div {
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.navbox .item .icon-liebiao-zengjia {
  color: var(--el-color-primary);
  display: none;
}

.navbox .item:hover .icon-liebiao-zengjia {
  display: block;
}

.navbox .title {
  font-weight: bold;
  padding: 10px 16px 0 16px;
  font-size: 18px;
  text-align: left;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.navbox .title>.iconfont {
  font-size: 30px;
  cursor: pointer;
}

.btns {
  display: block;
  padding: 20px 40px;
  text-align: center;
}

.custom-node {
  border: 1px solid #333;
  padding: 10px;
  border-radius: 5px;
}

.showAddbtn.history {
  left: inherit;
  right: 20px;
  background: rgba(4, 108, 79, 0.85);
}

.showAddbtn.history .iconfont {
  font-size: 18px;
}

.navbox.history .title {
  text-align: right;
  justify-content: flex-end;
  padding-right: 10px;
}

.navbox.history .title .icon-fanhui {
  transform: rotate(180deg);
}

.navbox.history {
  left: inherit;
  right: 20px;
}

.navbox.history.open {
  width: 300px;
}

.sharepage {
  position: fixed;
  background: #f7f7f7;
  left: 0;
  top: 0;
  right: 760px;
  bottom: 0;
  z-index: 3000;
}

.sharebg {
  position: fixed;
  background: #fff;
  left: 0;
  top: 0;
  right: 0;
  bottom: 0;
  z-index: 100;
}

.sharepage .meslist {
  display: block;
  width: 100%;
  max-width: 1000px;
  height: 100%;
  position: absolute;
  right: 0;
  bottom: 0;
}

.sharepage .icon-wuguan {
  color: var(--el-color-success);
}

.sharepage .icon-geren {
  color: var(--el-color-primary);
}

.meslist {
  box-sizing: border-box;
  border: 1px solid var(--el-border-color);
  border-radius: 5px;
}

.meslist.disabled {
  background: #f5f7fa;
}

.meslist .item {
  display: block;
  padding: 20px 0;
  box-sizing: border-box;
  position: relative;
}

.meslist .item.loadingbox {
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.meslist .item.loadingbox .load {
  position: relative;
  width: 40px;
  transform: scale(0.5);
}

.meslist .item.lbox {
  text-align: left;
  padding-left: 60px;
}

.meslist .item.rbox {
  text-align: right;
  padding-right: 60px;
}

.meslist .item .mes {
  display: inline-block;
  padding: 16px 20px;
  background: #fff;
  border-radius: 16px;
  word-break: break-all;
  text-align: left;
  max-width: 800px;
  border: 1px solid var(--el-border-color)
}

.meslist .item.lbox .mes {
  min-width: 200px;
}

.meslist .item.rbox .mes {
  background: var(--chakra-colors-primary-100);
}

.meslist .item.lbox.active .mes {
  background: var(--c-bg-linear);
  border: 1px solid var(--el-color-primary);
  box-shadow: 0px 4px 6px 0px rgba(228, 228, 228, 0.5);
}

.meslist .item.rbox.active .mes {
  /* background: #d1eaff; */
}

.meslist .item .mes>.iconfontbox {
  position: absolute;
  font-size: 30px;
  top: 20px;
}

.meslist .item.lbox .mes>.iconfontbox {
  left: 20px;
}

.meslist .item.rbox .mes>.iconfontbox {
  right: 20px;
}
</style>