<script setup>
import { ref, nextTick, shallowRef, onActivated, reactive } from "vue";
import { useStore } from "vuex";
import Add from "./components/add.vue";
import CompRadio from "@/components/CompRadio.vue";
import { knowledges, knowledgesAdd, knowledgesDelete, similaritysearch } from "@/api/api";
import { onBeforeRouteLeave, useRoute, useRouter } from "vue-router";
import { cloneDeep,uniq } from "lodash";
const route = useRoute();
const router = useRouter();

const store = useStore();
import xltest from "@/components/xltest.vue";
const dialogFormVisible1 = ref(false);

const activeName = ref('');
if (route.query.active) {
  activeName.value = route.query.active;
}

let pagelist = ref([]);
const alllist = ref([]);
const search = () => {
  knowledges().then((res) => {
    let arr = res || [];
    alllist.value = cloneDeep(arr);
    pagelist.value = arr;
    textlist.value = [];
    splist.value = [];
    excellist.value = [];
    arr.forEach((item) => {
      if (item.type == 2) {
        splist.value.push(item);
      } else if (item.type == 1) {
        textlist.value.push(item);
      } else if (item.type == 3) {
        excellist.value.push(item);
      }
    });
    if (activeName.value) {
      setpagelist();
    }

  });
};

search();
const curlabels = ref([]);
const form1 = reactive({ name: "", caption: "", id: "", type: "", label: "" });

const addTag = () =>{
  curlabels.value = uniq([...curlabels.value]);
}


const openDialog = (item, type = "") => {
  // 使用三元操作符简化条件判断
  form1.id = item ? item.id : "";
  form1.name = item ? item.name : "";
  form1.caption = item ? item.caption : "";
  form1.label = item ? item.label : "";
  curlabels.value = item?.label ? item.label.split(",") : [];

  form1.type = type || item?.type || "";
  dialogFormVisible1.value = true;
  setTimeout(() => {
    document.querySelectorAll(".autofocus.inp2 input")[0].focus();
  }, 100);
};

const del = (id) => {
  _this.$confirm("此操作将永久删除该知识库, 是否继续?").then((res) => {
    knowledgesDelete({ id }).then((res) => {
      _this.$message("删除成功");
      search();
    });
  });
};

// 创建知识库

const ruleFormRef1 = ref();
const rules1 = reactive({
  name: [{ required: true, message: "请输入知识库名称" }],
});
const saveZsk = async (formEl) => {
  if (!formEl) return;
  formEl.validate((valid) => {
    if (valid) {
      form1.label = curlabels.value.join(",");

      knowledgesAdd(form1).then((res) => {
        if (res) {
          _this.$message("提交成功");
          dialogFormVisible1.value = false;
          search();
        }
      });
    } else {
      document.querySelectorAll(".autofocus.inp2 input")[0].focus();
      return false;
    }
  });
};


const xlDialog = ref(false);
const xlform = reactive({
  knowledgebase_k: 5,
  knowledgebase_ids: [],
  file_knowledgebase_ids: [],
  product_model_ids: [],
  file_knowledgebase_k: 5,
  product_model_top_k: 5,
  question: "",
});
const curContext = ref([]);
const openxlDialog = (item) => {
  curContext.value = [];
  xlform.knowledgebase_k = 5;
  xlform.knowledgebase_ids = [];
  xlform.product_model_ids = [];
  xlform.file_knowledgebase_ids = [];
  xlform.product_model_top_k = 5;
  xlform.file_knowledgebase_k = 5;
  xlform.question = "";

  if (item) {
    if (item.type == 2) {
      xlform.product_model_ids = [item.id];
    } else if (item.type == 3) {
      xlform.file_knowledgebase_ids = [item.id];
    } else if (item.type == 1) {
      xlform.knowledgebase_ids = [item.id];
    }
  }

  xlDialog.value = true;
};



const textlist = ref([]);
const splist = ref([]);
const excellist = ref([]);




const handleClick = (tab, event) => {
  let query = { ...route.query };
  query.active = activeName.value;
  router.replace({ path: route.path, query: query });
  setpagelist()
};

const setpagelist = () => {
  if (activeName.value == '1') {
    pagelist.value = textlist.value;
  } else if (activeName.value == '2') {
    pagelist.value = splist.value;
  } else if (activeName.value == '3') {
    pagelist.value = excellist.value;
  } else {
    pagelist.value = alllist.value;
  }
}


</script>

