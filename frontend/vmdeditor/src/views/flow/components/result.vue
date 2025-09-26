<script setup>
import { ref, nextTick, onMounted, reactive, watch } from "vue";
import { useStore } from "vuex";
import { useRoute, useRouter } from "vue-router";

import content from "@/components/content.vue";
import icon from "@/components/icon.vue";

import {
  get_log_scores,
  get_cates,
  train_case_add,
  get_log_detail,
} from "@/api/api";
import addtestDialog from "@/views/test/components/addtestDialog.vue";
import addxlDialog from "@/views/edu/components/addxlDialog.vue";
const props = defineProps({
  id: {
    type: [String, Number],
    default: () => 0,
  },
  
  nodeid: {
    type: [String, Number],
    default: () => '',
  },
  title: {
    type: [String, Number],
    default: "新建文件夹",
  },
  data: {
    type: Object,
    default: {},
  },
  modelValue: { type: Boolean, default: false },
});
const emits = defineEmits(["subfn", "update:modelValue", "change", "btnclose"]);
const route = useRoute();
const router = useRouter();
const store = useStore();

const showTest = ref(false);
const xlTypelist = ref([
  { id: 0, name: "未分类", color: "#ff0000", pid: null, children: [] },
]);
watch(
  () => props.modelValue,
  async (n, old) => {
    if (n !== old && n) {
      curnodeIndex.value = -1;
      if (xlTypelist.value.length <= 1) {
        await get_cates().then((res) => {
          xlTypelist.value = [
            {
              id: 0,
              name: "未分类",
              color: "#ff0000",
              pid: null,
              children: [],
            },
          ].concat(res);
          // xlTypelist.value = res
        });
      }

      workflowrunfn(props.data);
    }
  }
);

const close = () => {
  emits("update:modelValue", false);
};

const sub = (params) => {
  emits("subfn", params);
};

const openResult = (item) => {
  console.log(item)
  testSize.value = "90%";
  if (window.innerWidth > 2200) {
    testSize.value = "2000px";
  }

  if (window.innerWidth < 1400) {
    testSize.value = "100%";
  }

  isHide1.value = true;
  isHide2.value = true;
  isHide3.value = true;
  isHide4.value = true;
  isHide5.value = true;

  isResDetail.value = true;
  curResult.value = item;
};
const isResDetail = ref(false);
const runresult = ref({});
const curResult = ref(null);
const isHide1 = ref(true);
const isHide2 = ref(true);
const isHide3 = ref(true);
const isHide4 = ref(true);
const isHide5 = ref(true);
const isHide21 = ref(true);
const isHide22 = ref(true);
const testSize = ref("760px");
const is_sectionid = ref("");
const workflowrunfn = async (curitem) => {
  let item = null;
  if (curitem.id === undefined) {
    // 试运行
    item = curitem;
  } else {
    try {
      item = await get_log_detail({ id: curitem.id });
    } catch (err) {
      console.error("获取详情失败:", err);
      close();
      return;
    }

    if (item.question_id) {
      let scorelist = await get_log_scores({ question_id: item.question_id });

      scorelist.forEach((sitem) => {
        item.human_messages.forEach((citem) => {
          if (citem.id == sitem.answer_id) {
            citem.score = sitem.score;
            if (sitem.score === 5) {
              citem.amend_answer = sitem.amend_answer;
            }
          }
        });
      });
    }
  }
  if (!item || Object.keys(item).length < 1) {
    _this.$message("获取数据失败", "error");
    close();
    return;
  }

  runresult.value = item;
  curResult.value = null;
  testSize.value = "760px";
  initTimes();
  showTest.value = true;

  if (props.nodeid) {
    // 如果存在节点id 展开节点
    if (runresult.value.node_log) {
      runresult.value.node_log.forEach(item => {
        if (item.detail_id == props.nodeid) {
          openResult(item)
        }
      })
    }
  }
};

const maxtime = ref(0);
const curmaxtime = ref(0);
const curmintime = ref(0);
const initTimes = () => {
  let times = runresult.value.node_log || [];
  let min = 0;
  let max = 0;

  times.forEach((item) => {
    let mintime = new Date(item.start_time).getTime();
    let maxtime = new Date(item.end_time).getTime();

    if (min == 0 || mintime < min) {
      min = mintime;
    }
    if (maxtime > max) {
      max = maxtime;
    }

    item.mintime = mintime / 1000;
    item.maxtime = maxtime / 1000;
    item.curtime = parseFloat(item.duration);
  });

  times.forEach((item) => {
    // 查找最早的时间节点 当前最晚的时间节点  计算 节点总时长

    let maxtime = new Date(item.end_time).getTime();
    item.alltime = (maxtime - min) / 1000;
  });
  if (runresult.value.human_messages) {
    runresult.value.human_messages.forEach((item) => {
      let maxtime = new Date(item.send_time).getTime();
      item.alltime = (maxtime - min) / 1000;
    });
  }


  maxtime.value = (max - min) / 1000;
  curmaxtime.value = max / 1000;
  curmintime.value = min / 1000;
};

const colorMap = {};
const getStyle = (item, type, flag) => {
  let styleobj = {};
  let left = (
    ((item.mintime - curmintime.value) /
      (curmaxtime.value - curmintime.value)) *
    100
  ).toFixed(2);
  if (type == "namebox") {
    // 
    let len = 5;
    if(item.runner && item.runner.length > 5){
      len = item.runner.length;
    }
    let fontw = (1-(18*len / 720))*100;  //估算文字宽度 
    if(left <= fontw){
      // 如果宽度足够显示 按照左对齐  不足显示则默认靠右排列
      styleobj = { left: left + "%" };
    }else{
      styleobj = { right: "0%" };
    }
    // styleobj = { left: (left > 80 ? 80 : left) + "%" };
  } else {
    let colorList = [
      "199, 246, 156",
      "242, 217, 117",
      "246, 138, 185",
      "206, 155, 243",
      "175, 214, 237",
      "190, 242, 220",
      "217, 249, 199",
      "249, 222, 199",
      "243, 161, 221",
      "170, 161, 243",
      "161, 205, 243",
      "161, 243, 225",
      "161, 243, 176",
      "209, 241, 174",
      "241, 233, 174",
    ];
    if (!colorMap[item.runner]) {
      let ccindex = -1;
      colorList.forEach((coloritem, colorindex) => {
        let curmapindex = true;
        for (const key in colorMap) {
          const color = colorMap[key];
          if (coloritem == color) {
            curmapindex = false;
          }
        }
        if (curmapindex) {
          // 这个颜色没有使用
          ccindex = colorindex;
          colorMap[item.runner] = coloritem;
        }
      });
      if (ccindex == -1) {
        colorMap[item.runner] =
          colorList[Math.floor(Math.random() * colorList.length)];
      } else {
        colorMap[item.runner] = colorList[ccindex];
      }
    }
    let width = ((item.curtime / maxtime.value) * 100).toFixed(2);
    if (flag == true) {
      width = (parseFloat(item.duration).toFixed(2) / parseFloat(item.alltime).toFixed(2)) * width;
    }
    styleobj = {
      left: left + "%",
      width: width + "%",
      background: 'rgba(' + colorMap[item.runner] + ', 1)',
    };
  }
  return styleobj;
};

const getTiem = (step) => {
  return (maxtime.value * step).toFixed(1);
};



const curContext = ref([]);
const dialogFormVisible1 = ref(false);

const showContext = (item) => {
  // 创建一个新的数组，并复制 item.context 的内容，同时添加 isOpen 属性
  curContext.value = item.citations.map((citem) => ({
    ...citem, // 复制 citem 的所有属性
    isOpen: false, // 添加新的 isOpen 属性
  }));
  dialogFormVisible1.value = true;
};
const curtitle = ref("添加到语料");

const addparam = ref({});
const isShowAddDialog = ref(false);
const addXlfn = () => {
  curtitle.value = "添加到语料";
  addparam.value = {
    train_cate_id: xlTypelist.value[0].id || 0,
    node_id: curResult.value.detail_id || undefined,
    output_data: curResult.value.response_content || "",
    input_data: curResult.value.prompt_str || "",
    feature: curResult.value.inputs.user_input,
    is_modified: false,
  };
  isShowAddDialog.value = true;
};

const testparam = ref({});

const isShowAddTestDialog = ref(false);
const addTestfn = () => {
  TEST_TYPE.value = 'S'
  testparam.value = {
    workflow_node_log_id: curResult.value.detail_id || undefined,
    right_answer: curResult.value.response_content,
    question: curResult.value.prompt_str,
  };
  isShowAddTestDialog.value = true;
};
const TEST_TYPE = ref('S')
const addflowTestfn = () => {
  TEST_TYPE.value = 'W'
  testparam.value = {
    workflow_log_id: runresult.value.id,
    right_answer: runresult.value.output.join("\n"),
    question: runresult.value.user_input,
  };
  isShowAddTestDialog.value = true;
};
const subaddtestfn = (res) => {
  _this.$message("添加成功");
  isShowAddTestDialog.value = false;
  // 添加到测试
  if (TEST_TYPE.value == 'S') {
    if (!curResult.value.unit_cate) {
      curResult.value.unit_cate = [];
    }
    curResult.value.unit_cate.push(res.item);
  } else if (TEST_TYPE.value == 'W') {
    if (!runresult.value.test_cates) {
      runresult.value.test_cates = [];
    }
    runresult.value.test_cates.push(res.item);
  }

  emits("change", runresult.value);
};

const subaddfn = async (res) => {
  _this.$message("添加成功");
  isShowAddDialog.value = false;
  curResult.value.cate.push(res.item);
  emits("change", runresult.value);
};

const isHiderole_variables = ref(true);
const curnodeIndex = ref(-1);