<template>
  <div class="c-titlebox">
    <span class="title">知识库</span>
    <div class="btns">
      <el-button size="small" @click="openxlDialog()" type="primary">向量检测</el-button>
      <el-popover :width="200">
        <template #reference>
          <el-button size="small" class="on" style="border: none;" plain>新建</el-button>
        </template>
        <template #default>
          <div class="c-cardbtn-btns">
            <div @click="openDialog(undefined, 1)" class="item">
              <span class="name">文本知识库</span>
            </div>
            <!-- <div @click="openDialog(undefined, 2)" class="item">
                    <span class="name">产品知识库</span>
                  </div> -->
            <div @click="openDialog(undefined, 3)" class="item">
              <span class="name">EXCEL知识库</span>
            </div>

          </div>

        </template>
      </el-popover>
    </div>
  </div>

  <div class="tabbox">
    <el-tabs v-model="activeName" class="demo-tabs" @tab-change="handleClick">
      <el-tab-pane name="1">
        <template #label>
          文本知识库
        </template>
      </el-tab-pane>
      <!-- <el-tab-pane name="2">
        <template #label>
          产品知识库
        </template>
      </el-tab-pane> -->
      <el-tab-pane name="3">
        <template #label>
          EXCEL知识库
        </template>
      </el-tab-pane>
      <el-tab-pane :name="''">
        <template #label>
          全部
        </template>
      </el-tab-pane>
    </el-tabs>
  </div>

  <div class="scrollbox">
    <el-scrollbar ref="scrollbarRef">
      <div class="pagelistbox">
        <div v-for="(item, index) in pagelist" @click="
          $router.push(
            item.type == 2
              ? `/dataset/shop?id=${item.id}`
              : item.type == 1 ? `/dataset/detail?id=${item.id}` : `/dataset/excel?id=${item.id}&name=${item.name}`
          )
          " :key="index" :class="'type' + item.type" class="item">
          <span class="iconfont icon-zhishiku-kapianzaiti"></span>
          <span class="iconfont icon-zhishiku-ceshianniubeijing"></span>

          <span :class="'c-topicon' + item.type"></span>
          <div class="rbox">
            <el-popover :width="160">
              <template #reference>
                <span class="iconfont icon-gengduo c-cardbtn-icon"></span>
              </template>
              <template #default>
                <div class="c-cardbtn-btns">
                  <div @click="openDialog(item)" class="item">
                    <span class="name">修改</span>
                  </div>
                  <div @click="del(item.id)" class="item err">
                    <span class="name">删除</span>
                  </div>
                </div>
              </template>
            </el-popover>
          </div>




          <div :title="item.name" class="title ellipsis">
            {{ item.name }}
          </div>



          <div class="typebox">
            {{ store.getters.iconMaps.knowledgeNames[item.type].name }}
          </div>

          <div :title="item.caption" class="introbox ellipsis2">
            {{ item.caption || "这个知识库还没有介绍~" }}
          </div>

          <div v-if="item" :title="item.label" class="ellipsis labelbox">
            <template v-if="item.label">
              <div class="brand_name c-primary-btn ellipsis" v-for="citem in item.label.split(',')">
                {{ citem }}
              </div>
            </template>
            <template v-else>
              <div class="brand_name c-plain-btn ellipsis">暂无标签</div>
            </template>
          </div>



          <div @click.stop="openxlDialog(item)" class="fotbtn">
            测试 <span class="iconfont icon-xiangyoujiantou"></span>
          </div>
        </div>
      </div>
    </el-scrollbar>
  </div>
  <el-dialog v-model="dialogFormVisible1" :title="form1.id ? '修改知识库' : '创建知识库'" width="700">
    <el-form @submit.native.prevent ref="ruleFormRef1" class="tl" :rules="rules1" label-width="auto"
      label-position="top" inline :model="form1">
      <el-form-item style="width: calc(50% - 8px);margin-right: 16px;" label="知识库名称" prop="name">
        <el-input @keyup.native.enter="saveZsk(ruleFormRef1)" class="autofocus inp2" placeholder="请输入知识库名称"
          v-model="form1.name" maxlength="50" autocomplete="off" />
      </el-form-item>
      <el-form-item style="width: calc(50% - 8px);margin-right: 0px;" label="标签" prop="label">
        <template #label>
          标签 <span class="c-tips">(回车可添加多个标签)</span>
        </template>
        <el-input-tag 
        @add-tag="addTag"
        collapse-tags
        collapse-tags-tooltip
      :max-collapse-tags="2" v-model="curlabels" placeholder="请输入标签信息" />
      </el-form-item>

      <el-form-item style="width: 100%;margin-right: 0;" label="介绍" prop="caption">
        <el-input v-model="form1.caption" maxlength="200" :autosize="{ minRows: 2, maxRows: 4 }" type="textarea"
          placeholder="这个知识库还没有介绍~" />
      </el-form-item>
    </el-form>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="dialogFormVisible1 = false">取消</el-button>
        <el-button type="primary" @click="saveZsk(ruleFormRef1)">
          确认提交
        </el-button>
      </div>
    </template>
  </el-dialog>


  <xltest :xlform="xlform" v-model="xlDialog"></xltest>