const getCateList = () => {
  let arr = curResult.value.unit_cate || [];
  let arr1 = curResult.value.cate || [];
  arr1.forEach((item, index) => {
    item.xl = true;
  })
  return arr1.concat(arr)
}

const getNameBytype = (type) => {
  const map = {
    'tool': '工具',
    'llm': '大模型',
    'loop': '分批处理',
    'temp_executor': '执行器',
  }
  return map[type] || '';

}


</script>
<template>
  <el-drawer v-model="showTest" :with-header="false" @closed="close" :close-on-click-modal="true" :size="testSize"
    title="试运行" direction="rtl">
    <div :class="{ on: curResult && curResult.runner }" class="testbox">
      <div class="titlebox">
        <div class="title">
          <div class="lbox ellipsis">

            id:{{runresult.id}} 的运行结果（ {{ runresult && runresult.flow_name }} ）
          </div>
          <div class="rbox">
            <el-popover v-if="runresult.test_cates && runresult.test_cates.some((citem) => citem && citem.tag != 'S')"
              placement="bottom" :width="200" trigger="hover">
              <template #reference>
                <div class="dotbox">
                  <span v-for="(item, index) in runresult.test_cates.filter(
                    (citem) => citem && citem.tag != 'S'
                  )" class="dot" :class="{ on: item.xl }" :style="'background-color: ' +
                    item.color +
                    '; right: ' +
                    index * 5 +
                    'px'
                    "></span>
                </div>
              </template>
              <div class="dotcontentbox c-scroll-contain">
                <div class="title">
                  流程测试
                </div>
                <div v-if="runresult.test_cates && runresult.test_cates.some((citem) => citem && citem.tag != 'S')"
                  class="items">
                  <div v-for="item in runresult.test_cates.filter(
                    (citem) => citem && citem.tag != 'S'
                  )" :class="{ unit: item.tag == 'S' }" class="item ellipsis">
                    <span class="c-color radius" :style="'background-color:' + item.color"></span>
                    {{ item.name }}
                  </div>
                </div>

              </div>
            </el-popover>

            <el-button @click="addflowTestfn()" style="margin-left: 10px;" plain class="on">
              <span style="margin-left: 0;font-size:18px"
                class="iconfont icon-a-liuchengceshi-weixuanzhong-caidanicon2"></span>
              添加到流程测试</el-button>


            <span @click.stop="
              emits('btnclose');
            showTest = false;
            " class="iconfont icon-guanbi"></span>
          </div>

        </div>
        <div class="rtopbox">

          <el-button v-if="runresult.__isShowBtn__" @click.stop="
              emits('btnclose',1);
            showTest = false;
            " size="small" type="primary">重新输入</el-button>

          <template v-if="curResult && curResult.runner">
          <div :title="curResult.runner" class="runner ellipsis">
            <span style="font-weight: bold;">【 {{ curResult.runner }} 】</span>
            
            <span class="nodeid" v-if="curResult.runner_Id">id: {{ curResult.runner_Id }}</span>
          </div>
          <div class="runner_run_times ritem">
            第{{ curResult.runner_run_times }}次
          </div>
          <div class="ritem c-warn-btn">{{ curResult.duration }}s</div>
          <div v-if="curResult.model_name" class="ritem c-primary-btn" style="max-width: 100px;">
            <p style="padding: 0" :title="curResult.model_name" class="ellipsis">
              {{ curResult.model_name }}
            </p>
          </div>
          <div v-if="curResult.prompt_str && curResult.detail_id" class="topbtn">
            <el-button style="margin-left: 16px;" @click="addXlfn()" size="small" plain>添加到语料</el-button>
            <el-button @click="addTestfn()" size="small" plain>添加到单元测试</el-button>
          </div>

          <el-button style="margin-left:16px;" v-if="runresult.__isShowBtn__" 
             size="small"  @click.stop="curtitle='调试节点';addparam={input_data: curResult.prompt_str || '',__isTs__:true};isShowAddDialog = true;" plain>调试</el-button>
         

          <el-popover
            v-if="(curResult.cate && curResult.cate.length > 0) || (curResult.unit_cate && curResult.unit_cate.length > 0)"
            placement="bottom" :width="200" trigger="hover">
            <template #reference>
              <div class="dotbox">
                <span v-for="(item, index) in getCateList()" class="dot" :class="{ on: item.xl }" :style="'background-color: ' +
                  item.color +
                  '; left: ' +
                  index * 5 +
                  'px'
                  "></span>
              </div>
            </template>
            <div class="dotcontentbox c-scroll-contain">
              <div v-if="curResult.unit_cate.length > 0" class="title">
                单元测试
              </div>
              <div v-if="curResult.unit_cate.length > 0" class="items">
                <div v-for="item in curResult.unit_cate" :class="{ unit: item.tag == 'S' }" class="item ellipsis">
                  <span class="c-color radius" :style="'background-color:' + item.color"></span>
                  {{ item.name }}
                </div>
              </div>
              <div v-if="curResult.cate && curResult.cate.length > 0" class="title">语料类型</div>
              <div v-if="curResult.cate && curResult.cate.length > 0" class="items">
                <div v-for="item in curResult.cate" class="item ellipsis">
                  <span class="c-color" :style="'background-color:' + item.color"></span>
                  {{ item.name }}
                </div>
              </div>
            </div>
          </el-popover>
        </template>

        </div>
      </div>
      <div class="resultbody">
        <div v-if="curResult && curResult.runner" class="resultDialogbox">

          <div class="resultDialog">
            <div class="resultDialogitem">
              <div class="topbtn"></div>
              <div class="contbox">
                <el-scrollbar>
                  <div class="mr20">
                    <div class="cardbox" v-if="curResult.prompt_str">
                      <div class="ltitlebox">
                        <div @click.stop="isHide1 = !isHide1" class="ltitle">
                          <icon type="shuru1"></icon>
                          <span :class="{ off: isHide1 }" class="iconfont icon-xiajiantou pointer"></span>当前节点输入
                        </div>
                        <div @click.stop v-copy="curResult.prompt_str" style="color: #333;" class="c-copybox">
                          <span class="iconfont icon-chakanxiangqing-fuzhidaima"></span>
                          复制代码
                        </div>
                      </div>
                      <div v-show="isHide1" class="rbox">
                        <v-md-preview :text="curResult.prompt_str"></v-md-preview>
                      </div>
                    </div>
                  </div>
                </el-scrollbar>
              </div>
            </div>
            <div class="resultDialogitem">
              <div class="topbtn"></div>
              <div class="contbox">
                <el-scrollbar>
                  <div class="mr20">
                    <div class="cardbox dqjdsc" v-if="curResult.response_content">
                      <div class="ltitlebox">
                        <div @click.stop="isHide2 = !isHide2" class="ltitle">
                          <icon type="shuchu1"></icon>
                          <span :class="{ off: isHide2 }" class="iconfont icon-xiajiantou pointer"></span>当前节点输出
                        </div>
                        <div @click.stop v-copy="curResult.response_content" class="c-copybox">
                          <span class="iconfont icon-chakanxiangqing-fuzhidaima"></span>
                          复制代码
                        </div>
                      </div>
                      <div v-show="isHide2" class="rbox">
                        <v-md-preview :text="curResult.response_content"></v-md-preview>
                      </div>
                    </div>

                    <div class="cardbox hsfhz" v-if="curResult.function_calls">
                      <div class="ltitlebox">
                        <div @click.stop="isHide3 = !isHide3" class="ltitle">
                          <icon type="hsfhz"></icon>
                          <span :class="{ off: isHide3 }" class="iconfont icon-xiajiantou pointer"></span>工具函数返回值
                        </div>
                        <div @click.stop v-copy="curResult.function_calls" class="c-copybox">
                          <span class="iconfont icon-chakanxiangqing-fuzhidaima"></span>
                          复制代码
                        </div>
                      </div>
                      <div v-show="isHide3" style="padding: 0;" class="rbox">
                        <json-viewer :show-array-index="true" sort :expand-depth="2"
                          :value="curResult.function_calls"></json-viewer>
                      </div>
                    </div>

                    <div class="cardbox qjgzbl" v-if="curResult.variables">
                      <div class="ltitlebox">
                        <div @click.stop="isHide4 = !isHide4" class="ltitle">
                          <icon type="qjgzbl"></icon>
                          <span :class="{ off: isHide4 }" class="iconfont icon-xiajiantou pointer"></span>全局工作空间变量
                        </div>
                        <div @click.stop v-copy="curResult.variables" class="c-copybox">
                          <span class="iconfont icon-chakanxiangqing-fuzhidaima"></span>
                          复制代码
                        </div>
                      </div>
                      <div style="padding: 0;" v-show="isHide4" class="rbox">
                        <json-viewer :show-array-index="true" sort :expand-depth="2"
                          :value="curResult.variables"></json-viewer>
                      </div>
                    </div>

                    <div class="cardbox dqjdbl" v-if="curResult.role_variables">
                      <div class="ltitlebox">
                        <div @click.stop="isHiderole_variables = !isHiderole_variables" class="ltitle">
                          <icon type="dqjdbl"></icon>
                          <span :class="{ off: isHiderole_variables }"
                            class="iconfont icon-xiajiantou pointer"></span>当前节点变量
                        </div>
                        <div @click.stop v-copy="curResult.role_variables" class="c-copybox">
                          <span class="iconfont icon-chakanxiangqing-fuzhidaima"></span>
                          复制代码
                        </div>
                      </div>
                      <div style="padding: 0;" v-show="isHiderole_variables" class="rbox">
                        <json-viewer :show-array-index="true" sort :expand-depth="2"
                          :value="curResult.role_variables"></json-viewer>
                      </div>
                    </div>

                    <div class="cardbox ltsxx" v-if="curResult.room_messages">
                      <div class="ltitlebox">
                        <div @click.stop="isHide5 = !isHide5" class="ltitle">
                          <icon type="ltsxx"></icon>
                          <span :class="{ off: isHide5 }" class="iconfont icon-xiajiantou pointer"></span>聊天室消息
                        </div>
                        <div @click.stop v-copy="curResult.room_messages" class="c-copybox">
                          <span class="iconfont icon-chakanxiangqing-fuzhidaima"></span>
                          复制代码
                        </div>

                      </div>
                      <div style="padding: 0;" v-show="isHide5" class="rbox">
                        <json-viewer :show-array-index="true" sort :expand-depth="2"
                          :value="curResult.room_messages"></json-viewer>
                      </div>
                    </div>
                  </div>
                </el-scrollbar>
              </div>
            </div>
          </div>
        </div>

        <div class="resultbox">
          <el-scrollbar>
            <div class="mr20">
              <template v-if="runresult && runresult.inputs">
                <div class="ltitlebox">
                  <div @click.stop="isHide21 = !isHide21" class="ltitle">
                    <icon width="32" height="32" type="shuru"></icon>
                    <span :class="{ off: isHide21 }" class="iconfont icon-xiajiantou pointer"></span>
                    输入

                  </div>

                  <div @click.stop v-copy="runresult.inputs" class="c-copybox">
                    <span class="iconfont icon-chakanxiangqing-fuzhidaima"></span>
                    复制代码
                  </div>
                </div>

                <div v-show="isHide21" style="padding: 0;overflow: hidden;" class="cardbox">
                  <json-viewer :show-array-index="true" sort :expand-depth="2" :value="runresult.inputs"></json-viewer>
                </div>
              </template>

              <template v-if="runresult && runresult.human_messages">
                <div class="ltitlebox">
                  <div @click.stop="isHide22 = !isHide22" class="ltitle">
                    <icon width="32" height="32" type="shuchu"></icon>
                    <span :class="{ off: isHide22 }" class="iconfont icon-xiajiantou pointer"></span>输出
                    <span v-if="runresult.citations && runresult.citations.length > 0"
                      @click.stop="showContext(runresult)" class="c-primary pointer citations">
                      [{{ runresult.citations.length }}条引用]
                    </span>
                  </div>
                  <div v-copy="runresult.human_messages" class="c-copybox">
                    <span class="iconfont icon-chakanxiangqing-fuzhidaima"></span>
                    复制代码
                  </div>
                </div>
                <div v-show="isHide22" class="cardbox human_messages">
                  <div v-if="
                    !runresult.human_messages ||
                    runresult.human_messages.length < 1
                  " class="c-empty" style="text-align: left">
                    抱歉：目前没有任何输出
                    <br />
                  </div>
                  <div v-for="item in runresult.human_messages" class="item">
                    <div class="mestimebox">
                      <div class="rolebox">
                        {{ item.from_role }}
                        <span class="c-warn-btn radius" style="font-weight: normal;margin-left: 8px;">{{
                          item.alltime.toFixed(2) + "s" }}</span>

                        <el-popover placement="right" v-if="
                          (item.score || item.score === 0) && item.amend_answer
                        " :width="400" trigger="hover">
                          <template #reference>
                            <span class="c-danger">（{{ item.score }}分）</span>
                          </template>

                          <div style="margin: 0 -20px;">
                            <el-scrollbar max-height="400">
                              <div v-html="item.amend_answer" style="margin:0 20px;">
                              </div>
                            </el-scrollbar>
                          </div>
                        </el-popover>

                        <span v-if="
                          (item.score || item.score === 0) && !item.amend_answer
                        " class="c-danger">（{{ item.score }}分）</span>
                      </div>

                    </div>
                    <div class="message">
                      <v-md-preview :text="item.message"></v-md-preview>
                    </div>
                    <div class="time">{{ item.send_time ? item.send_time.split('.')[0] : '' }}</div>
                  </div>
                </div>
              </template>

              <div class="timebox node_logbox">
                <div class="bgline"></div>
                <div class="bgline"></div>
                <div class="bgline"></div>
                <div class="bgline"></div>
                <div class="bgline"></div>
                <div class="bgline"></div>
                <div class="bgc"></div>
                <div class="bgc"></div>
                <div class="bgc"></div>
                <div class="bgc"></div>
                <div class="bgc"></div>
                <div class="bgc"></div>
                <div class="timeline">
                  <div class="titem">0s</div>
                  <div class="titem">{{ getTiem(0.2) }}s</div>
                  <div class="titem">{{ getTiem(0.4) }}s</div>
                  <div class="titem">{{ getTiem(0.6) }}s</div>
                  <div class="titem">{{ getTiem(0.8) }}s</div>
                  <div class="titem">{{ maxtime.toFixed(2) }}s</div>
                </div>
                <div class="timecontain">
                  <div v-for="(item, index) in runresult.node_log" @click="
                    openResult(item);
                  curnodeIndex = index;
                  " :class="{
                    is_section_sub: item.is_section_sub,
                    checked: curnodeIndex == index,
                  }" class="titem" v-show="!item.is_section_sub || item.pid == is_sectionid">

                    <div :style="getStyle(item, 'process')" class="process"><span class="toolbox"
                        v-if="item.runner_type == 'tool'"><!-- 工具节点 --></span></div>
                    <!-- <div :style="getStyle(item, 'process', true)" class="process"></div> -->
                    <div :style="getStyle(item, 'namebox')" class="namebox">

                      <el-popover :show-after="1000" placement="right" :popper-style="{width:'auto',padding:'10px',minWidth:'80px'}" trigger="hover">
                        <template #reference>
                          <div class="nameitem" >
                            <p style="display: inline-block;" class="ellipsis">
                              <span v-if="item.is_section" @click.stop="
                                is_sectionid == item.id
                                  ? (is_sectionid = '')
                                  : (is_sectionid = item.id)
                                " class="iconfont icon-xiajiantou opensection pointer"
                                :class="{ on: is_sectionid == item.id }">
                              </span>
                              {{ item.runner }}
                              <span style="opacity: 0.8;font-size:12px;" v-if="item.is_section_sub">（{{
                                parseFloat(item.duration).toFixed(2) +
                                "/" +
                                parseFloat(item.alltime).toFixed(2) +
                                "s"
                                }}）</span>
                            </p>
                            <br>
                            <p style="opacity: 0.8;font-size:12px;display: inline-block;" class="ellipsis" v-if="!item.is_section_sub">{{
                              parseFloat(item.duration).toFixed(2) +
                              "/" +
                              parseFloat(item.alltime).toFixed(2) +
                              "s"
                              }}</p>
                          </div>
                        </template>
                        <div class="nodebox">
                          <div>
                            <div class="name">{{ item.runner }}</div>
                            <div class="time">
                              {{ parseFloat(item.duration).toFixed(2) +
                                '/' +
                                parseFloat(item.alltime).toFixed(2) +
                                's' }}
                            </div>
                          </div>

                          <span v-if="getNameBytype(item.runner_type)" class="c-primary-btn type">{{ getNameBytype(item.runner_type) }}</span>
                        </div>
                      </el-popover>



                    </div>
                  </div>
                </div>
              </div>

              <div v-if="runresult.error_msg" class="c-danger" style="padding: 20px 0">
                错误提示：<br />{{ runresult.error_msg }}
              </div>
            </div>
          </el-scrollbar>
        </div>
      </div>

    </div>
  </el-drawer>
  <content title="引用内容" :curContext="curContext" v-model="dialogFormVisible1"></content>

  <addxlDialog v-model="isShowAddDialog" :curResult="curResult" :item="addparam" :title="curtitle" @subfn="subaddfn"></addxlDialog>

  <addtestDialog v-model="isShowAddTestDialog" :TEST_TYPE="TEST_TYPE" :curResult="curResult" :item="testparam" @subfn="subaddtestfn">
  </addtestDialog>
</template>
<style scoped>
.nodebox {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}
.namebox .nameitem{
  display: inline-block;
    line-height: 15px;
    padding-top: 3px;
}
.namebox .nameitem .ellipsis{
  display: inline-block;
}
.nodebox .type {
  flex-shrink: 0;
  margin-left: 10px;
}

.nodebox .name {
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.nodebox .time {
  font-size: 12px;
  opacity: 0.8;
  color: var(--el-text-color-regular);
}

.node_logbox {
  position: relative;
  border-bottom: 1px solid var(--el-border-color);
  margin-top: 24px;
}

.node_logbox .bgline {
  position: absolute;
  width: 1px;
  height: 10px;
  border-left: 1px solid var(--el-border-color);
  left: 0;
  top: 22px;
}

.node_logbox .bgline:nth-child(2) {
  left: 20%;
}

.node_logbox .bgline:nth-child(3) {
  left: 40%;
}

.node_logbox .bgline:nth-child(4) {
  left: 60%;
}

.node_logbox .bgline:nth-child(5) {
  left: 80%;
}

.node_logbox .bgline:nth-child(6) {
  right: 0;
  left: inherit;
}

.node_logbox .bgc {
  position: absolute;
  width: 1px;
  border-left: 1px solid var(--el-border-color);
  left: 0;
  top: 24px;
  bottom: 0;
}

.node_logbox .bgc:nth-child(8) {
  left: 20%;
  border-style: dotted;
}

.node_logbox .bgc:nth-child(9) {
  left: 40%;
  border-style: dotted;
}

.node_logbox .bgc:nth-child(10) {
  left: 60%;
  border-style: dotted;
}

.node_logbox .bgc:nth-child(11) {
  left: 80%;
  border-style: dotted;
}

.node_logbox .bgc:nth-child(12) {
  right: 0;
  left: inherit;
}

.ltitlebox {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 24px;
}

.ltitlebox .ltitle {
  cursor: pointer;
}

.resultbox :deep(.v-md-editor-preview) {
  padding: 0;
}

.nodeid {
  color: #aaa;
  font-size: 14px;
  margin-left: 10px;
}

.isShowAddDialogBox {
  height: 700px;
}

.dotbox {
  position: relative;
  padding: 10px 0 0 0;
  cursor: pointer;
  margin-left: 10px;
}

.dotbox .dot {
  display: block;
  position: absolute;
  width: 10px;
  height: 10px;
  top: 0px;
  border-radius: 5px;
  z-index: 10;
}

.dotbox .dot.on {
  border-radius: 0;
}

.dotcontentbox {
  display: block;
  width: 100%;
  font-size: 12px;
  max-height: 300px;
  overflow-y: auto;
}

.dotcontentbox .title {
  color: #aaa;
  margin-bottom: 10px;
}

.dotcontentbox .items {
  margin-bottom: 10px;
}

.dotcontentbox .items .item {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  flex-wrap: wrap;
}

.mestimebox {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.mestimebox .time {
  flex-shrink: 0;
}

.testbox .timecontain .opensection {
  font-size: 12px;
  transition: all 0.3s;
  display: inline-block;
}

.testbox .timecontain .opensection.on {
  transform: rotate(-90deg);
}

.resultbody {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  height: calc(100% - 70px);
  margin: 0 -20px 0 -20px;
}

.resultbody .cardbox {
  background: #FFFFFF;
  border-radius: 16px;
  border: 1px solid #E2E2E2;
  padding: 16px;
  box-shadow: 0px 4px 6px 0px rgba(228, 228, 228, 0.5);
  background: #fff;
}

.resultbody .cardbox.hsfhz {
  border: 1px solid #EFE4C8;
}

.resultbody .cardbox.hsfhz .ltitlebox {
  background: #FBF2DA;
}

.resultbody .cardbox.hsfhz .icon-xiajiantou,
.resultbody .cardbox.hsfhz .c-copybox {
  color: #7F6318;
}

.resultbody .cardbox.dqjdsc {
  border: 1px solid #A1C5EF;
}

.resultbody .cardbox.dqjdsc .ltitlebox {
  background: #E8F3FE;
}

.resultbody .cardbox.dqjdsc .icon-xiajiantou,
.resultbody .cardbox.dqjdsc .c-copybox {
  color: #4978A6;
}

.resultbody .cardbox.qjgzbl {
  border: 1px solid #EFC4B1;
}

.resultbody .cardbox.qjgzbl .ltitlebox {
  background: #FEEDEA;
}

.resultbody .cardbox.qjgzbl .icon-xiajiantou,
.resultbody .cardbox.qjgzbl .c-copybox {
  color: #B74C1D;
}


.resultbody .cardbox.dqjdbl {
  border: 1px solid #F5AFC0;
}

.resultbody .cardbox.dqjdbl .ltitlebox {
  background: #FFF0F9;
}

.resultbody .cardbox.dqjdbl .icon-xiajiantou,
.resultbody .cardbox.dqjdbl .c-copybox {
  color: #AE0D39;
}

.resultbody .cardbox.ltsxx {
  border: 1px solid #A9D3DB;
}

.resultbody .cardbox.ltsxx .ltitlebox {
  background: #EBFBFE;
}

.resultbody .cardbox.ltsxx .icon-xiajiantou,
.resultbody .cardbox.ltsxx .c-copybox {
  color: #308292;
}


/* .resultDialogbox :deep(.github-markdown-body){
    font-size: 14px;
  } */
.resultDialog {
  text-align: left;
  height: 100%;
  width: 100%;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.resultDialogbox .cardbox {
  padding: 0;
  overflow: hidden;
  margin-bottom: 12px;
}

.resultDialogbox .cardbox .ltitlebox {
  padding: 0 16px;
  background: #EAEAEA;
  margin-top: 0;
}

.resultDialog .resultDialogitem {
  display: block;
  width: 50%;
  box-sizing: border-box;
  margin: 0;
  height: 100%;
  border-right: 1px solid var(--el-border-color);
}

.resultDialog .resultDialogitem .mr20 {
  margin: 20px 20px 0 20px;
}

.resultDialog .resultDialogitem:nth-last-child(1) {
  border: none;
}

.resultDialog .resultDialogitem .topbtn {
  display: flex;
  align-items: center;
  height: 0px;
  padding: 0 20px;
}

.resultDialog .resultDialogitem .contbox {
  height: calc(100% - 0px);

}

.testbox .resultbox {
  display: block;
  width: 100%;
  height: calc(100% - 10px);
  box-sizing: border-box;
}

.testbox .resultbox .mr20 {
  margin: 0 20px;
}


.resultDialogbox {
  display: block;
  width: 58%;
  height: 100%;
  border-right: 1px solid var(--el-border-color);
}

.testbox.on .resultbox {
  width: 42%;
  height: calc(100% - 12px);
  /*12px是左侧卡片下边距*/

}

.testbox {
  display: block;
  height: 100%;
  width: 100%;
}

.testbox .iconfont {

  cursor: pointer;
}

.testbox .titlebox .iconfont {
  margin-left: 20px;
  font-weight: bold;
  text-align: left;
}

.testbox .titlebox {
  height: 90px;
  margin: 0 -20px;
  padding: 0 20px 20px 20px;
  box-sizing: border-box;
  border-bottom: 1px solid var(--el-border-color);
}

.testbox .title {
  text-align: left;
  display: flex;
  align-items: center;
  justify-content: space-between;

  font-size: 20px;
  font-weight: bold;
}

.testbox .title .lbox {
  display: inline-block;
  max-width: calc(100% - 170px);
}

.testbox .title .rbox {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.testbox .iconfont {
  cursor: pointer;
}

.testbox .btns {
  text-align: right;
}

.titlebox .rtopbox {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  flex-wrap: wrap;
  margin-top: 10px;
}

.titlebox .rtopbox .runner {
  font-size: 16px;
  max-width: 320px;
  color: var(--el-text-color-regular);
  margin-right: 12px;
}

.titlebox .rtopbox .ritem {
  display: inline-block;
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 20px;
  margin-left: 5px;
}

.titlebox .rtopbox .runner_run_times {
  background: #F3F3F3;
  color: #333;
}

.titlebox .rtopbox .duration {
  background: #1237b3;
  color: #fff;
}

.resultDialog .rbox {
  box-sizing: border-box;
  padding: 16px;
}

.ltitle {
  font-size: 14px;
  text-align: left;
  padding: 5px 0;
  margin: 5px 0;
  font-weight: bold;
  display: flex;
  color: #333;
  align-items: center;
  justify-content: flex-start;
  position: relative;

}

.ltitle .citations {
  color: #446fff;
  font-weight: normal;
  font-size: 12px;
  padding-left: 17px;
}

.ltitle .copybtn {
  margin-left: 10px;
}

.ltitle .fr {
  position: absolute;
  right: 0;
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.ltitle .iconfont.pointer {
  padding: 5px;
  font-size: 12px;
  transition: all 0.3s;
  transform: rotate(-90deg);
}

.ltitle .iconfont.pointer.off {
  transform: rotate(0deg);
}

.timeline {
  display: block;
  position: relative;
  width: 100%;
  height: 30px;
  border-bottom: 1px solid #ccc;
}

.timeline .titem {
  position: absolute;
  text-align: center;
  left: 0;
}

.timeline .titem:nth-child(2) {
  left: 20%;
  transform: translateX(-50%);
}

.timeline .titem:nth-child(3) {
  left: 40%;
  transform: translateX(-50%);
}

.timeline .titem:nth-child(4) {
  left: 60%;
  transform: translateX(-50%);
}

.timeline .titem:nth-child(5) {
  left: 80%;
  transform: translateX(-50%);
}

.timeline .titem:nth-child(6) {
  right: 0;
  left: inherit;
}

.resultbox {
  display: block;
  text-align: left;
  font-size: 14px;
}

.timecontain {
  display: block;
  width: 100%;
  box-sizing: border-box;
  overflow-x: hidden;
}

.timecontain .titem {
  display: block;
  position: relative;
  width: 100%;
  height: 60px;
}

.timecontain .titem.is_section_sub {
  height: 40px;
}

.timecontain .titem .process {
  position: absolute;
  height: 50px;
  z-index: 1;
  top: 0;
  border-radius: var(--el-border-radius-base);
  display: flex;
  align-items: center;
  justify-content: center;
}

.timecontain .titem .process>.toolbox {
  display: block;
  width: 100%;
  height: 34px;
  background: #fff;
  opacity: 0.6;
}

.timecontain .titem.is_section_sub .process {
  height: 26px;
  background: #eee !important;
  border: 1px solid #eee;
  border-radius: 26px;
}

.timecontain .titem.is_section_sub .namebox {
  height: 28px;
  font-size: 12px;
  color: #777;
  padding: 5px 10px;
}

.timecontain .titem.checked.is_section_sub .namebox {
  color: #0090a1;
}

.timecontain .titem .namebox {
  position: absolute;
  height: 30px;
  cursor: pointer;
  top: 0;
  z-index: 2;
  right: 0;
  box-sizing: border-box;
  padding: 7px 10px 0 10px;
  color: #102642;
  display: block;
}

.human_messages .item {
  display: block;
  border-bottom: 1px solid var(--el-border-color);
  box-sizing: border-box;
  padding: 16px 0 12px 0;
}

.human_messages .item:nth-last-child(1) {
  border-bottom: none;
}

.resultbody .cardbox.human_messages {
  background: var(--c-bg-linear);

}

.human_messages .message {
  margin: 12px 0 0 0;
}

.human_messages .time {
  font-size: 12px;
  color: #999;
}


.testbox :deep(.github-markdown-body) {
  padding: 0px;
}

.human_messages :deep(.github-markdown-body) {
  font-size: 14px;
  margin-bottom: -10px;
}

.resultbox .rolebox {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  flex-wrap: wrap;
  font-weight: bold;
}

.resultbox .rolebox .from_role {
  margin-right: 10px;
}
</style>