</template>

<style scoped>
.labelbox{
  display: block;
  width: 170px;
  text-align: left;
}
.pagelistbox .item .labelbox{
  position: absolute;
  left: 20px;
  bottom: 16px;
}
.contextbox {
  padding: 10px;
}

.score {
  color: #aaa;
  margin-top: 5px;
}

.contextbox .item {
  box-sizing: border-box;
  padding: 20px;
  border: 1px solid var(--el-border-color);
  border-radius: 5px;
  margin-bottom: 20px;
  text-align: left;
  position: relative;
}

.contextbox .item .title {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.icon-gengduo {
  cursor: pointer;
}

.js-btn {
  cursor: pointer;
  position: absolute;
  right: 30px;
  bottom: 18px;
  background: #fff;
  padding: 2px;
  color: var(--el-color-primary);
  display: inline-block;
  font-size: 12px;
}

.intro {
  display: block;
  height: 40px;
  overflow: hidden;
  line-height: 20px;
}

.intro.open {
  height: auto;
}

.xlcontent {
  height: calc(100% - 60px);
}

.xltitle {
  text-align: left;
  padding: 10px;
  border-bottom: 1px solid #ccc;
}

.icon-zhishiku {
  color: var(--el-color-primary);
}

.icon-zhishikuguanli {
  color: var(--el-color-success);
}


.titlebox {
  text-align: left;
  font-size: 22px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding: 10px 30px;
  font-weight: bold;
}

.icon-zhishi {
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

.listbox .icon-zhishi {
  font-size: 20px;
}

.scrollbox {
  display: block;
  width: 100%;
  height: calc(100% - 54px);
}

.pagelistbox {
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  flex-wrap: wrap;
}

.pagelistbox .item {
  width: 312px;
  height: 272px;
  background: none;
  box-sizing: border-box;
  margin: 0 16px 16px 0;
  cursor: pointer;
  padding: 24px;
  position: relative;
  overflow: hidden;
}

.pagelistbox .item>* {
  z-index: 1;
  position: relative;
}



.pagelistbox .item .title {
  font-weight: 500;
  font-size: 20px;
  color: #333333;
  text-align: left;
  font-style: normal;
  margin-top: 16px;
  margin-bottom: 4px;
}

.pagelistbox .item .brand_name {
  max-width: 137px;
  margin-right: 5px;
}

.pagelistbox .item .fotbtn {
  position: absolute;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 90px;
  height: 60px;
  font-size: 14px;
  color: var(--c-font-color);
}

.pagelistbox .item .fotbtn:hover {
  color: var(--el-color-primary);
}

.pagelistbox .item .fotbtn .iconfont {
  font-size: 10px;
}

.pagelistbox .item .rbox {
  position: absolute;
  right: 0;
  top: 0;
  z-index: 2;
}

.pagelistbox .item .typebox {
  text-align: left;
  font-size: 14px;
  color: #004AAF;
}

.pagelistbox .item.type2 .typebox {
  color: #CE1E4E;
}

.pagelistbox .item.type3 .typebox {
  color: #EB5A02;
}

.pagelistbox .item .icon-zhishiku-kapianzaiti {
  position: absolute;
  color: #fff;
  font-size: 272px;
  left: 0;
  top: -68px;
  z-index: 0;
}

.pagelistbox .item .icon-zhishiku-ceshianniubeijing {
  position: absolute;
  color: #fff;
  font-size: 59px;
  right: 0;
  bottom: -16px;
  z-index: 0;
}

.pagelistbox .item .c-cardbtn-btns {
  text-align: left;
}

.namebox {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #eff4ff;
  box-sizing: border-box;
  padding: 6px 15px;
}

.namebox.type2 {
  background: #f4fbf3;
}

.namebox.type3 {
  background: #fffaf4;
}

.namebox .rbox {
  flex-shrink: 0;
}

.namebox .lbox {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  font-size: 16px;
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
  color: #949494;
  margin-top: 16px;
  font-size: 12px;
}

.botbox {
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: absolute;
  left: 15px;
  bottom: 10px;
  right: 15px;
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
